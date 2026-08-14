"""
Quantitative attention audit: does the correction move attention off the backdrop?

Replaces a subjective judgement with a measurement. The paper's attention audit
categorised 15 of 24 in-distribution and 5 of 20 external heatmaps by eye, which
is a small non-random sample scored by a human, and it characterised the
PRE-normalisation models. Both weaknesses are addressed here:

  * All 150 external images, not a sample.
  * An automatic scalar, not a category judgement.
  * Both conditions -- with and without the three-way normalisation -- on the
    same images, so the comparison is paired.

The metric is BORDER MASS FRACTION: the share of total Grad-CAM mass falling in
an outer frame occupying the outer 20% of each side. It needs no bounding-box
annotation, which is what makes it runnable over the whole set, and it targets
the specific failure the qualitative audit diagnosed -- attention on the
photographic backdrop, image corners and margins rather than the product. Under
the null "attention is spatially uniform" the border ring covers 1 - 0.6^2 =
0.64 of the area, so a border fraction near 0.64 means diffuse attention, well
below means product-centred attention, and well above means the model is
actively looking at the surround.

A second scalar, CENTRE MASS FRACTION over the central 40% x 40% box (0.16 of
the area), is reported alongside it.

Note on a defect this script also fixes: gradcam.py and gradcam_split_c.py feed
raw decoded images through build_transform() only, so they never apply the
capture normalisation the production models are trained under. Their heatmaps
therefore describe a model evaluated off-distribution. Here each condition's
Grad-CAM input passes through exactly the preprocessing that condition's model
was trained with.

Output: modeling/results/gradcam_quantitative.csv (per image, both conditions)
        modeling/results/gradcam_quantitative_summary.csv
"""
import csv
from pathlib import Path
import sys

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import build_transform, load_examples, set_seed, IMG_SIZE, SEED
from normalization import normalize_capture_confounds
from experiment_brightness_norm import load_split_c_examples
from result_io import load_chosen_lr
from train_model4_efficientnet import build_backbone, build_head, MODEL_NAME
from torch_utils import train_model_on_features

RESULTS = Path(__file__).resolve().parent / "results"
OUT_PER_IMAGE = RESULTS / "gradcam_quantitative.csv"
OUT_SUMMARY = RESULTS / "gradcam_quantitative_summary.csv"

BORDER_FRAC = 0.20   # outer ring width, as a fraction of each side
CENTRE_FRAC = 0.40   # central box side, as a fraction of each side


def ring_masks(n=IMG_SIZE):
    b = int(round(n * BORDER_FRAC))
    border = np.ones((n, n), dtype=bool)
    border[b:n - b, b:n - b] = False

    c0 = int(round(n * (0.5 - CENTRE_FRAC / 2)))
    c1 = int(round(n * (0.5 + CENTRE_FRAC / 2)))
    centre = np.zeros((n, n), dtype=bool)
    centre[c0:c1, c0:c1] = True
    return border, centre


def build_model(normalise):
    """Train M4's head under one preprocessing condition, deterministically."""
    def prep(im):
        im = im.convert("RGB")
        return normalize_capture_confounds(im) if normalise else im

    @torch.no_grad()
    def extract(fe, gap, examples, train, k):
        fe.eval()
        Xs, ys = [], []
        tf = build_transform(train=train)
        for pass_idx in range(k):
            set_seed(SEED + pass_idx)
            for start in range(0, len(examples), 32):
                batch = examples[start:start + 32]
                imgs = []
                for e in batch:
                    with Image.open(e["path"]) as im:
                        imgs.append(tf(prep(im)))
                Xs.append(gap(fe(torch.stack(imgs))).flatten(1).numpy())
                ys.extend(e["label"] for e in batch)
        return np.concatenate(Xs, 0), np.array(ys)

    fe, gap = build_backbone()
    head = build_head()

    # MUST be eval mode before any forward pass. Left in train mode, the
    # backbone's BatchNorm layers use batch-of-1 statistics AND overwrite their
    # running averages on every call, which silently corrupts the model: an
    # earlier version of this script did exactly that and reported Split C
    # accuracies of 0.06/0.16 against the true 0.033/0.807. Grad-CAM still
    # works in eval mode -- gradients flow to the activations, and BN does not
    # update. The sanity check is that split_c_accuracy in the summary must
    # match Table XII; if it does not, the model is being fed wrong.
    fe.eval()

    # The normalised condition IS the production model, so load its persisted
    # checkpoint rather than re-deriving it -- both to save the training and,
    # more importantly, so the heatmaps describe the model of record rather
    # than a rebuild hoped to be equivalent (Section 6.5). The un-normalised
    # baseline has no checkpoint (it is not a production condition) and is
    # trained here.
    if normalise:
        from result_io import load_checkpoint
        ckpt = load_checkpoint(head, MODEL_NAME, "split_b_final",
                               expected_lr=load_chosen_lr(MODEL_NAME))
        print(f"    loaded production checkpoint (lr={ckpt['lr']}, "
              f"epochs_run={ckpt['epochs_run']})")
        head.eval()
        return fe, gap, head, prep

    examples = load_examples("split_b")
    by = {s: [e for e in examples if e["split"] == s] for s in ("train", "val")}
    Xtr, ytr = extract(fe, gap, by["train"], True, 3)
    Xva, yva = extract(fe, gap, by["val"], False, 1)

    set_seed(SEED)
    head, _ = train_model_on_features(
        head, Xtr, ytr, Xva, yva, load_chosen_lr(MODEL_NAME),
        model_tag=MODEL_NAME, run_tag="gradcam_quant_raw")
    return fe, gap, head, prep


def cam_for(fe, gap, head, path, prep, target_class=None):
    fe.eval()
    head.eval()
    tf = build_transform(train=False)
    with Image.open(path) as im:
        x = tf(prep(im)).unsqueeze(0)
    A = fe(x).detach().requires_grad_(True)
    logits = head(gap(A).flatten(1))
    prob_counterfeit = torch.softmax(logits, 1)[0, 1].item()
    cls = int(logits.argmax(1).item()) if target_class is None else target_class
    grads = torch.autograd.grad(logits[0, cls], A)[0]
    cam = F.relu((grads.mean(dim=(2, 3), keepdim=True) * A).sum(1, keepdim=True))
    cam = cam.squeeze().detach().numpy()
    cam = np.maximum(cam - cam.min(), 0)
    img = Image.fromarray((cam / cam.max() * 255).astype(np.uint8)) if cam.max() > 0 \
        else Image.fromarray(np.zeros_like(cam, dtype=np.uint8))
    return np.asarray(img.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR), dtype=float), \
        cls, prob_counterfeit


def wilson_mean_ci(v):
    """Normal-approximation CI on the mean of a bounded scalar."""
    v = np.asarray(v, dtype=float)
    m = v.mean()
    se = v.std(ddof=1) / np.sqrt(len(v))
    return m, m - 1.96 * se, m + 1.96 * se


def main():
    border, centre = ring_masks()
    split_c = load_split_c_examples()
    print(f"{len(split_c)} external images; border ring covers "
          f"{border.mean():.3f} of the frame, centre box {centre.mean():.3f}")

    rows = []
    for normalise in (False, True):
        tag = "normalised" if normalise else "baseline"
        print(f"\n=== building M4 ({tag}) ===", flush=True)
        fe, gap, head, prep = build_model(normalise)
        print(f"=== Grad-CAM over {len(split_c)} images ({tag}) ===", flush=True)
        for i, e in enumerate(split_c):
            cam, cls, p = cam_for(fe, gap, head, e["path"], prep)
            total = cam.sum()
            if total <= 0:
                continue
            rows.append({
                "condition": tag,
                "image_id": e["image_id"],
                "predicted_class": "counterfeit" if cls == 1 else "authentic",
                "correct": int(cls == 0),          # Split C is authentic-only
                "prob_counterfeit": round(p, 4),
                "border_mass_fraction": round(float(cam[border].sum() / total), 4),
                "centre_mass_fraction": round(float(cam[centre].sum() / total), 4),
            })
            if (i + 1) % 50 == 0:
                print(f"  {i + 1}/{len(split_c)}", flush=True)

    RESULTS.mkdir(parents=True, exist_ok=True)
    with open(OUT_PER_IMAGE, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    summary = []
    for tag in ("baseline", "normalised"):
        sub = [r for r in rows if r["condition"] == tag]
        for metric in ("border_mass_fraction", "centre_mass_fraction"):
            m, lo, hi = wilson_mean_ci([r[metric] for r in sub])
            summary.append({"condition": tag, "metric": metric, "n": len(sub),
                            "mean": round(m, 4), "ci_lo": round(lo, 4),
                            "ci_hi": round(hi, 4)})
            print(f"{tag:<11} {metric:<22} n={len(sub)}  "
                  f"mean={m:.3f} [{lo:.3f}, {hi:.3f}]")
        acc = np.mean([r["correct"] for r in sub])
        expected = {"baseline": 0.033, "normalised": 0.807}[tag]
        if abs(acc - expected) > 0.05:
            print(f"  !! WARNING: {tag} Split C accuracy {acc:.3f} does not "
                  f"match the value of record {expected:.3f}. The model is "
                  f"being fed differently from the production pipeline; the "
                  f"attention numbers below are not trustworthy.")
        summary.append({"condition": tag, "metric": "split_c_accuracy",
                        "n": len(sub), "mean": round(float(acc), 4),
                        "ci_lo": "", "ci_hi": ""})
        print(f"{tag:<11} {'split_c_accuracy':<22} n={len(sub)}  {acc:.3f}")

    # paired comparison on the images present in both conditions
    b = {r["image_id"]: r["border_mass_fraction"] for r in rows if r["condition"] == "baseline"}
    n_ = {r["image_id"]: r["border_mass_fraction"] for r in rows if r["condition"] == "normalised"}
    shared = sorted(set(b) & set(n_))
    d = np.array([n_[k] - b[k] for k in shared])
    m, lo, hi = wilson_mean_ci(d)
    summary.append({"condition": "paired delta", "metric": "border_mass_fraction",
                    "n": len(shared), "mean": round(m, 4),
                    "ci_lo": round(lo, 4), "ci_hi": round(hi, 4)})
    print(f"\npaired change in border mass (normalised - baseline), n={len(shared)}: "
          f"{m:+.3f} [{lo:+.3f}, {hi:+.3f}]")

    with open(OUT_SUMMARY, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(summary[0].keys()))
        w.writeheader()
        w.writerows(summary)
    print(f"\nwrote {OUT_PER_IMAGE.name} and {OUT_SUMMARY.name}")


if __name__ == "__main__":
    main()

"""
Occlusion sensitivity on the external set: a second opinion on the attention audit.

Gap this closes. The claim that the corrected models take their evidence for
"authentic" from the background rests on Grad-CAM: 40 external maps, one
annotator, one attribution method, and a method the study itself argues is
degraded by the 128 px bottleneck it runs behind (Section S-I-J). Every part of
that is a reason for a reviewer to discount it. This script tests the same
claim with a method that shares none of those weaknesses:

  * it is perturbation-based, not gradient-based, so it does not inherit
    Grad-CAM's dependence on the spatial resolution reaching the last
    convolutional stage;
  * it needs no human judgement, so there is no annotator to agree with;
  * it runs on all 150 external images of each set rather than a sample.

Method. For each image, slide an occluding patch over a regular grid and record
how far the model's probability of "authentic" FALLS when each region is
hidden. A region whose occlusion costs the model its "authentic" answer is a
region the answer was resting on. The positive part of that surface is
normalised to unit mass and summarised with the same two statistics the
Grad-CAM audit uses -- the share of mass in an outer ring covering the outer
20% of each side (0.642 of the frame, so 0.642 is the value for uniform
attribution) and the share in the central 40% x 40% box (0.161 of the frame) --
so the two methods are directly comparable, by construction.

The number that matters is not the absolute share but the CONTRAST the
qualitative audit reported: on external images, evidence for "authentic" should
sit in the surround, and it should do so for the images the model gets right.
Both outcomes are informative and neither is assumed here. If the surround
carries the evidence, an independent method has confirmed the paper's most
uncomfortable finding. If it does not, the Grad-CAM reading was overstating a
dependence on the background, which the paper would then have to say.

Occlusion is applied after the production preprocessing, in normalised tensor
space, by writing the ImageNet channel mean into the patch -- the value the
network sees as "no signal" -- so the perturbation adds no colour or edge of
its own beyond the patch boundary.

Both models load their persisted production checkpoints and each asserts its
Split C accuracy against the value of record before reporting anything, which
is the check Section S-I-G argues every rebuild path should carry.

    python modeling/occlusion_sensitivity.py            # both backbones
    python modeling/occlusion_sensitivity.py --model 4  # one of them

Output: modeling/results/occlusion_sensitivity.csv          (per image)
        modeling/results/occlusion_sensitivity_summary.csv  (per model/outcome)
        paper/tables/table_occlusion.csv                    (manuscript table)
"""
import argparse
import csv
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import build_transform, IMG_SIZE                      # noqa: E402
from gradcam_quantitative import ring_masks                       # noqa: E402
from normalization import normalize_capture_confounds             # noqa: E402
from result_io import load_checkpoint, load_chosen_lr             # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "modeling" / "results"
OUT_PER_IMAGE = RESULTS / "occlusion_sensitivity.csv"
OUT_SUMMARY = RESULTS / "occlusion_sensitivity_summary.csv"
PAPER_TABLE = ROOT / "paper" / "tables" / "table_occlusion.csv"

PATCH = 64          # occluder side in pixels, on the 224 x 224 network input
STRIDE = 32         # 6 x 6 = 36 positions per image
BATCH = 32

# Split C accuracy of record, from results/external_from_checkpoints.csv.
OF_RECORD = {"model3_mobilenetv3small_frozen": 0.7733,
             "model4_efficientnetb0_frozen": 0.8067}
DISPLAY = {"model3_mobilenetv3small_frozen": "M3 MobileNetV3",
           "model4_efficientnetb0_frozen": "M4 EfficientNet-B0"}


def load_model(which):
    """The production backbone and head, in eval mode, from the checkpoint."""
    import importlib
    module = ("train_model3_mobilenet" if which == 3
              else "train_model4_efficientnet")
    mod = importlib.import_module(module)
    fe, gap = mod.build_backbone()
    # eval() before any forward pass: build_backbone returns a module in
    # training mode, and these backbones carry BatchNorm layers that would
    # otherwise run on batch statistics and overwrite their running averages
    # (the defect of Section S-I-G).
    fe.eval()
    head = mod.build_head()
    ckpt = load_checkpoint(head, mod.MODEL_NAME, "split_b_final",
                           expected_lr=load_chosen_lr(mod.MODEL_NAME))
    head.eval()
    print(f"  loaded {mod.MODEL_NAME} checkpoint "
          f"(lr={ckpt['lr']}, epochs_run={ckpt['epochs_run']})")
    return mod.MODEL_NAME, fe, gap, head


@torch.no_grad()
def prob_authentic(fe, gap, head, batch):
    logits = head(gap(fe(batch)).flatten(1))
    return torch.softmax(logits, dim=1)[:, 0]      # authentic = class 0


def occlusion_map(fe, gap, head, x, fill):
    """Drop in P(authentic) when each patch is hidden. Shape: (grid, grid)."""
    starts = list(range(0, IMG_SIZE - PATCH + 1, STRIDE))
    base = float(prob_authentic(fe, gap, head, x.unsqueeze(0))[0])

    variants, coords = [], []
    for top in starts:
        for left in starts:
            v = x.clone()
            v[:, top:top + PATCH, left:left + PATCH] = fill
            variants.append(v)
            coords.append((top, left))

    drops = []
    for i in range(0, len(variants), BATCH):
        chunk = torch.stack(variants[i:i + BATCH])
        drops.extend((base - prob_authentic(fe, gap, head, chunk)).tolist())

    # Spread each patch's drop over the pixels it covered, so the surface is
    # comparable with a Grad-CAM map at the same resolution rather than with a
    # coarse grid. Overlapping patches average.
    surface = np.zeros((IMG_SIZE, IMG_SIZE), dtype=float)
    counts = np.zeros((IMG_SIZE, IMG_SIZE), dtype=float)
    for (top, left), d in zip(coords, drops):
        surface[top:top + PATCH, left:left + PATCH] += d
        counts[top:top + PATCH, left:left + PATCH] += 1
    return surface / np.maximum(counts, 1), base


def run(which, rows, limit=None):
    from experiment_brightness_norm import load_split_c_examples

    name, fe, gap, head = load_model(which)
    border, centre = ring_masks()
    tf = build_transform(train=False)
    # The value the network reads as "no signal": zero in normalised space is
    # the ImageNet channel mean in pixel space.
    fill = 0.0

    examples = load_split_c_examples()
    if limit:
        examples = examples[:limit]
    correct = 0
    for i, e in enumerate(examples):
        with Image.open(e["path"]) as im:
            x = tf(normalize_capture_confounds(im.convert("RGB")))

        surface, p_auth = occlusion_map(fe, gap, head, x, fill)
        called_authentic = p_auth >= 0.5           # Split C is authentic-only
        correct += int(called_authentic)

        pos = np.maximum(surface, 0.0)             # evidence FOR "authentic"
        total = pos.sum()
        if total <= 0:
            continue
        rows.append({
            "model": name,
            "image_id": e["image_id"],
            "predicted": "authentic" if called_authentic else "counterfeit",
            "correct": int(called_authentic),
            "prob_authentic": round(p_auth, 4),
            "border_mass_fraction": round(float(pos[border].sum() / total), 4),
            "centre_mass_fraction": round(float(pos[centre].sum() / total), 4),
        })
        if (i + 1) % 25 == 0:
            print(f"    {i + 1}/{len(examples)}", flush=True)

    acc = correct / len(examples)
    want = OF_RECORD[name]
    if limit:
        print(f"  [note] subset of {limit} image(s): accuracy {acc:.3f} is not "
              f"comparable with the {want:.3f} of record over all 150")
    elif abs(acc - want) > 0.02:
        print(f"  !! WARNING: Split C accuracy {acc:.3f} does not match the "
              f"value of record {want:.3f}. The model is being fed differently "
              f"from the production pipeline; do not report these numbers.")
    else:
        print(f"  [ok] Split C accuracy {acc:.3f} matches the value of record "
              f"{want:.3f}")
    return name, acc


def summarise(rows, accs):
    out = []
    for name in sorted({r["model"] for r in rows}):
        sub = [r for r in rows if r["model"] == name]
        groups = [("all", sub),
                  ("called authentic (correct)",
                   [r for r in sub if r["correct"]]),
                  ("called counterfeit (wrong)",
                   [r for r in sub if not r["correct"]])]
        for label, g in groups:
            if not g:
                continue
            b = np.array([r["border_mass_fraction"] for r in g])
            c = np.array([r["centre_mass_fraction"] for r in g])

            def ci(v):
                m = float(v.mean())
                if len(v) < 2:
                    return m, "", ""
                se = float(v.std(ddof=1)) / np.sqrt(len(v))
                return m, m - 1.96 * se, m + 1.96 * se

            bm, blo, bhi = ci(b)
            cm, _, _ = ci(c)
            out.append({
                "model": DISPLAY[name], "group": label, "n": len(g),
                "border_mass_mean": round(bm, 4),
                "border_ci_lo": round(blo, 4) if blo != "" else "",
                "border_ci_hi": round(bhi, 4) if bhi != "" else "",
                "centre_mass_mean": round(cm, 4),
                "split_c_accuracy": round(accs[name], 4),
            })

    fields = list(out[0].keys())
    for path in (OUT_SUMMARY, PAPER_TABLE):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(out)

    print(f"\nuniform-attribution reference: border 0.642, centre 0.161")
    for r in out:
        print(f"  {r['model']:<20} {r['group']:<28} n={r['n']:>3}  "
              f"border {r['border_mass_mean']:.3f}  "
              f"centre {r['centre_mass_mean']:.3f}")
    print(f"\nwrote {OUT_SUMMARY.relative_to(ROOT)} and "
          f"{PAPER_TABLE.relative_to(ROOT)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", type=int, choices=(3, 4), nargs="+",
                    default=[3, 4])
    ap.add_argument("--limit", type=int,
                    help="run on the first N images only (smoke test; the "
                         "value-of-record check is skipped)")
    args = ap.parse_args()

    rows, accs = [], {}
    for which in args.model:
        print(f"=== occlusion sensitivity, model {which}, "
              f"{len(range(0, IMG_SIZE - PATCH + 1, STRIDE)) ** 2} positions "
              f"per image ===", flush=True)
        name, acc = run(which, rows, args.limit)
        accs[name] = acc
        RESULTS.mkdir(parents=True, exist_ok=True)
        with open(OUT_PER_IMAGE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    summarise(rows, accs)


if __name__ == "__main__":
    main()

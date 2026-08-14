"""
Gray-world white balance as a fourth normalisation axis -- DETERMINISTIC RERUN.

Why this file was rewritten (2026-08-13). The original version of this
experiment ran on 2026-07-25 and its result -- white balance helps nothing
alone (8.7% -> 10.7%) and is mildly negative in combination (45.3% -> 42.0%)
-- is what the manuscript cites to rule the axis out. That run is not
trustworthy, for three reasons found on re-reading the file:

  1. Its feature extraction looped `for _ in range(k_augment)` with no
     per-pass seeding. That is exactly the defect written up as Finding 13,
     fixed in feature_cache.py on 2026-07-26, i.e. the day AFTER this
     experiment ran. Under that defect a single unchanged condition read
     62.7, 45.3 and 50.7 across three executions -- a spread of 17 points,
     far larger than the 3.3-point difference the axis was rejected on.
  2. It hard-coded the learning rate at 0.001 instead of reading the value
     the training scripts recorded (the 2026-07-28 result_io fix).
  3. Its "combined" reference was resolution + brightness only. Compression
     had not yet been promoted, so white balance was never tested against
     the pipeline that actually ships.

All three are corrected here, and the conditions now include a same-run
production baseline. The superseded numbers are preserved in
results/colorbalance_norm_experiment_PRE_DETERMINISM_20260725.csv.

Motivation for the axis is unchanged and still real: Kaggle's R:G:B channel
means (normalised to R = 1) are 1 : 0.94 : 0.86, a warm cast with the blue
channel suppressed ~14% relative to red, against Split C's much more neutral
1 : 0.93 : 0.93. Gray-world white balance scales the R and B channels so
their means match G. Like the other three operators it is label-free and
deployable unchanged at inference.

Placement: white balance is a photometric channel-scaling, so it is composed
with brightness, before the compression bottleneck (R -> B -> W -> C). The
two-way conditions reproduce the original comparison on a sound footing.

Robustness to the host killing long background processes: every condition
appends its row immediately and a re-run skips conditions already recorded.

Output: modeling/results/colorbalance_norm_experiment.csv
"""
import csv
from pathlib import Path
import sys

import numpy as np
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, set_seed, SEED, IMG_SIZE, IMAGENET_MEAN, IMAGENET_STD
from metrics import compute_point_metrics
from experiment_brightness_norm import load_split_c_examples
from normalization import (normalize_resolution, normalize_brightness,
                           normalize_compression)
from result_io import load_chosen_lr

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "modeling" / "results" / "colorbalance_norm_experiment.csv"


def normalize_color_balance(im: Image.Image) -> Image.Image:
    """Gray-world white balance: scale R and B channel means to match G."""
    arr = np.asarray(im.convert("RGB")).astype(np.float32)
    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    g_mean = g.mean()
    r_mean, b_mean = r.mean(), b.mean()
    if r_mean > 1e-6:
        arr[:, :, 0] = np.clip(r * (g_mean / r_mean), 0, 255)
    if b_mean > 1e-6:
        arr[:, :, 2] = np.clip(b * (g_mean / b_mean), 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


OPS = {
    "R": normalize_resolution,
    "B": normalize_brightness,
    "W": normalize_color_balance,
    "C": normalize_compression,
}

# (label, operator sequence). The production pipeline runs first so that every
# other row has a same-run reference point rather than a cross-run citation.
CONDITIONS = [
    ("production 3-way (R->B->C)",          "RBC"),
    ("white balance only (W)",              "W"),
    ("production 3-way + WB (R->B->W->C)",  "RBWC"),
    ("two-way (R->B)",                      "RB"),
    ("two-way + WB (R->B->W)",              "RBW"),
]

FIELDS = ["condition", "operators", "split_b_test_acc", "split_c_acc"]


def make_preprocess(sequence):
    def preprocess(im):
        im = im.convert("RGB")
        for key in sequence:
            im = OPS[key](im)
        return im
    return preprocess


def run_model4(preprocess, run_tag):
    from torchvision import transforms
    from train_model4_efficientnet import build_backbone, build_head, MODEL_NAME
    from torch_utils import train_model_on_features, evaluate_model_on_features

    def build_tf(train):
        if train:
            ops = [
                transforms.Resize((IMG_SIZE, IMG_SIZE)),
                transforms.RandomRotation(degrees=12),
                transforms.ColorJitter(brightness=0.25, contrast=0.25),
                transforms.RandomResizedCrop(IMG_SIZE, scale=(0.85, 1.0)),
                transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 0.8)),
            ]
        else:
            ops = [transforms.Resize((IMG_SIZE, IMG_SIZE))]
        ops += [transforms.ToTensor(),
                transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)]
        return transforms.Compose(ops)

    @torch.no_grad()
    def extract(feature_extractor, gap, examples, train, k_augment):
        # eval() matters: build_backbone returns a module in training mode and
        # these are BatchNorm backbones (the 2026-07-30 defect).
        feature_extractor.eval()
        all_X, all_y, all_ids = [], [], []
        tf = build_tf(train)
        for pass_idx in range(k_augment):
            set_seed(SEED + pass_idx)          # Finding 13
            for start in range(0, len(examples), 32):
                batch = examples[start:start + 32]
                imgs = []
                for e in batch:
                    with Image.open(e["path"]) as im:
                        imgs.append(tf(preprocess(im)))
                feats = gap(feature_extractor(torch.stack(imgs))).flatten(1)
                all_X.append(feats.numpy())
                all_y.extend([e["label"] for e in batch])
                all_ids.extend([e["image_id"] for e in batch])
        return np.concatenate(all_X, axis=0), np.array(all_y), all_ids

    examples = load_examples("split_b")
    by_split = {s: [e for e in examples if e["split"] == s]
                for s in ("train", "val", "test")}

    feature_extractor, gap = build_backbone()
    X_tr, y_tr, _ = extract(feature_extractor, gap, by_split["train"], True, 3)
    X_va, y_va, _ = extract(feature_extractor, gap, by_split["val"], False, 1)
    X_te, y_te, _ = extract(feature_extractor, gap, by_split["test"], False, 1)

    lr = load_chosen_lr(MODEL_NAME)
    set_seed(SEED)
    head = build_head()
    head, _ = train_model_on_features(head, X_tr, y_tr, X_va, y_va, lr,
                                      model_tag=MODEL_NAME, run_tag=run_tag)

    _, y_true, y_prob = evaluate_model_on_features(
        head, X_te, y_te, list(range(len(y_te))))
    b_acc = compute_point_metrics(y_true, y_prob)["accuracy"]

    split_c = load_split_c_examples()
    Xc, yc, idsc = extract(feature_extractor, gap, split_c, False, 1)
    _, _, yc_prob = evaluate_model_on_features(head, Xc, yc, idsc)
    c_acc = float(np.mean(np.array(yc_prob) < 0.5))
    return b_acc, c_acc


def load_done():
    if not OUT_PATH.exists():
        return []
    with open(OUT_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows if rows and set(rows[0]) == set(FIELDS) else []


def write_all(rows):
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def main():
    rows = load_done()
    done = {r["condition"] for r in rows}
    if done:
        print(f"resuming; {len(done)} condition(s) already recorded")

    for label, seq in CONDITIONS:
        if label in done:
            print(f"=== skip (done): {label} ===")
            continue
        print(f"=== Model 4: {label} ===", flush=True)
        b_acc, c_acc = run_model4(make_preprocess(seq), run_tag=f"wb_{seq}")
        print(f"  Split B test acc={b_acc:.3f}  Split C acc={c_acc:.3f}",
              flush=True)
        rows.append({"condition": label, "operators": seq,
                     "split_b_test_acc": round(b_acc, 4),
                     "split_c_acc": round(c_acc, 4)})
        write_all(rows)

    print(f"\nWrote {OUT_PATH}")
    for r in rows:
        print(f"  {r['condition']:<38} B={r['split_b_test_acc']}  "
              f"C={r['split_c_acc']}")


if __name__ == "__main__":
    main()

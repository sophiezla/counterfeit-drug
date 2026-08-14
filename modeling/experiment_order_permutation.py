"""
Does the ORDER of the three normalisation operators matter?

Gap this closes: Section V-D states that the three label-free operators are
"composed in a fixed order" -- resolution, then brightness, then compression
(Eq. 8) -- and normalization.py hard-codes that order. Nothing in the study
ever varied it. experiment_constant_sensitivity.py varies the three
*magnitudes* (128, 0.5, 40) but not the sequence, so a reviewer can fairly
ask whether the reported recovery depends on an unexamined choice.

The question is not cosmetic. Two of the three operators impose an
information bottleneck and they do not commute:

  * resolution then compression -- JPEG quantises a 128 px image, so the
    8x8 blocks cover a large fraction of the frame;
  * compression then resolution -- JPEG quantises at native size and the
    downsample then averages the artefacts away, which is much closer to no
    compression at all for a high-resolution external photograph.

Brightness is a location shift and commutes with neither exactly: applied
after compression it rescales quantisation artefacts, applied before it
changes what the quantiser sees. Clipping in normalize_brightness makes it
formally non-commutative even with itself under different inputs.

Method: all 3! = 6 orderings of the production operators, at their production
constants, on Model 4 (EfficientNet-B0), inside a single script execution so
every row is directly comparable. The production order runs first, giving a
same-run reference point rather than a citation to an older run. The learning
rate is read from results/chosen_lrs.json (see result_io), never hard-coded.

Robustness to the host killing long background processes: every condition
appends its row to the output CSV immediately and a re-run skips any
condition already present.

Output: modeling/results/order_permutation_experiment.csv
"""
import csv
import itertools
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
OUT_PATH = ROOT / "modeling" / "results" / "order_permutation_experiment.csv"

# The production operators themselves, imported rather than reimplemented so
# this experiment cannot drift from the pipeline it is testing.
OPS = {
    "R": ("resolution", normalize_resolution),
    "B": ("brightness", normalize_brightness),
    "C": ("compression", normalize_compression),
}
PRODUCTION_ORDER = ("R", "B", "C")          # Eq. (8)

FIELDS = ["order", "order_long", "is_production",
          "split_b_test_acc", "split_c_acc"]


def make_preprocess(order):
    def preprocess(im):
        im = im.convert("RGB")
        for key in order:
            im = OPS[key][1](im)
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
            # Per-pass seeding, as in feature_cache.extract_features
            # (Finding 13). Without it the augmented passes depend on prior
            # RNG state and the run is not reproducible.
            set_seed(SEED + pass_idx)
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


def conditions():
    """Production order first, so every later row has a same-run reference."""
    others = [p for p in itertools.permutations("RBC")
              if tuple(p) != PRODUCTION_ORDER]
    return [PRODUCTION_ORDER] + [tuple(p) for p in others]


def load_done():
    if not OUT_PATH.exists():
        return []
    with open(OUT_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_all(rows):
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def main():
    rows = load_done()
    done = {r["order"] for r in rows}
    if done:
        print(f"resuming; {len(done)} condition(s) already recorded")

    for order in conditions():
        key = "".join(order)
        if key in done:
            print(f"=== skip (done): {key} ===")
            continue
        long = " -> ".join(OPS[k][0] for k in order)
        is_prod = tuple(order) == PRODUCTION_ORDER
        print(f"=== Model 4: {key} ({long})"
              f"{'  [production]' if is_prod else ''} ===", flush=True)
        b_acc, c_acc = run_model4(make_preprocess(order),
                                  run_tag=f"order_{key}")
        print(f"  Split B test acc={b_acc:.3f}  Split C acc={c_acc:.3f}",
              flush=True)
        rows.append({"order": key, "order_long": long,
                     "is_production": is_prod,
                     "split_b_test_acc": round(b_acc, 4),
                     "split_c_acc": round(c_acc, 4)})
        write_all(rows)

    print(f"\nWrote {OUT_PATH}")
    for r in rows:
        print(f"  {r['order']:<5} {r['order_long']:<44} "
              f"B={r['split_b_test_acc']}  C={r['split_c_acc']}")


if __name__ == "__main__":
    main()

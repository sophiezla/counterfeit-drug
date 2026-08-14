"""
Sensitivity of the 3-way normalisation to its three constants.

Gap this closes: normalization.py fixes RESOLUTION_BOTTLENECK=128,
BRIGHTNESS_TARGET=0.5 and JPEG_QUALITY=40. Only the first has a stated
justification from the training distribution alone (128px sits below the
Kaggle pool's own 10th-percentile short side). The other two were picked
by hand and never varied, so a reviewer can fairly ask whether the reported
Split C recovery is an artefact of three lucky constants.

Method: from the production triple (128, 0.5, 40), vary one constant at a
time, on Model 4 (EfficientNet-B0), all conditions inside a single script
execution so the within-run comparison is valid. The learning rate is read
from results/chosen_lrs.json rather than hard-coded (see result_io).

Robustness to the host killing long background processes: every condition
appends its row to the output CSV immediately, and a re-run skips any
condition already present. Killing this script therefore costs one
condition, not the whole sweep.

Output: modeling/results/constant_sensitivity_experiment.csv
"""
import csv
import io
from pathlib import Path
import sys

import numpy as np
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, set_seed, SEED, IMG_SIZE, IMAGENET_MEAN, IMAGENET_STD
from metrics import compute_point_metrics
from experiment_brightness_norm import load_split_c_examples
from result_io import load_chosen_lr

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "modeling" / "results" / "constant_sensitivity_experiment.csv"

PRODUCTION = (128, 0.5, 40)

# (label, short_side, brightness_target, jpeg_quality). The production triple
# runs first so that every other row has a same-run reference point.
CONDITIONS = [
    ("production (128, 0.5, 40)", 128, 0.5, 40),
    ("resolution 96",             96,  0.5, 40),
    ("resolution 192",            192, 0.5, 40),
    ("resolution 256",            256, 0.5, 40),
    ("brightness target 0.4",     128, 0.4, 40),
    ("brightness target 0.6",     128, 0.6, 40),
    ("JPEG quality 25",           128, 0.5, 25),
    ("JPEG quality 60",           128, 0.5, 60),
    ("JPEG quality 85",           128, 0.5, 85),
]

FIELDS = ["condition", "short_side", "brightness_target", "jpeg_quality",
          "split_b_test_acc", "split_c_acc"]


def make_preprocess(short_side, brightness_target, jpeg_quality):
    """The Eq. (8) operator with its three constants supplied explicitly."""

    def preprocess(im):
        im = im.convert("RGB")
        # resolution bottleneck
        w, h = im.size
        if min(w, h) > short_side:
            scale = short_side / min(w, h)
            im = im.resize((max(1, round(w * scale)), max(1, round(h * scale))),
                           Image.BILINEAR)
        # brightness rescale
        arr = np.asarray(im).astype(np.float32) / 255.0
        mean = arr.mean()
        if mean > 1e-6:
            arr = arr * (brightness_target / mean)
        im = Image.fromarray((np.clip(arr, 0.0, 1.0) * 255).astype(np.uint8))
        # compression bottleneck
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=jpeg_quality)
        buf.seek(0)
        return Image.open(buf).convert("RGB")

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
        feature_extractor.eval()
        all_X, all_y, all_ids = [], [], []
        tf = build_tf(train)
        for pass_idx in range(k_augment):
            # Same per-pass seeding as feature_cache.extract_features (Finding
            # 13): without it, augmented passes depend on prior RNG state.
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


def load_done():
    if not OUT_PATH.exists():
        return []
    with open(OUT_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_all(rows):
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def main():
    rows = load_done()
    done = {r["condition"] for r in rows}
    if done:
        print(f"resuming; {len(done)} condition(s) already recorded")

    for label, s, mu, q in CONDITIONS:
        if label in done:
            print(f"=== skip (done): {label} ===")
            continue
        print(f"=== Model 4: {label} ===", flush=True)
        b_acc, c_acc = run_model4(make_preprocess(s, mu, q),
                                  run_tag=f"constsens_{s}_{mu}_{q}")
        print(f"  Split B test acc={b_acc:.3f}  Split C acc={c_acc:.3f}",
              flush=True)
        rows.append({"condition": label, "short_side": s,
                     "brightness_target": mu, "jpeg_quality": q,
                     "split_b_test_acc": round(b_acc, 4),
                     "split_c_acc": round(c_acc, 4)})
        write_all(rows)

    print(f"\nWrote {OUT_PATH}")
    for r in rows:
        print(f"  {r['condition']:<28} B={r['split_b_test_acc']}  "
              f"C={r['split_c_acc']}")


if __name__ == "__main__":
    main()

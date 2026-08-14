"""
Follow-up to experiment_brightness_norm.py, testing the other major
untested axis identified in the capture-method confound
(data/metadata/capture_method_confound_findings.md): resolution/detail.
Kaggle images are ~10x lower resolution than Split C's; brightness
normalization alone recovered only ~5x on Split C (6.7% -> 31.3% for
EfficientNet-B0), leaving most of the ~93%-in-distribution vs ~31%
gap unexplained. If detail budget is a second major shortcut, capping
every image (both sources, both classes) through the same low-resolution
bottleneck before the network ever sees it should recover more.

Method: every image is first downsampled to a small fixed size (128px on
the short side, chosen to sit below Kaggle's own 10th-percentile image
size so it's a genuine bottleneck for nearly all images in both sources,
not just the external ones) using standard bilinear resizing, THEN resized
back up to the network's normal 224x224 input size. This equalizes
"effective detail budget" the same way brightness normalization equalized
mean pixel value -- no label information is used, and it's a real,
deployable preprocessing step.

Tests three conditions for Model 4 (EfficientNet-B0, the model with usable
signal beyond pure confounds per the brightness experiment):
  - resolution normalization alone
  - brightness normalization alone (repeated here for a clean 3-way table)
  - both combined

Output: modeling/results/resolution_norm_experiment.csv
"""
import csv
from pathlib import Path
import sys

import numpy as np
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, set_seed, SEED, IMG_SIZE, RAW, IMAGENET_MEAN, IMAGENET_STD
from metrics import compute_point_metrics
from experiment_brightness_norm import normalize_brightness, load_split_c_examples

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "modeling" / "results" / "resolution_norm_experiment.csv"

RESOLUTION_BOTTLENECK = 128  # short-side px; below Kaggle's own 10th percentile (~287px)


def normalize_resolution(im: Image.Image) -> Image.Image:
    w, h = im.size
    if min(w, h) <= RESOLUTION_BOTTLENECK:
        return im  # already at or below the bottleneck, nothing to remove
    scale = RESOLUTION_BOTTLENECK / min(w, h)
    small = im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.BILINEAR)
    return small  # caller resizes back up to IMG_SIZE as part of the normal pipeline


def run_model4(norm_resolution: bool, norm_brightness: bool, run_tag: str):
    import torch.nn as nn
    from torchvision import transforms
    from train_model4_efficientnet import build_backbone, build_head, MODEL_NAME
    from torch_utils import train_model_on_features, evaluate_model_on_features

    def build_tf(train: bool):
        ops = []
        if train:
            ops += [
                transforms.Resize((IMG_SIZE, IMG_SIZE)),
                transforms.RandomRotation(degrees=12),
                transforms.ColorJitter(brightness=0.25, contrast=0.25),
                transforms.RandomResizedCrop(IMG_SIZE, scale=(0.85, 1.0)),
                transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 0.8)),
            ]
        else:
            ops += [transforms.Resize((IMG_SIZE, IMG_SIZE))]
        ops += [transforms.ToTensor(), transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)]
        return transforms.Compose(ops)

    def preprocess(im):
        im = im.convert("RGB")
        if norm_resolution:
            im = normalize_resolution(im)
        if norm_brightness:
            im = normalize_brightness(im)
        return im

    @torch.no_grad()
    def extract(feature_extractor, gap, examples, train: bool, k_augment: int):
        feature_extractor.eval()
        all_X, all_y, all_ids = [], [], []
        tf = build_tf(train)
        for _ in range(k_augment):
            for batch_start in range(0, len(examples), 32):
                batch = examples[batch_start:batch_start + 32]
                imgs = []
                for e in batch:
                    with Image.open(e["path"]) as im:
                        imgs.append(tf(preprocess(im)))
                x = torch.stack(imgs)
                feats = feature_extractor(x)
                feats = gap(feats).flatten(1)
                all_X.append(feats.numpy())
                all_y.extend([e["label"] for e in batch])
                all_ids.extend([e["image_id"] for e in batch])
        return np.concatenate(all_X, axis=0), np.array(all_y), all_ids

    examples = load_examples("split_b")
    by_split = {s: [e for e in examples if e["split"] == s] for s in ("train", "val", "test")}

    feature_extractor, gap = build_backbone()
    X_train, y_train, _ = extract(feature_extractor, gap, by_split["train"], train=True, k_augment=3)
    X_val, y_val, _ = extract(feature_extractor, gap, by_split["val"], train=False, k_augment=1)
    X_test, y_test, _ = extract(feature_extractor, gap, by_split["test"], train=False, k_augment=1)

    set_seed(SEED)
    head = build_head()
    head, _ = train_model_on_features(head, X_train, y_train, X_val, y_val, 0.001,
                                       model_tag=MODEL_NAME, run_tag=run_tag)

    _, y_true, y_prob = evaluate_model_on_features(head, X_test, y_test, list(range(len(y_test))))
    test_metrics = compute_point_metrics(y_true, y_prob)

    split_c = load_split_c_examples()
    Xc, yc, idsc = extract(feature_extractor, gap, split_c, train=False, k_augment=1)
    _, yc_true, yc_prob = evaluate_model_on_features(head, Xc, yc, idsc)
    c_acc = float(np.mean(np.array(yc_prob) < 0.5))

    return test_metrics["accuracy"], c_acc


def main():
    conditions = [
        ("baseline_no_norm", False, False),
        ("resolution_norm_only", True, False),
        ("brightness_norm_only", False, True),
        ("both_combined", True, True),
    ]
    results = []
    for name, res_norm, bright_norm in conditions:
        print(f"=== Model 4 (EfficientNet-B0): {name} ===")
        acc, c_acc = run_model4(res_norm, bright_norm, run_tag=f"resnorm_exp_{name}")
        print(f"  Split B test acc={acc:.3f}  Split C acc={c_acc:.3f}")
        results.append({"condition": name, "resolution_normalized": res_norm,
                         "brightness_normalized": bright_norm,
                         "split_b_test_acc": acc, "split_c_acc": c_acc})

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()

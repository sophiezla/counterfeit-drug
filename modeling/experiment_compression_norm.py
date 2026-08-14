"""
Follow-up to experiment_colorbalance_norm.py, testing the next untested axis
from data/metadata/capture_method_confound_findings.md's candidate list:
JPEG compression/quality artifacts.

Motivation: Kaggle's two classes don't just differ in resolution and
brightness (Findings 1, 4-5) -- their mean file sizes differ by ~56x
(6,022 vs 339,188 bytes, Finding 1), which is a compression-artifact
signature as much as a resolution one. A CNN has direct access to
compression-artifact statistics (blockiness, ringing, noise floor) the same
way it has direct access to resolution-dependent blur. Color balance
(Finding 9) turned out not to matter; compression is the next most obvious
untested candidate before concluding the remaining gap is irreducible.

Method: re-encode every image through a fixed, low JPEG quality bottleneck
(quality=40) and decode it back, label-free, applied identically to
train/test/Split C -- the same "impose a common bottleneck" logic as
resolution normalization (experiment_resolution_norm.py), just on the
compression axis instead of the pixel-count axis.

Tests, for Model 4 (EfficientNet-B0):
  - compression normalization alone
  - compression + resolution + brightness, all combined (the fullest
    condition tested so far)

Output: modeling/results/compression_norm_experiment.csv
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
from experiment_brightness_norm import normalize_brightness, load_split_c_examples
from experiment_resolution_norm import normalize_resolution

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "modeling" / "results" / "compression_norm_experiment.csv"

JPEG_QUALITY = 40  # aggressive; below Kaggle's own images*.jpg typical quality


def normalize_compression(im: Image.Image) -> Image.Image:
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="JPEG", quality=JPEG_QUALITY)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def run_model4(norm_resolution: bool, norm_brightness: bool, norm_compression: bool, run_tag: str):
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
        if norm_compression:
            im = normalize_compression(im)
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
        ("baseline_no_norm_rerun", False, False, False),
        ("compression_norm_only", False, False, True),
        ("resolution_brightness_combined_rerun", True, True, False),
        ("all_three_combined", True, True, True),
    ]
    results = []
    for name, res_norm, bright_norm, comp_norm in conditions:
        print(f"=== Model 4 (EfficientNet-B0): {name} ===")
        acc, c_acc = run_model4(res_norm, bright_norm, comp_norm, run_tag=f"compnorm_exp_{name}")
        print(f"  Split B test acc={acc:.3f}  Split C acc={c_acc:.3f}")
        results.append({"condition": name, "resolution_normalized": res_norm,
                         "brightness_normalized": bright_norm,
                         "compression_normalized": comp_norm,
                         "split_b_test_acc": acc, "split_c_acc": c_acc})
        with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
            w.writeheader()
            w.writerows(results)

    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()

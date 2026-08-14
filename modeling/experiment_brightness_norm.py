"""
Follow-up experiment testing the capture-method confound finding
(data/metadata/capture_method_confound_findings.md) directly: if Split C's
external-generalization collapse is driven by the brightness gap between
Kaggle's two classes (mean 0.77 authentic vs 0.56 counterfeit) and Split C's
own very dark images (mean 0.16), then normalizing brightness identically
across train, Kaggle test, AND Split C before feeding any model should
close at least part of the gap -- if it doesn't, brightness alone isn't
the (or the whole) mechanism, which is itself an informative result.

Method: every image (Kaggle train/val/test, Split C) is rescaled so its
mean pixel value matches a fixed target (0.5) before any other
processing, applied identically regardless of split or class -- the same
normalization a deployed system could actually apply, not something that
uses label information.

Tests Model 1 (classical, most directly tied to the exact confound found
via raw color-histogram features) and Model 4 (best in-distribution
performer, largest Split C gap) with and without this normalization.

Output: modeling/results/brightness_norm_experiment.csv
"""
import csv
from pathlib import Path
import sys

import numpy as np
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, set_seed, SEED, IMG_SIZE, RAW
from metrics import compute_point_metrics

ROOT = Path(__file__).resolve().parent.parent
CANDIDATE_PROV = ROOT / "data" / "metadata" / "split_c_candidate_provenance.csv"
OUT_PATH = ROOT / "modeling" / "results" / "brightness_norm_experiment.csv"

TARGET_BRIGHTNESS = 0.5


def normalize_brightness(im: Image.Image) -> Image.Image:
    """Rescale pixel values so the image's mean brightness matches
    TARGET_BRIGHTNESS. Uses no label information -- a real deployed system
    could apply this identically to any input image."""
    arr = np.asarray(im.convert("RGB")).astype(np.float32) / 255.0
    current = arr.mean()
    if current < 1e-6:
        return im
    scale = TARGET_BRIGHTNESS / current
    arr = np.clip(arr * scale, 0.0, 1.0)
    return Image.fromarray((arr * 255).astype(np.uint8))


def load_split_c_examples():
    with open(CANDIDATE_PROV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [{"image_id": r["image_id"], "path": RAW / r["orig_relpath"], "label": 0} for r in rows]


# ---------- Model 1 (classical): color histogram + LogReg ----------

def extract_histogram(path, normalize: bool):
    with Image.open(path) as im:
        im = im.convert("RGB").resize((IMG_SIZE, IMG_SIZE))
        if normalize:
            im = normalize_brightness(im)
        arr = np.asarray(im)
    feats = []
    for c in range(3):
        hist, _ = np.histogram(arr[:, :, c], bins=32, range=(0, 256), density=True)
        feats.append(hist)
    return np.concatenate(feats)


def run_model1(normalize: bool):
    from sklearn.linear_model import LogisticRegression

    examples = load_examples("split_b")
    by_split = {s: [e for e in examples if e["split"] == s] for s in ("train", "val", "test")}

    X_train = np.stack([extract_histogram(e["path"], normalize) for e in by_split["train"]])
    y_train = np.array([e["label"] for e in by_split["train"]])

    set_seed(SEED)
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED)
    clf.fit(X_train, y_train)

    X_test = np.stack([extract_histogram(e["path"], normalize) for e in by_split["test"]])
    y_test = np.array([e["label"] for e in by_split["test"]])
    test_prob = clf.predict_proba(X_test)[:, 1]
    test_metrics = compute_point_metrics(y_test, test_prob)

    split_c = load_split_c_examples()
    X_c = np.stack([extract_histogram(e["path"], normalize) for e in split_c])
    c_prob = clf.predict_proba(X_c)[:, 1]
    c_acc = float((c_prob < 0.5).mean())

    return test_metrics["accuracy"], c_acc


# ---------- Model 4 (EfficientNet-B0 frozen): cached features + head ----------

def run_model4(normalize: bool):
    import torch.nn as nn
    from torchvision import transforms
    from common import IMAGENET_MEAN, IMAGENET_STD
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
                        im = im.convert("RGB")
                        if normalize:
                            im = normalize_brightness(im)
                        imgs.append(tf(im))
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
                                       model_tag=MODEL_NAME, run_tag=f"brightness_exp_norm{normalize}")

    _, y_true, y_prob = evaluate_model_on_features(head, X_test, y_test, list(range(len(y_test))))
    test_metrics = compute_point_metrics(y_true, y_prob)

    split_c = load_split_c_examples()
    Xc, yc, idsc = extract(feature_extractor, gap, split_c, train=False, k_augment=1)
    _, yc_true, yc_prob = evaluate_model_on_features(head, Xc, yc, idsc)
    c_acc = float(np.mean(np.array(yc_prob) < 0.5))

    return test_metrics["accuracy"], c_acc


def main():
    results = []
    print("=== Model 1 (classical), WITHOUT brightness normalization (baseline) ===")
    acc, c_acc = run_model1(normalize=False)
    print(f"  Split B test acc={acc:.3f}  Split C acc={c_acc:.3f}")
    results.append({"model": "model1_classical", "normalized": False, "split_b_test_acc": acc, "split_c_acc": c_acc})

    print("=== Model 1 (classical), WITH brightness normalization ===")
    acc, c_acc = run_model1(normalize=True)
    print(f"  Split B test acc={acc:.3f}  Split C acc={c_acc:.3f}")
    results.append({"model": "model1_classical", "normalized": True, "split_b_test_acc": acc, "split_c_acc": c_acc})

    print("=== Model 4 (EfficientNet-B0), WITHOUT brightness normalization (baseline) ===")
    acc, c_acc = run_model4(normalize=False)
    print(f"  Split B test acc={acc:.3f}  Split C acc={c_acc:.3f}")
    results.append({"model": "model4_efficientnet", "normalized": False, "split_b_test_acc": acc, "split_c_acc": c_acc})

    print("=== Model 4 (EfficientNet-B0), WITH brightness normalization ===")
    acc, c_acc = run_model4(normalize=True)
    print(f"  Split B test acc={acc:.3f}  Split C acc={c_acc:.3f}")
    results.append({"model": "model4_efficientnet", "normalized": True, "split_b_test_acc": acc, "split_c_acc": c_acc})

    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()

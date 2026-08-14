"""
Extends the 3-way normalization finding (resolution + brightness +
compression, data/metadata/capture_method_confound_findings.md Finding 10,
so far tested only on Model 4, where it beat the 2-way combination
50.7%->78.0%) to all 4 models -- mirrors experiment_normalization_all_models.py
exactly but adds the compression bottleneck (experiment_compression_norm.py)
on top of resolution+brightness.

The key open question from Finding 10: Model 3 (MobileNetV3-Small) was the
one model actively HURT by brightness normalization alone (Finding 7,
80.0%->56.0%). Does adding compression normalization on top of
resolution+brightness make Model 3 worse still, recover some of the loss,
or behave differently since compression is a genuinely different axis
(detail/noise-floor, not overall pixel value)?

Same label-free, deployable preprocessing as before, applied identically to
train/test/Split C: resolution capped at 128px short-side, then brightness
rescaled to mean 0.5, then re-encoded through a JPEG quality=40 bottleneck.
Tests baseline vs. 3-way-normalized for Models 1-3; Model 4 baseline/3-way
numbers come from experiment_compression_norm.py's same-run comparison
(this run's own baseline_no_norm_rerun / all_three_combined rows, not an
older cross-script number, to keep the comparison honest given the
documented k_augment=3 non-determinism).

Output: modeling/results/compression_all_models_experiment.csv
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
from experiment_brightness_norm import normalize_brightness, load_split_c_examples
from experiment_resolution_norm import normalize_resolution
from experiment_compression_norm import normalize_compression


def combined_preprocess(im: Image.Image, normalize: bool) -> Image.Image:
    im = im.convert("RGB")
    if normalize:
        im = normalize_resolution(im)
        im = normalize_brightness(im)
        im = normalize_compression(im)
    return im


# ---------- Model 1: classical color histogram + LogReg ----------

def extract_histogram(path, normalize: bool):
    with Image.open(path) as im:
        im = combined_preprocess(im, normalize).resize((IMG_SIZE, IMG_SIZE))
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
    test_metrics = compute_point_metrics(y_test, clf.predict_proba(X_test)[:, 1])

    split_c = load_split_c_examples()
    X_c = np.stack([extract_histogram(e["path"], normalize) for e in split_c])
    c_acc = float((clf.predict_proba(X_c)[:, 1] < 0.5).mean())
    return test_metrics["accuracy"], c_acc


# ---------- Model 2: small CNN, trained end-to-end ----------

def run_model2(normalize: bool):
    from torchvision import transforms
    from train_model2_cnn import SmallCNN
    from torch_utils import train_model, evaluate_model, BATCH_SIZE

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

    class NormDataset(torch.utils.data.Dataset):
        def __init__(self, examples, train, normalize):
            self.examples = examples
            self.tf = build_tf(train)
            self.normalize = normalize

        def __len__(self):
            return len(self.examples)

        def __getitem__(self, idx):
            ex = self.examples[idx]
            with Image.open(ex["path"]) as im:
                im = combined_preprocess(im, self.normalize)
                img = self.tf(im)
            return img, ex["label"], ex["image_id"]

    def make_norm_loader(examples, train, normalize):
        ds = NormDataset(examples, train, normalize)
        g = torch.Generator()
        g.manual_seed(SEED)
        return torch.utils.data.DataLoader(ds, batch_size=BATCH_SIZE, shuffle=train,
                                            generator=g if train else None, num_workers=0)

    examples = load_examples("split_b")
    by_split = {s: [e for e in examples if e["split"] == s] for s in ("train", "val", "test")}

    import torch_utils as tu
    orig_make_loader = tu.make_loader
    tu.make_loader = lambda exs, train, batch_size=BATCH_SIZE: make_norm_loader(exs, train, normalize)
    try:
        set_seed(SEED)
        model = SmallCNN()
        # Was hard-coded 0.0003, which the 2026-07-28 audit found to be stale:
        # Model 2's LR search selects 0.001 under the normalised pipeline. The
        # numbers already reported from this script were produced at 0.0003;
        # because baseline and normalised conditions within one run share the
        # LR, the within-run comparison the ablation claims is unaffected, but
        # its absolute values are not comparable to the production model.
        # Re-run this script to refresh them at the recorded rate.
        from result_io import load_chosen_lr
        model, _ = train_model(model, by_split["train"], by_split["val"],
                               load_chosen_lr("model2_smallcnn_gap"),
                                model_tag="model2_smallcnn_gap", run_tag=f"compnormexp_{normalize}")
        _, y_true, y_prob = evaluate_model(model, by_split["test"])
        test_metrics = compute_point_metrics(y_true, y_prob)

        split_c = load_split_c_examples()
        _, _, c_prob = evaluate_model(model, split_c)
        c_acc = float(np.mean(np.array(c_prob) < 0.5))
    finally:
        tu.make_loader = orig_make_loader

    return test_metrics["accuracy"], c_acc


# ---------- Model 3: MobileNetV3-Small frozen backbone ----------

def run_model3(normalize: bool):
    from torchvision import transforms
    from train_model3_mobilenet import build_backbone, build_head, MODEL_NAME
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
    def extract(feature_extractor, gap, examples, train, k_augment):
        feature_extractor.eval()
        all_X, all_y, all_ids = [], [], []
        tf = build_tf(train)
        for _ in range(k_augment):
            for batch_start in range(0, len(examples), 32):
                batch = examples[batch_start:batch_start + 32]
                imgs = []
                for e in batch:
                    with Image.open(e["path"]) as im:
                        imgs.append(tf(combined_preprocess(im, normalize)))
                x = torch.stack(imgs)
                feats = gap(feature_extractor(x)).flatten(1)
                all_X.append(feats.numpy())
                all_y.extend([e["label"] for e in batch])
                all_ids.extend([e["image_id"] for e in batch])
        return np.concatenate(all_X, axis=0), np.array(all_y), all_ids

    examples = load_examples("split_b")
    by_split = {s: [e for e in examples if e["split"] == s] for s in ("train", "val", "test")}

    feature_extractor, gap = build_backbone()
    X_train, y_train, _ = extract(feature_extractor, gap, by_split["train"], True, 3)
    X_val, y_val, _ = extract(feature_extractor, gap, by_split["val"], False, 1)
    X_test, y_test, _ = extract(feature_extractor, gap, by_split["test"], False, 1)

    set_seed(SEED)
    head = build_head()
    # Read the recorded LR rather than hard-coding it: a hard-coded LR in a
    # rebuild path is exactly the defect the 2026-07-28 audit found in
    # eval_split_c.py. Happens to equal 0.001 for M3/M4 today; will not
    # silently disagree if either is ever retrained at another value.
    from result_io import load_chosen_lr
    head, _ = train_model_on_features(head, X_train, y_train, X_val, y_val,
                                      load_chosen_lr(MODEL_NAME),
                                       model_tag=MODEL_NAME, run_tag=f"compnormexp_{normalize}")
    _, y_true, y_prob = evaluate_model_on_features(head, X_test, y_test, list(range(len(y_test))))
    test_metrics = compute_point_metrics(y_true, y_prob)

    split_c = load_split_c_examples()
    Xc, yc, idsc = extract(feature_extractor, gap, split_c, False, 1)
    _, _, c_prob = evaluate_model_on_features(head, Xc, yc, idsc)
    c_acc = float(np.mean(np.array(c_prob) < 0.5))
    return test_metrics["accuracy"], c_acc


def main():
    results = []
    out_path = Path(__file__).resolve().parent / "results" / "compression_all_models_experiment.csv"
    runners = [("model1_classical", run_model1), ("model2_smallcnn", run_model2), ("model3_mobilenet", run_model3)]
    for name, fn in runners:
        for normalize in (False, True):
            label = "three_way_norm" if normalize else "baseline"
            print(f"=== {name}: {label} ===")
            acc, c_acc = fn(normalize)
            print(f"  Split B test acc={acc:.3f}  Split C acc={c_acc:.3f}")
            results.append({"model": name, "condition": label, "split_b_test_acc": acc, "split_c_acc": c_acc})
            with open(out_path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
                w.writeheader()
                w.writerows(results)

    print(f"\nWrote {out_path}")
    print("Note: Model 4's 3-way numbers are in compression_norm_experiment.csv (same-run baseline+combined).")


if __name__ == "__main__":
    main()

"""
Model 4 — EfficientNet-B0 transfer learning, frozen ImageNet backbone + GAP head.

Same cached-feature approach as Model 3 (see feature_cache.py) — necessary
here even more than for Model 3, since EfficientNet-B0 is heavier and a
first attempt at re-running its forward pass every epoch was killed by the
environment's runtime limit before Split A finished training. Head is
Dropout(0.3) -> Linear(1280, 2), 1280 being EfficientNet-B0's final feature
channel count.

Plan Part 3.1 lists "optional fine-tune" for this model; frozen-only (the
same protocol as Model 3) is run here to keep the CPU training budget
bounded and comparable across all 4 models — fine-tuning the backbone is
left as a documented future extension, not attempted silently.
"""
from pathlib import Path
import sys

import torch
import torch.nn as nn
import torchvision.models as tvm
from sklearn.model_selection import StratifiedGroupKFold
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, set_seed, SEED
from torch_utils import train_model_on_features, evaluate_model_on_features
from feature_cache import extract_features, K_AUGMENT
from result_io import save_predictions, MetricsAccumulator, save_chosen_lr
from metrics import full_report, compute_point_metrics

MODEL_NAME = "model4_efficientnetb0_frozen"
FEATURE_DIM = 1280
LR_GRID = [1e-3, 3e-4, 1e-4]
LR_SEARCH_EPOCHS = 5


def build_backbone():
    backbone = tvm.efficientnet_b0(weights=tvm.EfficientNet_B0_Weights.IMAGENET1K_V1)
    feature_extractor = backbone.features
    for p in feature_extractor.parameters():
        p.requires_grad = False
    gap = nn.AdaptiveAvgPool2d(1)
    return feature_extractor, gap


def build_head():
    return nn.Sequential(nn.Dropout(0.3), nn.Linear(FEATURE_DIM, 2))


_BACKBONE_CACHE = None


def get_features(examples, train: bool, k_augment: int = 1):
    # Build the (frozen, stateless) backbone once and reuse it. Rebuilding
    # torchvision's pretrained EfficientNet-B0 on every call (this function
    # is called ~18 times across LR search / Split A / Split B's 5 folds +
    # final fit) was observed to cause the whole script to stall/get killed
    # for no clear compute reason -- likely weight-cache/lookup overhead
    # repeated far more often than necessary for a backbone that never changes.
    global _BACKBONE_CACHE
    if _BACKBONE_CACHE is None:
        _BACKBONE_CACHE = build_backbone()
    fe, gap = _BACKBONE_CACHE
    return extract_features(fe, gap, examples, train=train, k_augment=k_augment)


def select_lr(X_train, y_train, X_val, y_val):
    print("  LR search (5 epochs each):", LR_GRID)
    best_lr, best_val_loss = None, float("inf")
    for lr in LR_GRID:
        set_seed(SEED)
        model = build_head()
        _, history = train_model_on_features(model, X_train, y_train, X_val, y_val, lr,
                                               model_tag=MODEL_NAME, run_tag=f"lrsearch_{lr}",
                                               max_epochs=LR_SEARCH_EPOCHS, patience=LR_SEARCH_EPOCHS + 1)
        final_val_loss = history[-1]["val_loss"]
        print(f"    lr={lr}: val_loss@epoch{LR_SEARCH_EPOCHS - 1}={final_val_loss:.4f}")
        if final_val_loss < best_val_loss:
            best_val_loss = final_val_loss
            best_lr = lr
    print(f"  selected lr={best_lr}")
    return best_lr


def run_split_a(acc, chosen_lr):
    examples = load_examples("split_a")
    by_split = {s: [e for e in examples if e["split"] == s] for s in ("train", "val", "test")}

    print("  extracting features (train x%d augmented passes, val/test x1)..." % K_AUGMENT)
    X_train, y_train, _ = get_features(by_split["train"], train=True, k_augment=K_AUGMENT)
    X_val, y_val, val_ids = get_features(by_split["val"], train=False, k_augment=1)
    X_test, y_test, test_ids = get_features(by_split["test"], train=False, k_augment=1)

    set_seed(SEED)
    model = build_head()
    model, history = train_model_on_features(model, X_train, y_train, X_val, y_val, chosen_lr,
                                               model_tag=MODEL_NAME, run_tag="split_a")

    for part, X, y, ids in (("val", X_val, y_val, val_ids), ("test", X_test, y_test, test_ids)):
        ids2, y_true, y_prob = evaluate_model_on_features(model, X, y, ids)
        report = full_report(y_true, y_prob, seed=SEED)
        if part == "test":
            save_predictions(MODEL_NAME, "split_a", ids2, y_true, y_prob)
        acc.add("split_a_single_fit", "A", part, report)
        print(f"[Split A] {part}: acc={report['accuracy']:.3f} f1={report['f1']:.3f} "
              f"auc={report['roc_auc']:.3f}")


def run_split_b(acc, chosen_lr):
    examples = load_examples("split_b")
    by_split = {s: [e for e in examples if e["split"] == s] for s in ("train", "val", "test")}
    train_examples = by_split["train"]

    groups = np.array([e["product_identity"] for e in train_examples])
    labels = np.array([e["label"] for e in train_examples])
    X_dummy = np.zeros(len(train_examples))
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)

    fold_metrics = []
    for fold_idx, (tr_idx, va_idx) in enumerate(sgkf.split(X_dummy, labels, groups)):
        fold_train = [train_examples[i] for i in tr_idx]
        fold_val = [train_examples[i] for i in va_idx]

        Xtr, ytr, _ = get_features(fold_train, train=True, k_augment=K_AUGMENT)
        Xva, yva, va_ids = get_features(fold_val, train=False, k_augment=1)

        set_seed(SEED)
        model = build_head()
        model, _ = train_model_on_features(model, Xtr, ytr, Xva, yva, chosen_lr,
                                            model_tag=MODEL_NAME, run_tag=f"split_b_fold{fold_idx}")
        _, y_true, y_prob = evaluate_model_on_features(model, Xva, yva, va_ids)
        m = compute_point_metrics(y_true, y_prob)
        fold_metrics.append(m)
        print(f"[Split B] fold {fold_idx}: acc={m['accuracy']:.3f} f1={m['f1']:.3f}")

    agg = {}
    for key in fold_metrics[0]:
        vals = [m[key] for m in fold_metrics]
        agg[f"{key}_mean"] = float(np.nanmean(vals))
        agg[f"{key}_std"] = float(np.nanstd(vals))
    agg["n_folds"] = 5
    acc.add("split_b_5foldcv", "B", "train_cv", agg)
    print(f"[Split B] 5-fold CV: acc={agg['accuracy_mean']:.3f}+/-{agg['accuracy_std']:.3f}")

    X_train, y_train, _ = get_features(train_examples, train=True, k_augment=K_AUGMENT)
    X_val, y_val, val_ids = get_features(by_split["val"], train=False, k_augment=1)
    X_test, y_test, test_ids = get_features(by_split["test"], train=False, k_augment=1)

    set_seed(SEED)
    model = build_head()
    model, _ = train_model_on_features(model, X_train, y_train, X_val, y_val, chosen_lr,
                                        model_tag=MODEL_NAME, run_tag="split_b_final")
    for part, X, y, ids in (("val", X_val, y_val, val_ids), ("test", X_test, y_test, test_ids)):
        ids2, y_true, y_prob = evaluate_model_on_features(model, X, y, ids)
        report = full_report(y_true, y_prob, seed=SEED)
        if part == "test":
            save_predictions(MODEL_NAME, "split_b", ids2, y_true, y_prob)
        acc.add("split_b_final_fit", "B", part, report)
        print(f"[Split B] {part}: acc={report['accuracy']:.3f} f1={report['f1']:.3f} "
              f"auc={report['roc_auc']:.3f}")


def main():
    print("=== Model 4: EfficientNet-B0 (frozen backbone, cached features) ===")
    acc = MetricsAccumulator(MODEL_NAME)

    examples_a = load_examples("split_a")
    train_a = [e for e in examples_a if e["split"] == "train"]
    val_a = [e for e in examples_a if e["split"] == "val"]
    print("  extracting LR-search features...")
    X_train, y_train, _ = get_features(train_a, train=True, k_augment=K_AUGMENT)
    X_val, y_val, _ = get_features(val_a, train=False, k_augment=1)
    chosen_lr = select_lr(X_train, y_train, X_val, y_val)
    save_chosen_lr(MODEL_NAME, chosen_lr)

    print("--- Split A ---")
    run_split_a(acc, chosen_lr)
    print("--- Split B ---")
    run_split_b(acc, chosen_lr)
    acc.flush()


if __name__ == "__main__":
    main()

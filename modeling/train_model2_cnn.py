"""
Model 2 — From-scratch CNN with a global-average-pooling head.

A conventional 3-conv-block channel progression (16 -> 32 -> 64, each block:
Conv3x3 -> BatchNorm -> ReLU -> MaxPool2x2), with a Global Average Pooling
head -> Dropout(0.5) -> Linear(64, 2) rather than the flatten -> Dense(128)
head that small-dataset CNN work commonly uses. On a 224x224 input the trunk
emits 28x28x64, so a flatten -> Dense(128) head would cost roughly 6.4 M
parameters — about 99.7% of such a network — on 357 training images. GAP
replaces that with 130 parameters and brings the whole model to 23,938,
removing the single largest source of overfitting risk while preserving the
trunk exactly.

LR search: a light 3-value grid {1e-3, 3e-4, 1e-4} is run for 5 epochs each
on Split A train/val only (to bound compute), and the lr with the lowest
val loss at epoch 5 is reused for both Split A and Split B full training
runs — this is the "document the search range, don't over-search" instruction
in plan Part 3.2.
"""
from pathlib import Path
import sys

import torch
import torch.nn as nn
from sklearn.model_selection import StratifiedGroupKFold
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, set_seed, SEED
from torch_utils import train_model, evaluate_model, BATCH_SIZE
from result_io import save_predictions, MetricsAccumulator, save_chosen_lr
from metrics import full_report, compute_point_metrics

MODEL_NAME = "model2_smallcnn_gap"
LR_GRID = [1e-3, 3e-4, 1e-4]
LR_SEARCH_EPOCHS = 5


class SmallCNN(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, 3, padding=1), nn.BatchNorm2d(16), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(16, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),
        )
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.dropout = nn.Dropout(0.5)
        self.fc = nn.Linear(64, 2)

    def forward(self, x):
        x = self.features(x)
        x = self.gap(x).flatten(1)
        x = self.dropout(x)
        return self.fc(x)


def select_lr(train_examples, val_examples):
    print("  LR search (5 epochs each):", LR_GRID)
    best_lr, best_val_loss = None, float("inf")
    for lr in LR_GRID:
        set_seed(SEED)
        model = SmallCNN()
        _, history = train_model(model, train_examples, val_examples, lr,
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

    set_seed(SEED)
    model = SmallCNN()
    model, history = train_model(model, by_split["train"], by_split["val"], chosen_lr,
                                  model_tag=MODEL_NAME, run_tag="split_a")

    for part in ("val", "test"):
        ids, y_true, y_prob = evaluate_model(model, by_split[part])
        report = full_report(y_true, y_prob, seed=SEED)
        if part == "test":
            save_predictions(MODEL_NAME, "split_a", ids, y_true, y_prob)
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
        set_seed(SEED)
        fold_train = [train_examples[i] for i in tr_idx]
        fold_val = [train_examples[i] for i in va_idx]
        model = SmallCNN()
        model, _ = train_model(model, fold_train, fold_val, chosen_lr,
                                model_tag=MODEL_NAME, run_tag=f"split_b_fold{fold_idx}")
        ids, y_true, y_prob = evaluate_model(model, fold_val)
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

    set_seed(SEED)
    model = SmallCNN()
    model, _ = train_model(model, train_examples, by_split["val"], chosen_lr,
                            model_tag=MODEL_NAME, run_tag="split_b_final")
    for part in ("val", "test"):
        ids, y_true, y_prob = evaluate_model(model, by_split[part])
        report = full_report(y_true, y_prob, seed=SEED)
        if part == "test":
            save_predictions(MODEL_NAME, "split_b", ids, y_true, y_prob)
        acc.add("split_b_final_fit", "B", part, report)
        print(f"[Split B] {part}: acc={report['accuracy']:.3f} f1={report['f1']:.3f} "
              f"auc={report['roc_auc']:.3f}")


def main():
    print("=== Model 2: Small CNN with GAP head ===")
    acc = MetricsAccumulator(MODEL_NAME)

    import os
    cached_lr = os.environ.get("PHARMAVISION_MODEL2_LR")
    if cached_lr:
        chosen_lr = float(cached_lr)
        print(f"  using cached lr={chosen_lr} (PHARMAVISION_MODEL2_LR env var, skipping LR search)")
    else:
        examples_a = load_examples("split_a")
        train_a = [e for e in examples_a if e["split"] == "train"]
        val_a = [e for e in examples_a if e["split"] == "val"]
        chosen_lr = select_lr(train_a, val_a)

    # Record it so eval_split_c*.py rebuild this model at the same LR instead
    # of carrying a hand-synced constant.
    save_chosen_lr(MODEL_NAME, chosen_lr)

    print("--- Split A ---")
    run_split_a(acc, chosen_lr)
    print("--- Split B ---")
    run_split_b(acc, chosen_lr)
    acc.flush()


if __name__ == "__main__":
    main()

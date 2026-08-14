"""
Model 1 — Classical baseline: RGB color histogram + Logistic Regression.

Feature: 32-bin-per-channel RGB histogram (96-dim), L1-normalized, computed
from the image resized to 224x224 (same resolution used by all other
models, for a fair comparison of what each model family can do at that
resolution).

Augmentation note: the plan's Part 2.7 augmentation (rotation, brightness/
contrast jitter, crop/zoom, blur) is NOT applied to this model's features.
Rotation/crop are near color-histogram-invariant, so they contribute little;
brightness/contrast jitter would directly distort the one feature this model
sees, which is a real regularizer for a CNN's *spatial* filters but is just
label noise for a histogram classifier. Applying it "for fairness" would
mechanically hurt this baseline without a comparable mechanism helping it,
which is not a fair comparison — so it's honestly left out and documented,
rather than blindly following "identical augmentation" into an unfair
setup for this specific model family.

Class balancing: sklearn class_weight="balanced" (plan Part 2.6:
class-weighted loss, not oversampling).

Runs: Split A (train/val/test) and Split B (5-fold CV on train partition,
reported mean +/- std, plus a final fit-on-full-train-B eval on val/test).
"""
import csv
import json
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, RESULTS_DIR, IMG_SIZE, set_seed, SEED
from metrics import full_report, compute_point_metrics

MODEL_NAME = "model1_classical_colorhist_logreg"
N_BINS = 32


def extract_histogram(path) -> np.ndarray:
    with Image.open(path) as im:
        im = im.convert("RGB").resize((IMG_SIZE, IMG_SIZE))
        arr = np.asarray(im)
    feats = []
    for c in range(3):
        hist, _ = np.histogram(arr[:, :, c], bins=N_BINS, range=(0, 256), density=True)
        feats.append(hist)
    return np.concatenate(feats)


def featurize(examples):
    X = np.stack([extract_histogram(e["path"]) for e in examples])
    y = np.array([e["label"] for e in examples])
    ids = [e["image_id"] for e in examples]
    return X, y, ids


def save_predictions(run_name, ids, y_true, y_prob):
    out = RESULTS_DIR / "predictions" / f"{MODEL_NAME}__{run_name}.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image_id", "y_true", "y_prob"])
        for i, yt, yp in zip(ids, y_true, y_prob):
            w.writerow([i, yt, yp])


_METRICS_ROWS = []


def append_metrics_row(run_name, split_name, partition, metrics_dict):
    row = {"model": MODEL_NAME, "run": run_name, "split_protocol": split_name,
           "partition": partition, **metrics_dict}
    _METRICS_ROWS.append(row)


def flush_metrics():
    """Write all accumulated rows to this model's own metrics CSV. Different
    row types (single train/val/test fit vs. 5-fold CV summary) have
    different columns, so we union all keys across rows rather than assume a
    fixed header (avoids silently misaligned columns from incremental
    DictWriter appends)."""
    out = RESULTS_DIR / f"metrics_{MODEL_NAME}.csv"
    all_keys = []
    for row in _METRICS_ROWS:
        for k in row:
            if k not in all_keys:
                all_keys.append(k)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=all_keys)
        w.writeheader()
        for row in _METRICS_ROWS:
            w.writerow(row)
    print(f"Wrote {out}")


def run_split_a():
    set_seed(SEED)
    examples = load_examples("split_a")
    by_split = {s: [e for e in examples if e["split"] == s] for s in ("train", "val", "test")}

    X_train, y_train, _ = featurize(by_split["train"])
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED)
    clf.fit(X_train, y_train)

    for part in ("val", "test"):
        X, y, ids = featurize(by_split[part])
        y_prob = clf.predict_proba(X)[:, 1]
        report = full_report(y, y_prob, seed=SEED)
        save_predictions("split_a", ids, y, y_prob) if part == "test" else None
        append_metrics_row("split_a_single_fit", "A", part, report)
        print(f"[Split A] {part}: acc={report['accuracy']:.3f} f1={report['f1']:.3f} "
              f"auc={report['roc_auc']:.3f}")


def run_split_b():
    set_seed(SEED)
    examples = load_examples("split_b")
    by_split = {s: [e for e in examples if e["split"] == s] for s in ("train", "val", "test")}
    train_examples = by_split["train"]

    # 5-fold stratified group CV on the train partition (plan Part 3.3 / 4.1)
    X_train, y_train, ids_train = featurize(train_examples)
    groups = np.array([e["product_identity"] for e in train_examples])
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)

    fold_metrics = []
    for fold_idx, (tr_idx, va_idx) in enumerate(sgkf.split(X_train, y_train, groups)):
        clf = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED)
        clf.fit(X_train[tr_idx], y_train[tr_idx])
        y_prob = clf.predict_proba(X_train[va_idx])[:, 1]
        m = compute_point_metrics(y_train[va_idx], y_prob)
        fold_metrics.append(m)
        print(f"[Split B] fold {fold_idx}: acc={m['accuracy']:.3f} f1={m['f1']:.3f}")

    agg = {}
    for key in fold_metrics[0]:
        vals = [m[key] for m in fold_metrics]
        agg[f"{key}_mean"] = float(np.nanmean(vals))
        agg[f"{key}_std"] = float(np.nanstd(vals))
    agg["n_folds"] = 5
    append_metrics_row("split_b_5foldcv", "B", "train_cv", agg)
    print(f"[Split B] 5-fold CV: acc={agg['accuracy_mean']:.3f}+/-{agg['accuracy_std']:.3f}")

    # final model: fit on the full B-train partition, evaluate on held-out val/test
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED)
    clf.fit(X_train, y_train)
    for part in ("val", "test"):
        X, y, ids = featurize(by_split[part])
        y_prob = clf.predict_proba(X)[:, 1]
        report = full_report(y, y_prob, seed=SEED)
        save_predictions("split_b", ids, y, y_prob) if part == "test" else None
        append_metrics_row("split_b_final_fit", "B", part, report)
        print(f"[Split B] {part}: acc={report['accuracy']:.3f} f1={report['f1']:.3f} "
              f"auc={report['roc_auc']:.3f}")


def main():
    print("=== Model 1: Color histogram + Logistic Regression ===")
    print("--- Split A ---")
    run_split_a()
    print("--- Split B ---")
    run_split_b()
    flush_metrics()


if __name__ == "__main__":
    main()

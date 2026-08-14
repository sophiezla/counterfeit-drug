"""
Synthetic-counterfeit Split C evaluation (see
data/metadata/synthetic_counterfeit_findings.md and HANDOFF.md's history).

Split C has always been authentic-only in this project (eval_split_c.py) --
no genuine independent counterfeit-labeled source exists. This evaluates
the same 4 models against a SYNTHETIC counterfeit proxy instead: the same
150 independent Mendeley "Huawei CN" authentic photos, paired with 150
approved synthetic-counterfeit perturbations of THOSE SAME photos
(data/metadata/split_c_synthetic_provenance.csv), built to control for the
capture-method confound (Finding 1) by construction -- the perturbation is
the only systematic difference between the two classes here.

This is explicitly a stress-test proxy, analogous to ImageNet-C corruption
benchmarks -- it measures robustness to a specific synthetic perturbation
style, NOT real-world counterfeit-detection recall. Never report it as the
latter.

Each model is deterministically retrained on Split B's train pool (same
seed/procedure as eval_split_c.py) then evaluated on the 300 synthetic
Split C images, reporting full binary metrics (accuracy, precision, recall,
F1, ROC-AUC) since this set (unlike the authentic-only Split C) has both
classes.

Output: modeling/results/split_c_synthetic_eval.csv (kept separate from
split_c_eval.csv -- the two must never be confused or merged in reporting).
"""
import csv
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, RAW, set_seed, SEED, LABEL_TO_INT
from metrics import compute_point_metrics
from result_io import load_chosen_lr

ROOT = Path(__file__).resolve().parent.parent
SYNTHETIC_PROV = ROOT / "data" / "metadata" / "split_c_synthetic_provenance.csv"
RESULTS_DIR = ROOT / "modeling" / "results"


def load_split_c_synthetic_examples():
    with open(SYNTHETIC_PROV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    examples = []
    for r in rows:
        examples.append({
            "image_id": r["image_id"],
            "path": RAW / r["orig_relpath"],
            "label": LABEL_TO_INT[r["class_label"]],
            "split": "split_c_synthetic",
            "product_identity": r["image_id"],
            "cv_fold": None,
        })
    return examples


def eval_model1():
    from train_model1_classical import extract_histogram
    from sklearn.linear_model import LogisticRegression

    examples = load_examples("split_b")
    train_examples = [e for e in examples if e["split"] == "train"]
    X_train = np.stack([extract_histogram(e["path"]) for e in train_examples])
    y_train = np.array([e["label"] for e in train_examples])

    set_seed(SEED)
    clf = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=SEED)
    clf.fit(X_train, y_train)

    split_c = load_split_c_synthetic_examples()
    X_c = np.stack([extract_histogram(e["path"]) for e in split_c])
    y_true = np.array([e["label"] for e in split_c])
    y_prob = clf.predict_proba(X_c)[:, 1]
    return y_true, y_prob


def eval_model2():
    from train_model2_cnn import SmallCNN
    from torch_utils import train_model, evaluate_model

    examples = load_examples("split_b")
    train_examples = [e for e in examples if e["split"] == "train"]
    val_examples = [e for e in examples if e["split"] == "val"]

    # Read the LR the real training run recorded, same as eval_split_c.py.
    chosen_lr = load_chosen_lr("model2_smallcnn_gap")

    set_seed(SEED)
    model = SmallCNN()
    model, _ = train_model(model, train_examples, val_examples, chosen_lr,
                            model_tag="model2_smallcnn_gap", run_tag="split_c_synthetic_eval_rebuild")

    split_c = load_split_c_synthetic_examples()
    ids, y_true, y_prob = evaluate_model(model, split_c)
    return np.array(y_true), np.array(y_prob)


def eval_frozen_backbone_model(module_name):
    import importlib
    mod = importlib.import_module(module_name)
    from torch_utils import train_model_on_features, evaluate_model_on_features

    examples = load_examples("split_b")
    train_examples = [e for e in examples if e["split"] == "train"]
    val_examples = [e for e in examples if e["split"] == "val"]

    X_train, y_train, _ = mod.get_features(train_examples, train=True, k_augment=3)
    X_val, y_val, _ = mod.get_features(val_examples, train=False, k_augment=1)
    chosen_lr = load_chosen_lr(mod.MODEL_NAME)

    set_seed(SEED)
    head = mod.build_head()
    head, _ = train_model_on_features(head, X_train, y_train, X_val, y_val, chosen_lr,
                                       model_tag=mod.MODEL_NAME, run_tag="split_c_synthetic_eval_rebuild")

    split_c = load_split_c_synthetic_examples()
    X_c, y_c, ids_c = mod.get_features(split_c, train=False, k_augment=1)
    ids, y_true, y_prob = evaluate_model_on_features(head, X_c, y_c, ids_c)
    return np.array(y_true), np.array(y_prob)


FIELDNAMES = ["model", "n", "accuracy", "precision", "recall", "f1", "roc_auc"]
OUT_PATH = RESULTS_DIR / "split_c_synthetic_eval.csv"


def load_done_models():
    if not OUT_PATH.exists():
        return {}
    with open(OUT_PATH, newline="", encoding="utf-8") as f:
        return {r["model"]: r for r in csv.DictReader(f)}


def append_result(row):
    # incremental write, same rationale as eval_split_c.py: this environment
    # kills background processes unpredictably, so a kill mid-run should
    # lose at most the in-progress model, not everything already computed.
    write_header = not OUT_PATH.exists()
    with open(OUT_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            w.writeheader()
        w.writerow(row)


def run_one(model_key, label, eval_fn):
    done = load_done_models()
    if model_key in done:
        print(f"\n--- {label}: already done, skipping (delete split_c_synthetic_eval.csv row to redo) ---")
        return
    print(f"\n--- {label} ---")
    y_true, y_prob = eval_fn()
    metrics = compute_point_metrics(y_true, y_prob)
    row = {"model": model_key, "n": len(y_true), **metrics}
    append_result(row)
    print(f"acc={metrics['accuracy']:.3f} prec={metrics['precision']:.3f} "
          f"recall={metrics['recall']:.3f} f1={metrics['f1']:.3f} "
          f"roc_auc={metrics['roc_auc']:.3f} (n={len(y_true)})")


def main():
    print("=== Synthetic-counterfeit Split C evaluation (proxy stress-test, NOT real counterfeit recall) ===")
    run_one("model1_classical_colorhist_logreg", "Model 1 (classical)", eval_model1)
    run_one("model2_smallcnn_gap", "Model 2 (small CNN)", eval_model2)
    run_one("model3_mobilenetv3small_frozen", "Model 3 (MobileNetV3-Small)",
            lambda: eval_frozen_backbone_model("train_model3_mobilenet"))
    run_one("model4_efficientnetb0_frozen", "Model 4 (EfficientNet-B0)",
            lambda: eval_frozen_backbone_model("train_model4_efficientnet"))
    print(f"\nDone. Results in {OUT_PATH}")


if __name__ == "__main__":
    main()

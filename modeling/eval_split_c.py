"""
Split C evaluation (plan Part 4.3) — external generalization check.

Split C here is AUTHENTIC-ONLY (see data/README.md and the Mendeley
candidate's provenance: it has no counterfeit label), per the user's
explicit direction after the original plan's two-class Split C source
search came up empty on independence grounds. This measures each model's
specificity on a source it has NEVER seen -- counterfeit is the positive
class, so accuracy on an authentic-only set is the true-negative rate. From a
different country,
different photographers, different camera hardware, and programmatically
verified (07_verify_split_c_independence.py) to be non-duplicative of the
training pool -- a genuine test of whether "authentic packaging" was
learned as a transferable concept or as source-specific pattern matching.

Each model is deterministically retrained on Split B's train pool (same
seed, same procedure as the original training scripts -- consistent with
how gradcam.py already reconstructs a trained model without a persisted
checkpoint) then evaluated on the 150 verified-independent Mendeley images.

For comparison, each model's authentic-class accuracy on its OWN Split B
test set (Kaggle, same distribution as training) is recomputed from the
already-saved prediction CSVs, so the "in-distribution vs external" gap is
directly visible.

Output: modeling/results/split_c_eval.csv
"""
import csv
from pathlib import Path
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, RAW, set_seed, SEED, IMG_SIZE
from result_io import MetricsAccumulator, load_chosen_lr

ROOT = Path(__file__).resolve().parent.parent
CANDIDATE_PROV = ROOT / "data" / "metadata" / "split_c_candidate_provenance.csv"
RESULTS_DIR = ROOT / "modeling" / "results"


def load_split_c_examples():
    with open(CANDIDATE_PROV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    examples = []
    for r in rows:
        examples.append({
            "image_id": r["image_id"],
            "path": RAW / r["orig_relpath"],
            "label": 0,  # all authentic
            "split": "split_c",
            "product_identity": r["image_id"],
            "cv_fold": None,
        })
    return examples


def in_distribution_authentic_acc(model_name):
    """Authentic-class accuracy on the model's own Split B test set, from
    already-saved predictions (no retraining needed for this part)."""
    path = RESULTS_DIR / "predictions" / f"{model_name}__split_b.csv"
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    authentic_rows = [r for r in rows if int(r["y_true"]) == 0]
    correct = sum(1 for r in authentic_rows if float(r["y_prob"]) < 0.5)
    return correct / len(authentic_rows), len(authentic_rows)


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

    split_c = load_split_c_examples()
    X_c = np.stack([extract_histogram(e["path"]) for e in split_c])
    y_prob = clf.predict_proba(X_c)[:, 1]
    acc = float((y_prob < 0.5).mean())
    return acc, len(split_c)


def eval_model2():
    from train_model2_cnn import SmallCNN
    from torch_utils import train_model, evaluate_model

    examples = load_examples("split_b")
    train_examples = [e for e in examples if e["split"] == "train"]
    val_examples = [e for e in examples if e["split"] == "val"]

    # The LR the real training run actually used, read from the record that
    # train_model2_cnn.py writes (modeling/results/chosen_lrs.json). This used
    # to be a hard-coded constant and went out of sync with the training run
    # twice -- see result_io.save_chosen_lr for the history. Re-running the LR
    # search here instead would cost ~15 redundant epochs per invocation.
    chosen_lr = load_chosen_lr("model2_smallcnn_gap")

    set_seed(SEED)
    model = SmallCNN()
    model, _ = train_model(model, train_examples, val_examples, chosen_lr,
                            model_tag="model2_smallcnn_gap", run_tag="split_c_eval_rebuild")

    split_c = load_split_c_examples()
    _, y_true, y_prob = evaluate_model(model, split_c)
    acc = float(np.mean(np.array(y_prob) < 0.5))
    return acc, len(split_c)


def eval_frozen_backbone_model(module_name):
    import importlib
    mod = importlib.import_module(module_name)
    from torch_utils import train_model_on_features, evaluate_model_on_features

    examples = load_examples("split_b")
    train_examples = [e for e in examples if e["split"] == "train"]
    val_examples = [e for e in examples if e["split"] == "val"]

    X_train, y_train, _ = mod.get_features(train_examples, train=True, k_augment=3)
    X_val, y_val, _ = mod.get_features(val_examples, train=False, k_augment=1)
    # As for Model 2: read the LR the real training run recorded rather than
    # re-searching or hard-coding it.
    chosen_lr = load_chosen_lr(mod.MODEL_NAME)

    set_seed(SEED)
    head = mod.build_head()
    head, _ = train_model_on_features(head, X_train, y_train, X_val, y_val, chosen_lr,
                                       model_tag=mod.MODEL_NAME, run_tag="split_c_eval_rebuild")

    split_c = load_split_c_examples()
    X_c, y_c, ids_c = mod.get_features(split_c, train=False, k_augment=1)
    _, y_true, y_prob = evaluate_model_on_features(head, X_c, y_c, ids_c)
    acc = float(np.mean(np.array(y_prob) < 0.5))
    return acc, len(split_c)


FIELDNAMES = ["model", "split_c_authentic_acc", "split_c_n",
              "split_b_test_authentic_acc", "split_b_test_n", "gap"]
OUT_PATH = RESULTS_DIR / "split_c_eval.csv"


def load_done_models():
    if not OUT_PATH.exists():
        return {}
    with open(OUT_PATH, newline="", encoding="utf-8") as f:
        return {r["model"]: r for r in csv.DictReader(f)}


def append_result(row):
    # incremental write: a kill mid-run loses at most the in-progress model,
    # not everything (this script was interrupted by the environment
    # multiple times during development -- see modeling/README.md)
    write_header = not OUT_PATH.exists()
    with open(OUT_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            w.writeheader()
        w.writerow(row)


def run_one(model_key, label, eval_fn, pred_file_name):
    done = load_done_models()
    if model_key in done:
        print(f"\n--- {label}: already done, skipping (delete split_c_eval.csv row to redo) ---")
        return
    print(f"\n--- {label} ---")
    acc, n = eval_fn()
    id_acc, id_n = in_distribution_authentic_acc(pred_file_name)
    row = {"model": model_key, "split_c_authentic_acc": acc, "split_c_n": n,
           "split_b_test_authentic_acc": id_acc, "split_b_test_n": id_n,
           "gap": id_acc - acc}
    append_result(row)
    print(f"Split C authentic acc: {acc:.3f} (n={n}); Split B test authentic acc: {id_acc:.3f} (n={id_n})")


def main():
    print("=== Split C (external, authentic-only) evaluation ===")
    run_one("model1_classical_colorhist_logreg", "Model 1 (classical)",
            eval_model1, "model1_classical_colorhist_logreg")
    run_one("model2_smallcnn_gap", "Model 2 (small CNN)",
            eval_model2, "model2_smallcnn_gap")
    run_one("model3_mobilenetv3small_frozen", "Model 3 (MobileNetV3-Small)",
            lambda: eval_frozen_backbone_model("train_model3_mobilenet"), "model3_mobilenetv3small_frozen")
    run_one("model4_efficientnetb0_frozen", "Model 4 (EfficientNet-B0)",
            lambda: eval_frozen_backbone_model("train_model4_efficientnet"), "model4_efficientnetb0_frozen")
    print(f"\nDone. Results in {OUT_PATH}")


if __name__ == "__main__":
    main()

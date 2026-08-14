"""
Step 6 (modeling) — Build the paper's headline leakage-quantification table
and run McNemar's tests between model pairs (plan Part 4.2 and 4.4).

Reads every modeling/results/metrics_*.csv and modeling/results/predictions/
*.csv produced by the 4 train_model*.py scripts.

Outputs:
  modeling/results/leakage_table.csv   — one row per model: Split A test acc
    (with 95% CI) vs Split B test acc (with 95% CI) vs Split B 5-fold CV
    mean+/-std, and the A-vs-B delta.
  modeling/results/mcnemar_table.csv   — pairwise McNemar's test between all
    models' Split B test-set predictions.
"""
import csv
import glob
from pathlib import Path

from common import RESULTS_DIR
from metrics import mcnemar_test

MODEL_ORDER = [
    "model1_classical_colorhist_logreg",
    "model2_smallcnn_gap",
    "model3_mobilenetv3small_frozen",
    "model4_efficientnetb0_frozen",
]


def read_metrics(model_name):
    path = RESULTS_DIR / f"metrics_{model_name}.csv"
    if not path.exists():
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_predictions(model_name, run_name):
    path = RESULTS_DIR / "predictions" / f"{model_name}__{run_name}.csv"
    if not path.exists():
        return None
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    ids = [r["image_id"] for r in rows]
    y_true = [int(r["y_true"]) for r in rows]
    y_prob = [float(r["y_prob"]) for r in rows]
    y_pred = [1 if p >= 0.5 else 0 for p in y_prob]
    return {"ids": ids, "y_true": y_true, "y_prob": y_prob, "y_pred": y_pred}


def build_leakage_table():
    out_rows = []
    for model_name in MODEL_ORDER:
        rows = read_metrics(model_name)
        if not rows:
            print(f"WARNING: no metrics found for {model_name}, skipping")
            continue
        by_run_part = {(r["run"], r["partition"]): r for r in rows}

        a_test = by_run_part.get(("split_a_single_fit", "test"))
        b_test = by_run_part.get(("split_b_final_fit", "test"))
        b_cv = by_run_part.get(("split_b_5foldcv", "train_cv"))

        row = {"model": model_name}
        if a_test:
            row["split_a_test_acc"] = a_test["accuracy"]
            row["split_a_test_acc_ci"] = f"[{float(a_test['accuracy_ci_lo']):.3f}, {float(a_test['accuracy_ci_hi']):.3f}]"
            row["split_a_test_auc"] = a_test["roc_auc"]
        if b_test:
            row["split_b_test_acc"] = b_test["accuracy"]
            row["split_b_test_acc_ci"] = f"[{float(b_test['accuracy_ci_lo']):.3f}, {float(b_test['accuracy_ci_hi']):.3f}]"
            row["split_b_test_auc"] = b_test["roc_auc"]
        if b_cv:
            row["split_b_cv_acc_mean"] = b_cv["accuracy_mean"]
            row["split_b_cv_acc_std"] = b_cv["accuracy_std"]
        if a_test and b_test:
            row["delta_acc_A_minus_B"] = float(a_test["accuracy"]) - float(b_test["accuracy"])
        out_rows.append(row)

    if not out_rows:
        print("No results yet to aggregate.")
        return

    all_keys = []
    for row in out_rows:
        for k in row:
            if k not in all_keys:
                all_keys.append(k)
    out_path = RESULTS_DIR / "leakage_table.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=all_keys)
        w.writeheader()
        w.writerows(out_rows)
    print(f"Wrote {out_path}")
    for row in out_rows:
        print(row)


def build_mcnemar_table():
    preds = {}
    for model_name in MODEL_ORDER:
        p = read_predictions(model_name, "split_b")
        if p:
            preds[model_name] = p

    models = list(preds.keys())
    if len(models) < 2:
        print("Not enough models with Split B predictions for McNemar's tests yet.")
        return

    out_rows = []
    for i in range(len(models)):
        for j in range(i + 1, len(models)):
            m1, m2 = models[i], models[j]
            p1, p2 = preds[m1], preds[m2]
            if p1["ids"] != p2["ids"]:
                # align by image_id in case ordering differs
                d2 = dict(zip(p2["ids"], p2["y_pred"]))
                y_true = p1["y_true"]
                y_pred_a = p1["y_pred"]
                y_pred_b = [d2[i] for i in p1["ids"]]
            else:
                y_true, y_pred_a, y_pred_b = p1["y_true"], p1["y_pred"], p2["y_pred"]
            stat, pval = mcnemar_test(y_true, y_pred_a, y_pred_b)
            out_rows.append({"model_a": m1, "model_b": m2, "statistic": stat, "p_value": pval,
                              "significant_at_0.05": pval < 0.05})

    out_path = RESULTS_DIR / "mcnemar_table.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)
    print(f"Wrote {out_path}")
    for row in out_rows:
        print(row)


def main():
    build_leakage_table()
    build_mcnemar_table()


if __name__ == "__main__":
    main()

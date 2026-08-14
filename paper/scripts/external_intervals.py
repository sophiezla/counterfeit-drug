"""
Wilson score intervals for every accuracy reported on the external evaluation
sets (Table X, Table XI).

The in-distribution tables carry bootstrap intervals; the external ones did
not, even though the external result is the paper's headline. These are exact
binomial intervals on the reported counts, so no retraining or resampling is
needed -- Split C is 150 independent images and the synthetic proxy 300.

They quantify sampling uncertainty on a fixed trained model. They do NOT
capture training-run variance, which would need repeated seeds; the paper says
so where it cites them.

Writes paper/tables/table_external_intervals.csv.
"""

import csv
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "paper", "tables", "table_external_intervals.csv")

NAMES = {
    "model1_classical_colorhist_logreg": "M1 hist+LR",
    "model2_smallcnn_gap": "M2 CNN",
    "model3_mobilenetv3small_frozen": "M3 MobileNetV3",
    "model4_efficientnetb0_frozen": "M4 EfficientNet-B0",
}
ORDER = ["M1 hist+LR", "M2 CNN", "M3 MobileNetV3", "M4 EfficientNet-B0"]

# Split C baseline (pre-normalisation) correct counts out of 150, from the
# archived pre-normalisation production run. Stored as counts rather than the
# rounded accuracies Table X prints, so the interval is exact.
BASELINE_K = {
    "M1 hist+LR": 0,
    "M2 CNN": 0,
    "M3 MobileNetV3": 104,
    "M4 EfficientNet-B0": 5,
}


def wilson(k, n, z=1.959963985):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def hanley_mcneil(auc, n_pos, n_neg, z=1.959963985):
    """Closed-form 95% CI for ROC-AUC (Hanley & McNeil, 1982).

    Used because the synthetic-proxy evaluation script did not persist
    per-image scores, so a bootstrap over scores is not available. This
    estimator needs only the AUC and the two class sizes; it is mildly
    conservative for AUCs near 0.5.
    """
    q1 = auc / (2 - auc)
    q2 = 2 * auc * auc / (1 + auc)
    var = (
        auc * (1 - auc)
        + (n_pos - 1) * (q1 - auc * auc)
        + (n_neg - 1) * (q2 - auc * auc)
    ) / (n_pos * n_neg)
    se = np.sqrt(max(var, 0.0))
    return (max(0.0, auc - z * se), min(1.0, auc + z * se))


def counts(acc, n):
    """Recover the integer success count from a reported accuracy."""
    k = round(acc * n)
    assert abs(k / n - acc) < 1e-6, f"{acc} is not a k/{n} proportion"
    return k


def fmt(acc, n):
    k = counts(acc, n)
    lo, hi = wilson(k, n)
    return k, f"{acc:.3f} [{lo:.3f}, {hi:.3f}]"


def main():
    rows = []

    ext = {
        NAMES[r["model"]]: r
        for r in csv.DictReader(
            open(os.path.join(ROOT, "modeling", "results", "split_c_eval.csv"),
                 newline="", encoding="utf-8")
        )
    }
    syn = {
        NAMES[r["model"]]: r
        for r in csv.DictReader(
            open(os.path.join(ROOT, "modeling", "results",
                              "split_c_synthetic_eval.csv"),
                 newline="", encoding="utf-8")
        )
    }

    for m in ORDER:
        e = ext[m]
        n_c = int(e["split_c_n"])
        n_b = int(e["split_b_test_n"])

        k, s = fmt(float(e["split_b_test_authentic_acc"]), n_b)
        rows.append({"model": m, "quantity": "in-distribution authentic acc",
                     "n": n_b, "k": k, "value_ci": s})

        kb = BASELINE_K[m]
        lo, hi = wilson(kb, n_c)
        rows.append({"model": m, "quantity": "Split C, baseline",
                     "n": n_c, "k": kb,
                     "value_ci": f"{kb / n_c:.3f} [{lo:.3f}, {hi:.3f}]"})

        k, s = fmt(float(e["split_c_authentic_acc"]), n_c)
        rows.append({"model": m, "quantity": "Split C, 3-way normalised",
                     "n": n_c, "k": k, "value_ci": s})

        n_s = int(syn[m]["n"])
        k, s = fmt(float(syn[m]["accuracy"]), n_s)
        rows.append({"model": m, "quantity": "synthetic proxy accuracy",
                     "n": n_s, "k": k, "value_ci": s})

        auc = float(syn[m]["roc_auc"])
        lo, hi = hanley_mcneil(auc, n_s // 2, n_s // 2)
        rows.append({"model": m, "quantity": "synthetic proxy ROC-AUC",
                     "n": n_s, "k": "",
                     "value_ci": f"{auc:.3f} [{lo:.3f}, {hi:.3f}]"})

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["model", "quantity", "n", "k",
                                           "value_ci"])
        w.writeheader()
        w.writerows(rows)

    for r in rows:
        print(f"{r['model']:<20} {r['quantity']:<30} "
              f"{r['k']:>3}/{r['n']:<4} {r['value_ci']}")
    print(f"\nwrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()

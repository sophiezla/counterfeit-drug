"""
Metric computation shared by all models: point metrics + bootstrap CIs,
McNemar's test for paired model comparison.
"""
import numpy as np
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                              f1_score, roc_auc_score)


def compute_point_metrics(y_true, y_prob, threshold=0.5):
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    y_pred = (y_prob >= threshold).astype(int)
    out = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }
    # ROC-AUC undefined if only one class present in y_true
    if len(set(y_true.tolist())) > 1:
        out["roc_auc"] = roc_auc_score(y_true, y_prob)
    else:
        out["roc_auc"] = float("nan")
    return out


def bootstrap_ci(y_true, y_prob, metric_name="accuracy", n_boot=1000, seed=42, alpha=0.05):
    """95% CI via bootstrap resampling of the test set (plan Part 4.1)."""
    rng = np.random.RandomState(seed)
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    n = len(y_true)
    values = []
    for _ in range(n_boot):
        idx = rng.randint(0, n, size=n)
        yt, yp = y_true[idx], y_prob[idx]
        if len(set(yt.tolist())) < 2 and metric_name == "roc_auc":
            continue
        m = compute_point_metrics(yt, yp)
        values.append(m[metric_name])
    values = np.array(values)
    lo = np.percentile(values, 100 * alpha / 2)
    hi = np.percentile(values, 100 * (1 - alpha / 2))
    return float(lo), float(hi)


def full_report(y_true, y_prob, n_boot=1000, seed=42):
    point = compute_point_metrics(y_true, y_prob)
    report = {}
    for name, val in point.items():
        report[name] = val
        if name == "roc_auc" and np.isnan(val):
            report[f"{name}_ci_lo"] = float("nan")
            report[f"{name}_ci_hi"] = float("nan")
            continue
        lo, hi = bootstrap_ci(y_true, y_prob, metric_name=name, n_boot=n_boot, seed=seed)
        report[f"{name}_ci_lo"] = lo
        report[f"{name}_ci_hi"] = hi
    report["n_test"] = len(y_true)
    return report


def mcnemar_test(y_true, y_pred_a, y_pred_b):
    """
    McNemar's test between two models' predictions on the SAME test set
    (plan Part 4.4). Returns (statistic, p_value).
    Uses the exact binomial test when the discordant count is small,
    otherwise the standard chi-square approximation with continuity correction.
    """
    from scipy.stats import binomtest, chi2

    y_true = np.asarray(y_true)
    y_pred_a = np.asarray(y_pred_a)
    y_pred_b = np.asarray(y_pred_b)

    a_correct = (y_pred_a == y_true)
    b_correct = (y_pred_b == y_true)

    n01 = int(np.sum(a_correct & ~b_correct))  # a right, b wrong
    n10 = int(np.sum(~a_correct & b_correct))  # a wrong, b right
    n_discordant = n01 + n10

    if n_discordant == 0:
        return 0.0, 1.0

    if n_discordant < 25:
        result = binomtest(min(n01, n10), n_discordant, 0.5)
        return float(n_discordant), float(result.pvalue)

    stat = (abs(n01 - n10) - 1) ** 2 / n_discordant
    p = 1 - chi2.cdf(stat, df=1)
    return float(stat), float(p)

"""
Compute the full extended metric set the manuscript reports, from artifacts
already on disk. NOTHING here retrains a model or invents a number.

Sources read (all produced by modeling/):
  results/predictions/<model>__split_{a,b}.csv   per-image (y_true, y_prob)
  results/metrics_<model>.csv                    5-fold CV summaries + CIs
  results/split_c_eval.csv                       authentic-only external eval
  results/split_c_synthetic_eval.csv             synthetic-proxy eval
  results/curves/*.csv                           per-epoch train/val curves

Written to paper/tables/*.csv (one file per manuscript table).

Extended metrics beyond what modeling/metrics.py computed: specificity,
balanced accuracy, MCC, PR-AUC (average precision), and full confusion
matrices. Positive class = counterfeit (authentic=0, counterfeit=1), the
project-wide convention fixed in modeling/common.py.

For the synthetic Split C set, per-image scores were never persisted by
eval_split_c_synthetic.py, so the confusion matrix is reconstructed exactly
(integer-verified) from the reported accuracy/precision/recall on a known
150/150 class balance. Threshold-free metrics that need raw scores (PR-AUC)
are therefore NOT available for that set and are reported as such rather
than approximated.
"""
import csv
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                            f1_score, roc_auc_score, average_precision_score,
                            matthews_corrcoef, balanced_accuracy_score,
                            confusion_matrix, roc_curve, precision_recall_curve)

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "modeling" / "results"
OUT = ROOT / "paper" / "tables"
OUT.mkdir(parents=True, exist_ok=True)

MODELS = [
    ("model1_classical_colorhist_logreg", "M1", "Colour histogram + LogReg"),
    ("model2_smallcnn_gap", "M2", "Small CNN (GAP head)"),
    ("model3_mobilenetv3small_frozen", "M3", "MobileNetV3-Small (frozen)"),
    ("model4_efficientnetb0_frozen", "M4", "EfficientNet-B0 (frozen)"),
]

SEED = 42
N_BOOT = 2000


def read_predictions(model, split):
    p = RES / "predictions" / f"{model}__{split}.csv"
    with open(p, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    ids = [r["image_id"] for r in rows]
    y = np.array([int(r["y_true"]) for r in rows])
    prob = np.array([float(r["y_prob"]) for r in rows])
    return ids, y, prob


def all_metrics(y, prob, thr=0.5):
    pred = (prob >= thr).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    spec = tn / (tn + fp) if (tn + fp) else float("nan")
    return {
        "n": int(len(y)),
        "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
        "accuracy": accuracy_score(y, pred),
        "precision": precision_score(y, pred, zero_division=0),
        "recall_sensitivity": recall_score(y, pred, zero_division=0),
        "specificity": spec,
        "f1": f1_score(y, pred, zero_division=0),
        "balanced_accuracy": balanced_accuracy_score(y, pred),
        "mcc": matthews_corrcoef(y, pred) if len(set(y)) > 1 else float("nan"),
        "roc_auc": roc_auc_score(y, prob) if len(set(y)) > 1 else float("nan"),
        "pr_auc": average_precision_score(y, prob) if len(set(y)) > 1 else float("nan"),
    }


def _auc_fast(y, prob):
    """Mann-Whitney U form of ROC-AUC, with mid-ranks for ties. Identical to
    sklearn.metrics.roc_auc_score but without the per-call validation overhead
    (this runs 2000x per model/split, where sklearn's overhead dominates)."""
    order = np.argsort(prob, kind="mergesort")
    ranks = np.empty(len(prob), dtype=np.float64)
    sp = prob[order]
    i = 0
    while i < len(sp):
        j = i
        while j + 1 < len(sp) and sp[j + 1] == sp[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    n_pos = int(y.sum())
    n_neg = len(y) - n_pos
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    return (ranks[y == 1].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


def bootstrap_ci(y, prob, key, n_boot=N_BOOT, seed=SEED):
    """Percentile bootstrap over test-set resamples. Matches
    modeling/metrics.py's protocol (same seed, resample-with-replacement,
    2.5/97.5 percentiles); only the inner metric computation is vectorised."""
    rng = np.random.RandomState(seed)
    n = len(y)
    idx = rng.randint(0, n, size=(n_boot, n))
    yb = y[idx]
    pb = prob[idx]
    if key == "accuracy":
        vals = ((pb >= 0.5).astype(int) == yb).mean(axis=1)
    elif key == "roc_auc":
        vals = np.array([_auc_fast(yb[i], pb[i]) for i in range(n_boot)])
        vals = vals[~np.isnan(vals)]
    else:
        raise ValueError(key)
    if not len(vals):
        return float("nan"), float("nan")
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def write_csv(name, rows):
    if not rows:
        return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    p = OUT / name
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {p.relative_to(ROOT)}  ({len(rows)} rows)")


# ---------------------------------------------------------------- table 1
# Full in-distribution performance, Split A and Split B test partitions.
perf_rows = []
curve_data = {}
for model, tag, label in MODELS:
    for split in ("split_a", "split_b"):
        ids, y, prob = read_predictions(model, split)
        m = all_metrics(y, prob)
        lo, hi = bootstrap_ci(y, prob, "accuracy")
        auc_lo, auc_hi = bootstrap_ci(y, prob, "roc_auc")
        perf_rows.append({
            "model": tag, "model_full": label,
            "split": "A (naive)" if split == "split_a" else "B (product-grouped)",
            **m,
            "accuracy_ci_lo": lo, "accuracy_ci_hi": hi,
            "roc_auc_ci_lo": auc_lo, "roc_auc_ci_hi": auc_hi,
        })
        fpr, tpr, _ = roc_curve(y, prob)
        pr, rc, _ = precision_recall_curve(y, prob)
        curve_data[f"{tag}__{split}"] = {
            "fpr": fpr.tolist(), "tpr": tpr.tolist(),
            "precision": pr.tolist(), "recall": rc.tolist(),
            "y_true": y.tolist(), "y_prob": prob.tolist(),
            "roc_auc": m["roc_auc"], "pr_auc": m["pr_auc"],
            "label": label,
        }
write_csv("table_performance_full.csv", perf_rows)
(OUT / "curve_data.json").write_text(json.dumps(curve_data), encoding="utf-8")
print(f"wrote {(OUT / 'curve_data.json').relative_to(ROOT)}")


# ---------------------------------------------------------------- table 2
# Leakage-quantification table, recomputed from the CURRENT predictions so it
# matches the production (3-way-normalised) pipeline. The committed
# modeling/results/leakage_table.csv predates that retrain for Models 2-4.
cv_rows = {}
for model, tag, label in MODELS:
    with open(RES / f"metrics_{model}.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["run"] == "split_b_5foldcv":
                cv_rows[tag] = r

leak_rows = []
for model, tag, label in MODELS:
    a = next(r for r in perf_rows if r["model"] == tag and r["split"].startswith("A"))
    b = next(r for r in perf_rows if r["model"] == tag and r["split"].startswith("B"))
    cv = cv_rows[tag]
    leak_rows.append({
        "model": tag, "model_full": label,
        "split_a_acc": a["accuracy"],
        "split_a_ci": f"[{a['accuracy_ci_lo']:.3f}, {a['accuracy_ci_hi']:.3f}]",
        "split_b_acc": b["accuracy"],
        "split_b_ci": f"[{b['accuracy_ci_lo']:.3f}, {b['accuracy_ci_hi']:.3f}]",
        "split_b_cv_mean": float(cv["accuracy_mean"]),
        "split_b_cv_std": float(cv["accuracy_std"]),
        "delta_a_minus_b": a["accuracy"] - b["accuracy"],
        "split_a_auc": a["roc_auc"], "split_b_auc": b["roc_auc"],
    })
write_csv("table_leakage.csv", leak_rows)


# ---------------------------------------------------------------- table 3
# Pairwise McNemar's tests on Split B test predictions (recomputed).
import sys
sys.path.insert(0, str(ROOT / "modeling"))
from metrics import mcnemar_test  # noqa: E402

pred_b = {}
for model, tag, _ in MODELS:
    ids, y, prob = read_predictions(model, "split_b")
    pred_b[tag] = {"ids": ids, "y": y, "pred": (prob >= 0.5).astype(int)}

mc_rows = []
tags = [t for _, t, _ in MODELS]
for i in range(len(tags)):
    for j in range(i + 1, len(tags)):
        a, b = pred_b[tags[i]], pred_b[tags[j]]
        if a["ids"] != b["ids"]:
            lut = dict(zip(b["ids"], b["pred"]))
            pb = np.array([lut[k] for k in a["ids"]])
        else:
            pb = b["pred"]
        stat, p = mcnemar_test(a["y"], a["pred"], pb)
        n01 = int(((a["pred"] == a["y"]) & (pb != a["y"])).sum())
        n10 = int(((a["pred"] != a["y"]) & (pb == a["y"])).sum())
        mc_rows.append({"model_a": tags[i], "model_b": tags[j],
                        "n01_a_right_b_wrong": n01, "n10_a_wrong_b_right": n10,
                        "n_discordant": n01 + n10, "statistic": stat,
                        "p_value": p, "significant_005": p < 0.05})
write_csv("table_mcnemar.csv", mc_rows)


# ---------------------------------------------------------------- table 4
# External generalisation: authentic-only Split C (real photographs).
with open(RES / "split_c_eval.csv", newline="", encoding="utf-8") as f:
    sc = {r["model"]: r for r in csv.DictReader(f)}
sc_rows = []
for model, tag, label in MODELS:
    r = sc[model]
    sc_rows.append({
        "model": tag, "model_full": label,
        "split_c_authentic_acc": float(r["split_c_authentic_acc"]),
        "split_c_n": int(r["split_c_n"]),
        "split_b_authentic_acc": float(r["split_b_test_authentic_acc"]),
        "split_b_authentic_n": int(r["split_b_test_n"]),
        "gap": float(r["gap"]),
    })
write_csv("table_split_c_authentic.csv", sc_rows)


# ---------------------------------------------------------------- table 5
# Synthetic counterfeit-proxy Split C: reconstruct the confusion matrix
# exactly from reported acc/precision/recall on a known 150/150 balance,
# then derive specificity / balanced accuracy / MCC. Verified for integer
# consistency; the script fails loudly rather than rounding silently.
with open(RES / "split_c_synthetic_eval.csv", newline="", encoding="utf-8") as f:
    syn = {r["model"]: r for r in csv.DictReader(f)}

N_POS = N_NEG = 150
syn_rows = []
for model, tag, label in MODELS:
    r = syn[model]
    acc, prec, rec = float(r["accuracy"]), float(r["precision"]), float(r["recall"])
    tp = rec * N_POS
    fp = tp / prec - tp if prec > 0 else 0.0
    fn, tn = N_POS - tp, N_NEG - fp
    ints = [round(v) for v in (tp, fp, fn, tn)]
    for v, iv in zip((tp, fp, fn, tn), ints):
        assert abs(v - iv) < 1e-6, f"{tag}: non-integer confusion cell {v}"
    tp, fp, fn, tn = ints
    assert abs((tp + tn) / (N_POS + N_NEG) - acc) < 1e-9, f"{tag}: accuracy mismatch"
    spec = tn / (tn + fp) if (tn + fp) else float("nan")
    denom = np.sqrt(float(tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = ((tp * tn - fp * fn) / denom) if denom > 0 else 0.0
    syn_rows.append({
        "model": tag, "model_full": label, "n": int(r["n"]),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "accuracy": acc, "precision": prec, "recall_sensitivity": rec,
        "specificity": spec, "f1": float(r["f1"]),
        "balanced_accuracy": (rec + spec) / 2, "mcc": mcc,
        "roc_auc": float(r["roc_auc"]),
        "pr_auc": "not available (per-image scores not persisted)",
    })
write_csv("table_split_c_synthetic.csv", syn_rows)


# ---------------------------------------------------------------- table 6
# Normalisation ablation, assembled from the committed experiment CSVs.
def read_exp(name):
    with open(RES / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

abl_rows = []
for r in read_exp("resolution_norm_experiment.csv"):
    abl_rows.append({"source": "resolution_norm_experiment.csv", "model": "M4",
                     "condition": r["condition"],
                     "resolution": r["resolution_normalized"],
                     "brightness": r["brightness_normalized"],
                     "compression": "False", "colour_balance": "False",
                     "split_b_acc": float(r["split_b_test_acc"]),
                     "split_c_acc": float(r["split_c_acc"])})
for r in read_exp("colorbalance_norm_experiment.csv"):
    abl_rows.append({"source": "colorbalance_norm_experiment.csv", "model": "M4",
                     "condition": r["condition"],
                     "resolution": r["resolution_normalized"],
                     "brightness": r["brightness_normalized"],
                     "compression": "False",
                     "colour_balance": r["color_balance_normalized"],
                     "split_b_acc": float(r["split_b_test_acc"]),
                     "split_c_acc": float(r["split_c_acc"])})
for r in read_exp("compression_norm_experiment.csv"):
    abl_rows.append({"source": "compression_norm_experiment.csv", "model": "M4",
                     "condition": r["condition"],
                     "resolution": r["resolution_normalized"],
                     "brightness": r["brightness_normalized"],
                     "compression": r["compression_normalized"],
                     "colour_balance": "False",
                     "split_b_acc": float(r["split_b_test_acc"]),
                     "split_c_acc": float(r["split_c_acc"])})
for r in read_exp("model3_decompose_experiment.csv"):
    abl_rows.append({"source": "model3_decompose_experiment.csv", "model": "M3",
                     "condition": r["condition"],
                     "resolution": r["resolution_normalized"],
                     "brightness": r["brightness_normalized"],
                     "compression": "False", "colour_balance": "False",
                     "split_b_acc": float(r["split_b_test_acc"]),
                     "split_c_acc": float(r["split_c_acc"])})
write_csv("table_ablation_axes.csv", abl_rows)

tag_of = {"model1_classical": "M1", "model2_smallcnn": "M2",
          "model3_mobilenet": "M3", "model4_efficientnet": "M4"}
cross_rows = []
for fname, cond_label in (("normalization_all_models_experiment.csv", "2-way (res+bright)"),
                          ("compression_all_models_experiment.csv", "3-way (res+bright+comp)")):
    rows = read_exp(fname)
    by_model = {}
    for r in rows:
        by_model.setdefault(r["model"], {})[r["condition"]] = r
    for m, conds in by_model.items():
        base = next((v for k, v in conds.items() if k == "baseline"), None)
        norm = next((v for k, v in conds.items() if k != "baseline"), None)
        if not base or not norm:
            continue
        cross_rows.append({
            "experiment": cond_label, "source": fname, "model": tag_of[m],
            "baseline_split_b": float(base["split_b_test_acc"]),
            "baseline_split_c": float(base["split_c_acc"]),
            "normalised_split_b": float(norm["split_b_test_acc"]),
            "normalised_split_c": float(norm["split_c_acc"]),
            "delta_split_c": float(norm["split_c_acc"]) - float(base["split_c_acc"]),
        })

# M4's 3-way row lives in compression_norm_experiment.csv (the single-model
# experiment that introduced the axis), not in compression_all_models_*.csv,
# which only covers M1-M3. Both its baseline and its 3-way condition come from
# the SAME script execution, so the within-run comparison is valid.
_c = {r["condition"]: r for r in read_exp("compression_norm_experiment.csv")}
cross_rows.append({
    "experiment": "3-way (res+bright+comp)", "source": "compression_norm_experiment.csv",
    "model": "M4",
    "baseline_split_b": float(_c["baseline_no_norm_rerun"]["split_b_test_acc"]),
    "baseline_split_c": float(_c["baseline_no_norm_rerun"]["split_c_acc"]),
    "normalised_split_b": float(_c["all_three_combined"]["split_b_test_acc"]),
    "normalised_split_c": float(_c["all_three_combined"]["split_c_acc"]),
    "delta_split_c": float(_c["all_three_combined"]["split_c_acc"])
                     - float(_c["baseline_no_norm_rerun"]["split_c_acc"]),
})
write_csv("table_ablation_all_models.csv", cross_rows)


# ---------------------------------------------------------------- table 7
# Training curves: epochs run / best epoch, per model, per split.
curve_rows = []
for model, tag, label in MODELS:
    if tag == "M1":
        continue  # closed-form LogReg fit, no epochs
    for run, run_label in (("split_a", "A (naive)"), ("split_b_final", "B (product-grouped)")):
        p = RES / "curves" / f"{model}__{run}.csv"
        if not p.exists():
            continue
        with open(p, newline="", encoding="utf-8") as f:
            hist = list(csv.DictReader(f))
        best = min(hist, key=lambda r: float(r["val_loss"]))
        curve_rows.append({
            "model": tag, "split": run_label, "epochs_run": len(hist),
            "best_epoch": int(best["epoch"]),
            "best_val_loss": float(best["val_loss"]),
            "best_val_acc": float(best["val_acc"]),
            "final_train_loss": float(hist[-1]["train_loss"]),
            "final_train_acc": float(hist[-1]["train_acc"]),
        })
write_csv("table_training_curves.csv", curve_rows)


# ---------------------------------------------------------------- table 8
# Error analysis, recomputed from the CURRENT predictions. The committed
# modeling/results/error_analysis.csv predates the normalised retrain for
# Models 2-4, so its per-model error counts no longer match the models of
# record; the qualitative per-image review it documents was done on that
# earlier run and is cited as such in the manuscript.
err_rows = []
per_image = {}
for model, tag, label in MODELS:
    n_err = 0
    n_tot = 0
    for split in ("split_a", "split_b"):
        ids, y, prob = read_predictions(model, split)
        pred = (prob >= 0.5).astype(int)
        for i, yt, yp in zip(ids, y, pred):
            n_tot += 1
            if yt != yp:
                n_err += 1
                per_image.setdefault(i, []).append(f"{tag}/{split[-1].upper()}")
    err_rows.append({"model": tag, "model_full": label, "predictions": n_tot,
                     "errors": n_err, "error_rate": n_err / n_tot})
err_rows.append({
    "model": "ALL", "model_full": "pooled across 4 models x 2 splits",
    "predictions": sum(r["predictions"] for r in err_rows),
    "errors": sum(r["errors"] for r in err_rows),
    "error_rate": sum(r["errors"] for r in err_rows) / sum(r["predictions"] for r in err_rows),
})
write_csv("table_error_analysis.csv", err_rows)

consensus = sorted(((k, v) for k, v in per_image.items() if len(v) >= 3),
                   key=lambda kv: -len(kv[1]))
write_csv("table_error_consensus.csv",
          [{"image_id": k, "n_model_split_combinations_wrong": len(v),
            "wrong_in": " ".join(sorted(v))} for k, v in consensus])
print(f"  distinct images with >=1 error: {len(per_image)}; "
      f"wrong in >=3 model/split combinations: {len(consensus)}")
print("\ndone")

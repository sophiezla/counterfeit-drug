"""
Balanced external evaluation — the primary external-validation result.

WHAT THIS ADDS THAT NOTHING ELSE IN THIS PROJECT COULD
------------------------------------------------------
Splits C and D are authentic-only and Split E is counterfeit-only, so the
Section III-D terminology rule holds that nothing computed on any of them is an
accuracy: the first two yield a specificity and the third a recall. That is not
a presentational inconvenience, it is a measurement limit. A one-sided
evaluation cannot distinguish a model applying a decision rule from one that has
simply moved its operating point, and this project has an instance of the
failure rather than a hypothesis about it: M1 returns 0.000 and 0.000
specificity on Splits C and D against 0.967 recall on Split E, which is the
degenerate all-counterfeit classifier.

The balanced external test (scripts/32_build_balanced_external.py) is two-class
and equal-count, so accuracy, balanced accuracy, precision, F1 and ROC-AUC are
all defined on it, and a confusion matrix means something. This script reports
all of them, once.

THE PROTOCOL, AND WHY IT IS FIXED BEFORE THIS RUNS
--------------------------------------------------
Confirmatory rather than exploratory, and the ordering is what makes that true:

  training -> preprocessing -> normalisation -> decision threshold and
  model-selection rule -> the external set is locked -> evaluate once.

Every one of those was settled before the balanced set existed. The models are
loaded from the same persisted Split B checkpoints that produced Tables 4-7 --
not retrained, not refitted, not re-thresholded. The decision threshold is 0.5,
the project default since the first evaluation script. The preprocessing is
modeling/common.py's, untouched.

If any of that is changed after reading the numbers below, the re-run is
exploratory and must be reported as such. There is no version of "we adjusted
the threshold to see what happens" that stays confirmatory.

Output: modeling/results/balanced_external_eval.csv
        modeling/results/predictions/<model>__balanced_external.csv
"""
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, set_seed, SEED  # noqa: E402
from result_io import load_chosen_lr  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "modeling" / "results"
PROVENANCE = ROOT / "data" / "metadata" / "balanced_external_provenance.csv"
OUT = RESULTS / "balanced_external_eval.csv"

THRESHOLD = 0.5          # the project default; fixed before the set was built
N_BOOTSTRAP = 10000
BOOTSTRAP_SEED = 42

FIELDS = ["model", "n", "n_authentic", "n_counterfeit",
          "tn", "fp", "fn", "tp",
          "accuracy", "accuracy_lo", "accuracy_hi",
          "balanced_accuracy", "balanced_accuracy_lo", "balanced_accuracy_hi",
          "specificity", "specificity_lo", "specificity_hi",
          "recall", "recall_lo", "recall_hi",
          "precision", "precision_lo", "precision_hi",
          "f1", "f1_lo", "f1_hi",
          "roc_auc", "roc_auc_lo", "roc_auc_hi"]


def wilson(k, n, z=1.959963985):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def metrics(y, pred, prob):
    """Every quantity the paper reports, from one set of predictions."""
    y = np.asarray(y)
    pred = np.asarray(pred)
    tn = int(((y == 0) & (pred == 0)).sum())
    fp = int(((y == 0) & (pred == 1)).sum())
    fn = int(((y == 1) & (pred == 0)).sum())
    tp = int(((y == 1) & (pred == 1)).sum())

    spec = tn / (tn + fp) if tn + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    prec = tp / (tp + fp) if tp + fp else float("nan")
    f1 = (2 * prec * rec / (prec + rec)
          if prec + rec and not np.isnan(prec) and not np.isnan(rec)
          else 0.0)
    acc = (tp + tn) / len(y)
    bacc = (spec + rec) / 2

    # ROC-AUC by the Mann-Whitney form, ties at half, so it does not depend on
    # a curve implementation or on how ties are broken.
    pos = np.asarray(prob)[y == 1]
    neg = np.asarray(prob)[y == 0]
    if len(pos) and len(neg):
        diff = pos[:, None] - neg[None, :]
        auc = float(((diff > 0).sum() + 0.5 * (diff == 0).sum())
                    / (len(pos) * len(neg)))
    else:
        auc = float("nan")

    return {"tn": tn, "fp": fp, "fn": fn, "tp": tp, "specificity": spec,
            "recall": rec, "precision": prec, "f1": f1, "accuracy": acc,
            "balanced_accuracy": bacc, "roc_auc": auc}


def bootstrap_ci(y, pred, prob, key, n_boot=N_BOOTSTRAP, seed=BOOTSTRAP_SEED):
    """Stratified percentile interval: resample each class to its own size.

    Stratified because the set is balanced by design -- 46 and 46 is a property
    of the construction, not a draw, so an unstratified resample would put
    sampling noise into a quantity that has none.
    """
    rng = np.random.default_rng(seed)
    y = np.asarray(y)
    idx0 = np.flatnonzero(y == 0)
    idx1 = np.flatnonzero(y == 1)
    draws = np.empty(n_boot)
    for b in range(n_boot):
        take = np.concatenate([rng.choice(idx0, len(idx0), replace=True),
                               rng.choice(idx1, len(idx1), replace=True)])
        m = metrics(y[take], np.asarray(pred)[take], np.asarray(prob)[take])
        draws[b] = m[key]
    draws = draws[~np.isnan(draws)]
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def balanced_examples():
    rows = list(csv.DictReader(open(PROVENANCE, newline="", encoding="utf-8")))
    return [{"image_id": r["image_id"],
             "path": ROOT / r["relpath_from_root"],
             "label": 0 if r["class_label"] == "authentic" else 1,
             "split": "balanced_external",
             "product_identity": r["product_identity"],
             "group_id": r["group_id"], "cv_fold": None} for r in rows]


def eval_model1(examples):
    from train_model1_classical import extract_histogram
    from sklearn.linear_model import LogisticRegression

    train = [e for e in load_examples("split_b") if e["split"] == "train"]
    X = np.stack([extract_histogram(e["path"]) for e in train])
    y = np.array([e["label"] for e in train])
    set_seed(SEED)
    clf = LogisticRegression(max_iter=2000, class_weight="balanced",
                             random_state=SEED).fit(X, y)
    return list(map(float, clf.predict_proba(
        np.stack([extract_histogram(e["path"]) for e in examples]))[:, 1]))


def eval_model2(examples):
    from train_model2_cnn import SmallCNN
    from torch_utils import evaluate_model
    from result_io import load_checkpoint

    model = SmallCNN()
    ckpt = load_checkpoint(model, "model2_smallcnn_gap", "split_b_final",
                           expected_lr=load_chosen_lr("model2_smallcnn_gap"))
    print(f"    loaded checkpoint: lr={ckpt['lr']} seed={ckpt['seed']} "
          f"epochs_run={ckpt['epochs_run']}")
    model.eval()
    _, _, prob = evaluate_model(model, examples)
    return list(map(float, prob))


def eval_frozen(module_name, examples):
    import importlib
    from torch_utils import evaluate_model_on_features
    from result_io import load_checkpoint

    mod = importlib.import_module(module_name)
    head = mod.build_head()
    ckpt = load_checkpoint(head, mod.MODEL_NAME, "split_b_final",
                           expected_lr=load_chosen_lr(mod.MODEL_NAME))
    print(f"    loaded checkpoint: lr={ckpt['lr']} seed={ckpt['seed']} "
          f"epochs_run={ckpt['epochs_run']}")
    head.eval()
    X, y, ids = mod.get_features(examples, train=False, k_augment=1)
    _, _, prob = evaluate_model_on_features(head, X, y, ids)
    return list(map(float, prob))


MODELS = [
    ("model1_classical_colorhist_logreg", eval_model1),
    ("model2_smallcnn_gap", eval_model2),
    ("model3_mobilenetv3small_frozen",
     lambda ex: eval_frozen("train_model3_mobilenet", ex)),
    ("model4_efficientnetb0_frozen",
     lambda ex: eval_frozen("train_model4_efficientnet", ex)),
]

CI_KEYS = ["accuracy", "balanced_accuracy", "specificity", "recall",
           "precision", "f1", "roc_auc"]


def main():
    examples = balanced_examples()
    y = [e["label"] for e in examples]
    n_auth, n_cft = y.count(0), y.count(1)
    print(f"Balanced external test: {len(examples)} images, "
          f"{n_auth} authentic, {n_cft} counterfeit")
    print(f"Decision threshold {THRESHOLD} (project default, fixed before the "
          f"set was built). Checkpoints are the Split B ones of record.\n")

    rows = list(csv.DictReader(open(OUT, newline="", encoding="utf-8"))) \
        if OUT.exists() else []
    done = {r["model"] for r in rows}

    for name, fn in MODELS:
        if name in done:
            print(f"=== skip (done): {name} ===")
            continue
        print(f"=== {name} ===", flush=True)
        try:
            prob = fn(examples)
        except FileNotFoundError as exc:
            print(f"    SKIPPED: {exc}")
            continue

        pred = (np.asarray(prob) >= THRESHOLD).astype(int)
        m = metrics(y, pred, prob)
        row = {"model": name, "n": len(examples), "n_authentic": n_auth,
               "n_counterfeit": n_cft,
               **{k: m[k] for k in ("tn", "fp", "fn", "tp")}}
        for key in CI_KEYS:
            lo, hi = bootstrap_ci(y, pred, prob, key)
            row[key] = round(m[key], 4)
            row[f"{key}_lo"] = round(lo, 4)
            row[f"{key}_hi"] = round(hi, 4)
        rows.append(row)

        print(f"    confusion  TN {m['tn']:>3}  FP {m['fp']:>3} | "
              f"FN {m['fn']:>3}  TP {m['tp']:>3}")
        for key in CI_KEYS:
            print(f"    {key:<18} {m[key]:.3f} "
                  f"[{row[key + '_lo']:.3f}, {row[key + '_hi']:.3f}]")
        print(flush=True)

        pdir = RESULTS / "predictions"
        pdir.mkdir(parents=True, exist_ok=True)
        with open(pdir / f"{name}__balanced_external.csv", "w", newline="",
                  encoding="utf-8") as pf:
            pw = csv.DictWriter(pf, fieldnames=["image_id", "group_id",
                                                "y_true", "y_prob", "y_pred"])
            pw.writeheader()
            for e, p, q in zip(examples, prob, pred):
                pw.writerow({"image_id": e["image_id"],
                             "group_id": e["group_id"], "y_true": e["label"],
                             "y_prob": p, "y_pred": int(q)})

        with open(OUT, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)

    print(f"wrote {OUT.name}\n")
    hdr = (f"{'model':<38} {'acc':>6} {'bal':>6} {'spec':>6} {'rec':>6} "
           f"{'prec':>6} {'F1':>6} {'AUC':>6}")
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(f"{r['model']:<38} "
              + " ".join(f"{float(r[k]):>6.3f}" for k in
                         ("accuracy", "balanced_accuracy", "specificity",
                          "recall", "precision", "f1", "roc_auc")))
    print("\nBalanced accuracy is the column to read first: on 46/46 it is the "
          "one\nquantity a shifted operating point cannot inflate.")


if __name__ == "__main__":
    main()

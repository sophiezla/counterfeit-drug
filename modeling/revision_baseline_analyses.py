"""
Baseline-model evaluations and cluster-aware intervals for the J. Imaging revision.

Why this exists. The pipeline of record trains M2-M4 WITH the exploratory
provenance normalization (common.py normalize=True), so the internal table and
the balanced external test in earlier drafts reported the normalized models,
while the acquisition-shift headline (0/150, 100/150, 9/150) came from the
un-normalized baseline. This script puts every primary result on the baseline
models, which were planned before the external failure was seen, and keeps the
normalized models as a separate, exploratory condition.

Stages (each resumable; outputs are written as they finish):

  score    load the persisted seed-42 BASELINE checkpoints written by
           seed_sweep.py (run tag "seed42_baseline", Split B training
           partition, normalize=False) and score them on the Split B test
           partition, conditions C and D, and the balanced external set.
           No training. Condition C/D counts must reproduce seed_sweep.csv.
  splita   retrain M2-M4 on the Split A partition at seed 42 with
           normalize=False (the Split A baseline had never been run), and
           score the Split A test partition.
  stats    recompute every interval from the per-image prediction files
           with one procedure: 10,000 percentile-bootstrap resamples,
           stratified by class; on the internal test partitions, resampling
           near-duplicate groups; on the balanced set, resampling images and,
           as a sensitivity analysis, resampling the 29 authentic query-term
           clusters (each counterfeit frame is its own regulatory alert).

    python modeling/revision_baseline_analyses.py score
    python modeling/revision_baseline_analyses.py splita
    python modeling/revision_baseline_analyses.py stats

Outputs: modeling/results/predictions/<model>__baseline_seed42__<set>.csv
         modeling/results/revision_internal.csv
         modeling/results/revision_balanced_external.csv
         modeling/results/revision_external_specificity.csv
"""
import csv
import importlib
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "modeling" / "results"
PRED = RESULTS / "predictions"
BALANCED_PROV = ROOT / "data" / "metadata" / "balanced_external_provenance.csv"

N_BOOT = 10000
BOOT_SEED = 42
THRESHOLD = 0.5

FROZEN = {"model3_mobilenetv3small_frozen": "train_model3_mobilenet",
          "model4_efficientnetb0_frozen": "train_model4_efficientnet"}
M2 = "model2_smallcnn_gap"
MODELS = [M2, *FROZEN]
M1 = "model1_classical_colorhist_logreg"
DISPLAY = {M1: "M1 hist+LR", M2: "M2 CNN",
           "model3_mobilenetv3small_frozen": "M3 MobileNetV3",
           "model4_efficientnetb0_frozen": "M4 EfficientNet-B0"}


# ------------------------------------------------------------------ io

def write_pred(path, ids, y, p):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image_id", "y_true", "y_prob"])
        for i, t, q in zip(ids, y, p):
            w.writerow([i, int(t), float(q)])


def read_pred(path):
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8")))
    return ([r["image_id"] for r in rows],
            np.array([int(float(r["y_true"])) for r in rows]),
            np.array([float(r["y_prob"]) for r in rows]))


def balanced_examples():
    rows = list(csv.DictReader(open(BALANCED_PROV, newline="", encoding="utf-8")))
    return [{"image_id": r["image_id"], "path": ROOT / r["relpath_from_root"],
             "label": 0 if r["class_label"] == "authentic" else 1,
             "split": "balanced_external", "product_identity": r["product_identity"],
             "cv_fold": None} for r in rows]


def eval_sets():
    from common import load_examples
    from eval_external_from_checkpoints import split_c_examples, split_d_examples
    b = [e for e in load_examples("split_b") if e["split"] == "test"]
    return {"split_b_test": b, "split_c": split_c_examples(),
            "split_d": split_d_examples(), "balanced_external": balanced_examples()}


# ------------------------------------------------------------- stage: score

def stage_score():
    from result_io import load_checkpoint, load_chosen_lr
    from torch_utils import evaluate_model, evaluate_model_on_features
    from feature_cache import extract_features

    sets = eval_sets()
    for name in MODELS:
        if name == M2:
            from train_model2_cnn import SmallCNN
            model = SmallCNN()
            ck = load_checkpoint(model, name, "seed42_baseline",
                                 expected_lr=load_chosen_lr(name))
            print(f"{name}: seed={ck['seed']} lr={ck['lr']} epochs={ck['epochs_run']}")
            for s, ex in sets.items():
                ids, y, p = evaluate_model(model, ex, normalize=False)
                write_pred(PRED / f"{name}__baseline_seed42__{s}.csv", ids, y, p)
                report(name, s, y, p)
        else:
            mod = importlib.import_module(FROZEN[name])
            head = mod.build_head()
            ck = load_checkpoint(head, name, "seed42_baseline",
                                 expected_lr=load_chosen_lr(name))
            print(f"{name}: seed={ck['seed']} lr={ck['lr']} epochs={ck['epochs_run']}")
            fe, gap = mod.build_backbone()
            for s, ex in sets.items():
                X, y, ids = extract_features(fe, gap, ex, train=False, k_augment=1,
                                             normalize=False)
                ids, y, p = evaluate_model_on_features(head, X, y, ids)
                write_pred(PRED / f"{name}__baseline_seed42__{s}.csv", ids, y, p)
                report(name, s, y, p)


def report(name, s, y, p):
    y = np.asarray(y); pred = (np.asarray(p) >= THRESHOLD).astype(int)
    print(f"  {s:<18} n={len(y):>3}  acc={np.mean(pred == y):.4f}  "
          f"auth correct={int(((y == 0) & (pred == 0)).sum())}/{int((y == 0).sum())}  "
          f"cft correct={int(((y == 1) & (pred == 1)).sum())}/{int((y == 1).sum())}",
          flush=True)


# ------------------------------------------------------------ stage: splita

def stage_splita():
    from common import load_examples, set_seed, SEED
    from result_io import load_chosen_lr
    from torch_utils import (train_model, evaluate_model,
                             train_model_on_features, evaluate_model_on_features)
    from feature_cache import extract_features, K_AUGMENT

    ex = load_examples("split_a")
    by = {s: [e for e in ex if e["split"] == s] for s in ("train", "val", "test")}
    for name in MODELS:
        out = PRED / f"{name}__baseline_seed42__split_a_test.csv"
        if out.exists():
            print(f"skip (done): {name}")
            continue
        print(f"=== {name}: Split A, baseline, seed {SEED} ===", flush=True)
        if name == M2:
            from train_model2_cnn import SmallCNN
            set_seed(SEED)
            model, hist = train_model(SmallCNN(), by["train"], by["val"],
                                      load_chosen_lr(name), model_tag=name,
                                      run_tag="split_a_baseline_seed42",
                                      normalize=False)
            ids, y, p = evaluate_model(model, by["test"], normalize=False)
        else:
            mod = importlib.import_module(FROZEN[name])
            fe, gap = mod.build_backbone()
            f = lambda e, tr, k: extract_features(fe, gap, e, train=tr,
                                                  k_augment=k, normalize=False)
            X_tr, y_tr, _ = f(by["train"], True, K_AUGMENT)
            X_va, y_va, _ = f(by["val"], False, 1)
            X_te, y_te, id_te = f(by["test"], False, 1)
            set_seed(SEED)
            head, hist = train_model_on_features(
                mod.build_head(), X_tr, y_tr, X_va, y_va, load_chosen_lr(name),
                model_tag=name, run_tag="split_a_baseline_seed42")
            ids, y, p = evaluate_model_on_features(head, X_te, y_te, id_te)
        print(f"  epochs run: {len(hist)}")
        write_pred(out, ids, y, p)
        report(name, "split_a_test", y, p)


# ------------------------------------------------------------- stage: stats

def point(y, p):
    y = np.asarray(y); p = np.asarray(p); pred = (p >= THRESHOLD).astype(int)
    tn = int(((y == 0) & (pred == 0)).sum()); fp = int(((y == 0) & (pred == 1)).sum())
    fn = int(((y == 1) & (pred == 0)).sum()); tp = int(((y == 1) & (pred == 1)).sum())
    spec = tn / (tn + fp) if tn + fp else np.nan
    rec = tp / (tp + fn) if tp + fn else np.nan
    prec = tp / (tp + fp) if tp + fp else np.nan
    f1 = 2 * prec * rec / (prec + rec) if (tp and prec + rec) else 0.0
    pos, neg = p[y == 1], p[y == 0]
    if len(pos) and len(neg):
        d = pos[:, None] - neg[None, :]
        auc = float(((d > 0).sum() + 0.5 * (d == 0).sum()) / d.size)
    else:
        auc = np.nan
    return {"tn": tn, "fp": fp, "fn": fn, "tp": tp, "accuracy": (tp + tn) / len(y),
            "balanced_accuracy": (spec + rec) / 2, "specificity": spec,
            "recall": rec, "precision": prec, "f1": f1, "roc_auc": auc}


KEYS = ["accuracy", "balanced_accuracy", "specificity", "recall", "precision",
        "f1", "roc_auc"]


def cluster_boot(y, p, clusters, n_boot=N_BOOT, seed=BOOT_SEED):
    """Percentile bootstrap, stratified by class, resampling whole clusters."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y); p = np.asarray(p); clusters = np.asarray(clusters)
    strata = []
    for c in (0, 1):
        idx = np.flatnonzero(y == c)
        groups = {}
        for i in idx:
            groups.setdefault(clusters[i], []).append(i)
        strata.append(list(groups.values()))
    draws = {k: [] for k in KEYS}
    for _ in range(n_boot):
        take = []
        for groups in strata:
            pick = rng.integers(0, len(groups), len(groups))
            for g in pick:
                take.extend(groups[g])
        m = point(y[take], p[take])
        for k in KEYS:
            draws[k].append(m[k])
    return {k: (float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5)))
            for k, v in draws.items()}


def wilson(k, n, z=1.959963985):
    ph = k / n; d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def groups_for(split):
    from common import load_examples
    return {e["image_id"]: e["product_identity"] for e in load_examples(split)}


def stage_stats():
    # ---- internal: M1 (never normalized), M2-M4 baseline and normalized
    ga, gb = groups_for("split_a"), groups_for("split_b")
    files = []
    for name in [M1] + MODELS:
        if name == M1:
            files.append((name, "baseline", "A", PRED / f"{M1}__split_a.csv"))
            files.append((name, "baseline", "B", PRED / f"{M1}__split_b.csv"))
        else:
            files.append((name, "baseline", "A", PRED / f"{name}__baseline_seed42__split_a_test.csv"))
            files.append((name, "baseline", "B", PRED / f"{name}__baseline_seed42__split_b_test.csv"))
            files.append((name, "normalized", "A", PRED / f"{name}__split_a.csv"))
            files.append((name, "normalized", "B", PRED / f"{name}__split_b.csv"))
    rows = []
    for name, cond, split, path in files:
        if not path.exists():
            print(f"missing {path.name}")
            continue
        ids, y, p = read_pred(path)
        g = ga if split == "A" else gb
        m = point(y, p)
        ci = cluster_boot(y, p, [g[i] for i in ids])
        rows.append({"model": DISPLAY[name], "condition": cond, "split": split,
                     "n": len(y), "n_groups": len({g[i] for i in ids}),
                     **{k: m[k] for k in ("tn", "fp", "fn", "tp")},
                     **{k: round(m[k], 4) for k in KEYS},
                     **{f"{k}_lo": round(ci[k][0], 4) for k in KEYS},
                     **{f"{k}_hi": round(ci[k][1], 4) for k in KEYS}})
    dump(RESULTS / "revision_internal.csv", rows)

    # ---- balanced external: image-level and query-term-cluster intervals
    prov = {r["image_id"]: r for r in csv.DictReader(open(BALANCED_PROV, newline="", encoding="utf-8"))}
    rows = []
    for name in [M1] + MODELS:
        paths = ([("baseline", PRED / f"{M1}__balanced_external.csv")] if name == M1 else
                 [("baseline", PRED / f"{name}__baseline_seed42__balanced_external.csv"),
                  ("normalized", PRED / f"{name}__balanced_external.csv")])
        for cond, path in paths:
            if not path.exists():
                print(f"missing {path.name}")
                continue
            ids, y, p = read_pred(path)
            m = point(y, p)
            ci_img = cluster_boot(y, p, ids)
            ci_clu = cluster_boot(y, p, [prov[i]["product_identity"] for i in ids])
            rows.append({"model": DISPLAY[name], "condition": cond, "n": len(y),
                         **{k: m[k] for k in ("tn", "fp", "fn", "tp")},
                         **{k: round(m[k], 4) for k in KEYS},
                         **{f"{k}_img_lo": round(ci_img[k][0], 4) for k in KEYS},
                         **{f"{k}_img_hi": round(ci_img[k][1], 4) for k in KEYS},
                         **{f"{k}_clu_lo": round(ci_clu[k][0], 4) for k in KEYS},
                         **{f"{k}_clu_hi": round(ci_clu[k][1], 4) for k in KEYS}})
    dump(RESULTS / "revision_balanced_external.csv", rows)

    # ---- single-class external specificity, Wilson, from prediction files
    rows = []
    for name in [M1] + MODELS:
        for s in ("split_c", "split_d", "split_b_test"):
            conds = ([("baseline", PRED / f"{M1}__{s if s != 'split_b_test' else 'split_b'}.csv")]
                     if name == M1 else
                     [("baseline", PRED / f"{name}__baseline_seed42__{s}.csv"),
                      ("normalized", PRED / f"{name}__{s if s != 'split_b_test' else 'split_b'}.csv")])
            for cond, path in conds:
                if not path.exists():
                    continue
                ids, y, p = read_pred(path)
                a = y == 0
                k = int(((p < THRESHOLD) & a).sum()); n = int(a.sum())
                lo, hi = wilson(k, n)
                rows.append({"model": DISPLAY[name], "condition": cond, "set": s,
                             "k": k, "n": n, "specificity": round(k / n, 4),
                             "lo": round(lo, 4), "hi": round(hi, 4)})
    dump(RESULTS / "revision_external_specificity.csv", rows)
    rows_spec = rows

    # ---- exact McNemar between baseline models on the Split B test partition
    import itertools
    from scipy.stats import binomtest
    files = {M1: PRED / f"{M1}__split_b.csv",
             **{m: PRED / f"{m}__baseline_seed42__split_b_test.csv" for m in MODELS}}
    correct = {}
    for m, path in files.items():
        ids, y, p = read_pred(path)
        correct[m] = dict(zip(ids, (p >= THRESHOLD).astype(int) == y))
    ids = sorted(correct[M1])
    tests = []
    for a, b in itertools.combinations(files, 2):
        x = np.array([correct[a][i] for i in ids]); z = np.array([correct[b][i] for i in ids])
        n01, n10 = int((x & ~z).sum()), int((~x & z).sum())
        pv = binomtest(n01, n01 + n10, 0.5).pvalue if n01 + n10 else 1.0
        tests.append([DISPLAY[a], DISPLAY[b], n01, n10, pv])
    tests.sort(key=lambda t: t[4])
    run = 0.0
    rows = []
    for i, t in enumerate(tests):
        run = max(run, min(1.0, (len(tests) - i) * t[4]))
        rows.append({"model_a": t[0], "model_b": t[1], "a_only_correct": t[2],
                     "b_only_correct": t[3], "p_exact": round(t[4], 4),
                     "p_holm": round(run, 4)})
    dump(RESULTS / "revision_mcnemar_baseline.csv", rows)

    # ---- condition C minus condition D, Newcombe hybrid-score interval.
    # The two conditions come from one 150-package archive but the image-to-
    # package mapping is not distributed, so they cannot be paired; treating
    # them as independent widens the interval if the packages overlap.
    spec = {(r["model"], r["condition"], r["set"]): r for r in rows_spec}
    rows = []
    for (m, c, s), r in spec.items():
        if s != "split_c" or (m, c, "split_d") not in spec:
            continue
        d_ = spec[(m, c, "split_d")]
        k1, n1, k2, n2 = r["k"], r["n"], d_["k"], d_["n"]
        p1, p2 = k1 / n1, k2 / n2
        l1, u1 = wilson(k1, n1); l2, u2 = wilson(k2, n2)
        diff = p1 - p2
        rows.append({"model": m, "condition": c, "c_minus_d": round(diff, 4),
                     "lo": round(diff - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2), 4),
                     "hi": round(diff + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2), 4)})
    dump(RESULTS / "revision_c_minus_d.csv", rows)


def dump(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    print(f"wrote {path.name} ({len(rows)} rows)")


if __name__ == "__main__":
    {"score": stage_score, "splita": stage_splita, "stats": stage_stats}[sys.argv[1]]()

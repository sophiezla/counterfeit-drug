"""
A paired measurement of near-duplicate leakage, on one fixed test set.

Gap this closes. The paper bounds leakage by counting: 7 of the 76 Split A
test images have a near-duplicate group represented in Split A's training
partition, so at most 7/76 = 9.2 points of Split A test accuracy can come
from recognising a training photograph. That count is right and the bound it
supports is real, but it is a bound on one channel only. Admitting a mate
into training also changes the fitted parameters, and those parameters decide
the other 69 predictions too; nothing in the count constrains that second,
indirect channel in either direction. The measured Split A - Split B delta
does not settle it either, because the two splits do not share a test set --
230 of 510 images are assigned differently -- so that delta mixes the effect
of leakage with the effect of testing on different images.

This script separates the two channels by measuring instead of counting.
One test set is fixed. Two training sets are built around it that differ in
exactly one respect: whether the near-duplicate mates of the test images are
admitted. Everything else -- test images, validation set, architecture,
learning rate, augmentation, training-set size and training-set class
balance -- is held identical, so the difference in predictions is
attributable to the mates and to nothing else.

    exposed     the 28 test images that have a mate. The leaky arm has seen
                a near-duplicate of each; the clean arm has not. The direct
                channel acts here and only here.
    unexposed   the 46 test images with no mate anywhere in the pool. Both
                arms are equally ignorant of them. Any difference here is
                the indirect channel, i.e. the one the counting argument
                cannot see.

Design notes, each of which a reviewer would otherwise have to ask about:

  * The two training sets are the SAME SIZE and carry the SAME CLASS BALANCE.
    The leaky arm receives the 30 mates; the clean arm receives 30 substitute
    images drawn from singleton groups, class-matched one for one. Adding the
    mates to one arm without substituting in the other would confound leakage
    with training-set size, which is a different experiment.
  * The design is built under its own fixed seed, independent of the training
    seed, so all seeds train on the identical partition and the pairing is
    exact. Only initialisation, shuffling and augmentation move.
  * The test set is 74 images to match Split B's, of which 28 are exposed --
    every exposed image the pool admits. The pool has 480 groups over 510
    images (26 groups of 2, 2 of 3), so 28 is not a sample of the exposed
    images, it is all of them. It is also small, and the interval on the
    exposed-subset difference is correspondingly wide; the summary reports
    that interval rather than a point estimate for exactly that reason.
  * M1 is excluded. It is 97 parameters over a 96-bin colour histogram and
    has no capacity to memorise an individual photograph, so the direct
    channel this script measures does not exist for it.

    python modeling/leakage_paired.py               # all seeds, resumable
    python modeling/leakage_paired.py --seed 43     # one seed (worker mode)
    python modeling/leakage_paired.py --design      # print the partition only
    python modeling/leakage_paired.py --summary     # the tables

Output: modeling/results/leakage_paired_predictions.csv   (per image per run)
        modeling/results/leakage_paired_summary.csv       (accuracies)
        paper/tables/table_leakage_paired.csv             (the manuscript's)
"""
import argparse
import csv
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "modeling" / "results"
PRED = RESULTS / "leakage_paired_predictions.csv"
SUMMARY = RESULTS / "leakage_paired_summary.csv"
PAPER_TABLE = ROOT / "paper" / "tables" / "table_leakage_paired.csv"

SEEDS = [42, 43, 44, 45, 46]
ARMS = ["clean", "leaky"]

# Fixed, and deliberately not 42: the partition must not move when the
# training seed does, and using a distinct value makes that visible.
DESIGN_SEED = 20260829

N_TEST = 74          # matches Split B's test partition
VAL_FRACTION = 0.15

PRED_FIELDS = ["seed", "model", "arm", "image_id", "exposed", "y_true", "y_prob"]

DISPLAY = {
    "model2_smallcnn_gap": "M2 CNN",
    "model3_mobilenetv3small_frozen": "M3 MobileNetV3",
    "model4_efficientnetb0_frozen": "M4 EfficientNet-B0",
}
# Cheapest first, so a killed run still leaves the most models finished.
MODELS = ["model3_mobilenetv3small_frozen", "model2_smallcnn_gap",
          "model4_efficientnetb0_frozen"]


# ------------------------------------------------------------------ design

def build_design():
    """
    Returns (test, mates, substitutes, base_train, val), each a list of the
    example dicts common.load_examples yields, plus the set of exposed test
    image_ids. Pure function of the pool and DESIGN_SEED.
    """
    from common import load_examples

    examples = load_examples("split_b")
    by_id = {e["image_id"]: e for e in examples}

    groups = defaultdict(list)
    for e in examples:
        groups[e["product_identity"]].append(e["image_id"])
    for pid in groups:
        groups[pid].sort()

    multi = sorted(pid for pid, ids in groups.items() if len(ids) > 1)
    singles = sorted(ids[0] for pid, ids in groups.items() if len(ids) == 1)

    exposed = [groups[pid][0] for pid in multi]
    mates = [i for pid in multi for i in groups[pid][1:]]

    rng = np.random.default_rng(DESIGN_SEED)

    def label(i):
        return by_id[i]["label"]

    def take(pool, n_counterfeit, n_authentic):
        """Draw class-stratified without replacement; returns (drawn, rest)."""
        drawn = []
        for lab, k in ((1, n_counterfeit), (0, n_authentic)):
            avail = sorted(i for i in pool if label(i) == lab)
            assert len(avail) >= k, (lab, k, len(avail))
            drawn += list(rng.choice(avail, size=k, replace=False))
        rest = [i for i in pool if i not in set(drawn)]
        return sorted(drawn), rest

    # Fill the test set out to N_TEST with singletons, choosing the classes so
    # that the test set carries the pool's own class ratio rather than the
    # exposed images' (which are 42:16 authentic-heavy and would otherwise
    # skew it).
    pool_counterfeit = sum(1 for e in examples if e["label"] == 1)
    target_counterfeit = round(N_TEST * pool_counterfeit / len(examples))
    exposed_counterfeit = sum(1 for i in exposed if label(i) == 1)
    fill = N_TEST - len(exposed)
    fill_counterfeit = target_counterfeit - exposed_counterfeit
    assert 0 <= fill_counterfeit <= fill, (target_counterfeit, exposed_counterfeit)
    test_fill, remaining = take(singles, fill_counterfeit, fill - fill_counterfeit)

    # Substitutes: one per mate, matched class for class, so the two training
    # arms are identical in size and in class balance.
    mate_counterfeit = sum(1 for i in mates if label(i) == 1)
    substitutes, remaining = take(remaining, mate_counterfeit,
                                  len(mates) - mate_counterfeit)

    # Whatever is left becomes the shared base: a common validation set and
    # the part of the training set both arms hold.
    n_val = round(len(remaining) * VAL_FRACTION)
    rem_counterfeit = sum(1 for i in remaining if label(i) == 1)
    val_counterfeit = round(n_val * rem_counterfeit / len(remaining))
    val, base_train = take(remaining, val_counterfeit, n_val - val_counterfeit)

    test = sorted(exposed) + test_fill
    sel = lambda ids: [by_id[i] for i in sorted(ids)]
    return (sel(test), sel(mates), sel(substitutes), sel(base_train), sel(val),
            set(exposed))


def check_design(test, mates, substitutes, base_train, val, exposed):
    """Every property the comparison relies on, asserted rather than assumed."""
    pid = lambda rows: {e["product_identity"] for e in rows}
    ids = lambda rows: {e["image_id"] for e in rows}
    counterfeit = lambda rows: sum(1 for e in rows if e["label"] == 1)

    parts = [test, mates, substitutes, base_train, val]
    all_ids = [i for p in parts for i in ids(p)]
    assert len(all_ids) == len(set(all_ids)), "partitions overlap"

    clean_train = base_train + substitutes
    leaky_train = base_train + mates

    assert len(clean_train) == len(leaky_train), "arms differ in size"
    assert counterfeit(clean_train) == counterfeit(leaky_train), \
        "arms differ in class balance"

    # The one intended difference, and its absence in the control arm.
    assert not (pid(clean_train) & pid(test)), \
        "clean arm shares a product group with the test set"
    assert pid(leaky_train) & pid(test) == pid(mates), \
        "leaky arm's overlap with the test set is not exactly the mates"
    assert {e["image_id"] for e in test if e["product_identity"] in pid(mates)} \
        == exposed, "exposed set does not match the mates' groups"
    assert not (pid(val) & pid(test)), "validation leaks into the test set"


def describe_design():
    test, mates, substitutes, base_train, val, exposed = build_design()
    check_design(test, mates, substitutes, base_train, val, exposed)
    n_c = lambda rows: sum(1 for e in rows if e["label"] == 1)
    print(f"design seed {DESIGN_SEED}")
    for name, rows in (("test", test), ("  exposed", [e for e in test if e["image_id"] in exposed]),
                       ("  unexposed", [e for e in test if e["image_id"] not in exposed]),
                       ("mates (leaky arm only)", mates),
                       ("substitutes (clean arm only)", substitutes),
                       ("base train (both arms)", base_train),
                       ("val (both arms)", val)):
        print(f"  {name:<30} n={len(rows):>4}  counterfeit={n_c(rows):>3}")
    print(f"  {'clean train total':<30} n={len(base_train) + len(substitutes):>4}"
          f"  counterfeit={n_c(base_train) + n_c(substitutes):>3}")
    print(f"  {'leaky train total':<30} n={len(base_train) + len(mates):>4}"
          f"  counterfeit={n_c(base_train) + n_c(mates):>3}")
    print("  all assertions pass")


# ------------------------------------------------------------------ worker

def _run_model2(train, val, test, run_tag):
    from common import set_seed, SEED
    from result_io import load_chosen_lr
    from torch_utils import train_model, evaluate_model
    from train_model2_cnn import SmallCNN, MODEL_NAME

    set_seed(SEED)
    model = SmallCNN()
    model, _ = train_model(model, train, val, load_chosen_lr(MODEL_NAME),
                           model_tag=MODEL_NAME, run_tag=run_tag)
    ids, y_true, y_prob = evaluate_model(model, test)
    return ids, y_true, y_prob


def _run_frozen(module_name, train, val, test, run_tag):
    import importlib

    from common import set_seed, SEED
    from feature_cache import extract_features, K_AUGMENT
    from result_io import load_chosen_lr
    from torch_utils import train_model_on_features, evaluate_model_on_features

    mod = importlib.import_module(module_name)
    fe, gap = mod.build_backbone()

    def feats(examples, is_train, k):
        return extract_features(fe, gap, examples, train=is_train, k_augment=k)

    X_tr, y_tr, _ = feats(train, True, K_AUGMENT)
    X_va, y_va, _ = feats(val, False, 1)
    X_te, y_te, _ = feats(test, False, 1)

    set_seed(SEED)
    head = mod.build_head()
    head, _ = train_model_on_features(head, X_tr, y_tr, X_va, y_va,
                                      load_chosen_lr(mod.MODEL_NAME),
                                      model_tag=mod.MODEL_NAME, run_tag=run_tag)
    test_ids = [e["image_id"] for e in test]
    ids, y_true, y_prob = evaluate_model_on_features(head, X_te, y_te, test_ids)
    return ids, y_true, y_prob


def load_predictions():
    if not PRED.exists():
        return []
    with open(PRED, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_predictions(rows):
    PRED.parent.mkdir(parents=True, exist_ok=True)
    with open(PRED, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=PRED_FIELDS)
        w.writeheader()
        w.writerows(rows)


def worker(seed):
    print(f"=== seed {seed} ===", flush=True)
    assert os.environ.get("PHARMAVISION_SEED") == str(seed), \
        "worker must run with PHARMAVISION_SEED set before import"

    test, mates, substitutes, base_train, val, exposed = build_design()
    check_design(test, mates, substitutes, base_train, val, exposed)
    train_sets = {"clean": base_train + substitutes,
                  "leaky": base_train + mates}

    rows = load_predictions()
    done = {(r["seed"], r["model"], r["arm"]) for r in rows}

    for model in MODELS:
        for arm in ARMS:
            if (str(seed), model, arm) in done:
                print(f"  skip (done): {DISPLAY[model]} / {arm}", flush=True)
                continue
            tag = f"leakpair_seed{seed}_{arm}"
            print(f"  {DISPLAY[model]} / {arm} ...", flush=True)

            if model == "model2_smallcnn_gap":
                ids, y_true, y_prob = _run_model2(
                    train_sets[arm], val, test, tag)
            else:
                module = ("train_model3_mobilenet" if model.startswith("model3")
                          else "train_model4_efficientnet")
                ids, y_true, y_prob = _run_frozen(
                    module, train_sets[arm], val, test, tag)

            correct = (np.array(y_prob) >= 0.5) == np.array(y_true)
            print(f"    accuracy {correct.mean():.4f} on n={len(ids)}",
                  flush=True)

            for i, t, p in zip(ids, y_true, y_prob):
                rows.append({"seed": seed, "model": model, "arm": arm,
                             "image_id": i, "exposed": int(i in exposed),
                             "y_true": int(t), "y_prob": round(float(p), 6)})
            write_predictions(rows)      # checkpoint after every arm


# ----------------------------------------------------------------- summary

def _paired_bootstrap(pairs, n_boot=10000, seed=DESIGN_SEED):
    """
    Percentile interval on the leaky-minus-clean accuracy difference,
    resampling IMAGES (both arms' verdicts on an image move together, which
    is what makes it paired) rather than predictions.
    """
    if not pairs:
        return float("nan"), float("nan")
    a = np.array([p[0] for p in pairs], dtype=float)   # leaky correct
    b = np.array([p[1] for p in pairs], dtype=float)   # clean correct
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(a), size=(n_boot, len(a)))
    diffs = a[idx].mean(axis=1) - b[idx].mean(axis=1)
    return float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def summarise():
    from metrics import mcnemar_test

    rows = load_predictions()
    if not rows:
        raise SystemExit("no predictions yet; run the experiment first")

    # (model, arm, seed) -> {image_id: (correct, exposed)}
    runs = defaultdict(dict)
    for r in rows:
        correct = int((float(r["y_prob"]) >= 0.5) == bool(int(r["y_true"])))
        runs[(r["model"], r["arm"], r["seed"])][r["image_id"]] = (
            correct, int(r["exposed"]))

    out = []
    for model in MODELS:
        seeds = sorted({s for (m, a, s) in runs if m == model})
        if not seeds:
            continue
        for subset in ("all", "exposed", "unexposed"):
            def keep(exposed):
                return (subset == "all"
                        or (subset == "exposed") == bool(exposed))

            per_seed_acc = {"clean": [], "leaky": []}
            pooled_pairs, n01, n10 = [], 0, 0
            per_seed_p = []
            n_images = 0

            for s in seeds:
                got = {}
                for arm in ARMS:
                    run = runs.get((model, arm, s))
                    if run is None:
                        break
                    got[arm] = {i: c for i, (c, e) in run.items() if keep(e)}
                if len(got) != 2:
                    continue
                ids = sorted(got["clean"])
                n_images = len(ids)
                for arm in ARMS:
                    per_seed_acc[arm].append(
                        float(np.mean([got[arm][i] for i in ids])))
                pairs = [(got["leaky"][i], got["clean"][i]) for i in ids]
                pooled_pairs += pairs
                n01 += sum(1 for l, c in pairs if l and not c)
                n10 += sum(1 for l, c in pairs if c and not l)
                y_true = [1] * len(ids)
                _, p = mcnemar_test(y_true, [l for l, _ in pairs],
                                    [c for _, c in pairs])
                per_seed_p.append(p)

            if not pooled_pairs:
                continue
            lo, hi = _paired_bootstrap(pooled_pairs)
            y_true = [1] * len(pooled_pairs)
            _, p_pooled = mcnemar_test(
                y_true, [l for l, _ in pooled_pairs],
                [c for _, c in pooled_pairs])

            clean = np.array(per_seed_acc["clean"])
            leaky = np.array(per_seed_acc["leaky"])
            out.append({
                "model": DISPLAY[model], "subset": subset,
                "n_images": n_images, "n_seeds": len(clean),
                "clean_mean": round(float(clean.mean()), 4),
                "clean_sd": round(float(clean.std(ddof=1)), 4) if len(clean) > 1 else "",
                "leaky_mean": round(float(leaky.mean()), 4),
                "leaky_sd": round(float(leaky.std(ddof=1)), 4) if len(leaky) > 1 else "",
                "diff_points": round(float((leaky - clean).mean()) * 100, 1),
                "diff_ci_low_points": round(lo * 100, 1),
                "diff_ci_high_points": round(hi * 100, 1),
                "leaky_only_correct": n01, "clean_only_correct": n10,
                "mcnemar_p_pooled": round(p_pooled, 4),
                "mcnemar_p_min_per_seed": round(min(per_seed_p), 4),
            })

    fields = list(out[0].keys())
    for path in (SUMMARY, PAPER_TABLE):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(out)

    print(f"{'model':<20} {'subset':<10} {'n':>4} {'clean':>14} {'leaky':>14} "
          f"{'diff (pts)':>22} {'McNemar p':>10}")
    for r in out:
        cell = lambda k: (f"{r[k + '_mean']:.3f}+/-{r[k + '_sd']:.3f}"
                          if r[k + "_sd"] != "" else f"{r[k + '_mean']:.3f}")
        span = (f"{r['diff_points']:+.1f} "
                f"[{r['diff_ci_low_points']:+.1f}, {r['diff_ci_high_points']:+.1f}]")
        print(f"{r['model']:<20} {r['subset']:<10} {r['n_images']:>4} "
              f"{cell('clean'):>14} {cell('leaky'):>14} {span:>22} "
              f"{r['mcnemar_p_pooled']:>10.3f}")
    print(f"\nwrote {SUMMARY.relative_to(ROOT)} and "
          f"{PAPER_TABLE.relative_to(ROOT)}")


# -------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--seed", type=int, help="run one seed (worker mode)")
    ap.add_argument("--design", action="store_true",
                    help="print the partition and its assertions, run nothing")
    ap.add_argument("--summary", action="store_true",
                    help="rebuild the tables from existing predictions")
    args = ap.parse_args()

    if args.design:
        describe_design()
        return
    if args.summary:
        summarise()
        return
    if args.seed is not None:
        worker(args.seed)
        return

    for seed in SEEDS:
        env = dict(os.environ, PHARMAVISION_SEED=str(seed))
        cmd = [sys.executable, str(Path(__file__).resolve()), "--seed", str(seed)]
        print(f"\n>>> {' '.join(cmd)}", flush=True)
        subprocess.run(cmd, env=env, cwd=str(ROOT), check=True)
    summarise()


if __name__ == "__main__":
    main()

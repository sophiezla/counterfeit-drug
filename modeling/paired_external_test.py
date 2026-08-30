"""
Paired baseline-vs-normalized comparison on the external sets.

Gap this closes. Table 5 reports the correction's effect as the distance
between two Wilson intervals, one for the baseline model and one for the
normalized model. Those intervals describe two separate proportions; the
quantity actually of interest is a *difference*, and the two conditions are
evaluated on the same 150 external photographs, so the comparison is paired
and a paired test is the right instrument. This script runs one.

What it does. For M2, M3 and M4 it loads the persisted baseline and normalized
checkpoints written by seed_sweep.py at each of the five seeds, replays them
over Split C and Split D, and keeps the per-image verdict rather than the
count. It then reports, per model and per external set:

  * the seed-mean accuracy of each arm,
  * their difference with a 95% bootstrap interval that resamples *images*,
    so both arms' verdicts on an image move together and the pairing is kept,
  * McNemar's exact test on the discordant pairs, pooled over seeds.

The bootstrap and the McNemar form follow modeling/leakage_paired.py, so the
two paired analyses in this paper are computed the same way.

Self-check (Section S-I-G's rule). Every replayed accuracy is asserted against
the value seed_sweep.csv recorded for the same model, seed and condition; the
script refuses to write anything if one disagrees. M1 has no checkpoint and
never passes through the operator, so it is out of scope here.

Output: modeling/results/paired_external_test.csv
        paper/tables/table_paired_external.csv
"""
import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "modeling" / "results"
OUT = RESULTS / "paired_external_test.csv"
PAPER_TABLE = ROOT / "paper" / "tables" / "table_paired_external.csv"
SEED_SWEEP = RESULTS / "seed_sweep.csv"

SEEDS = [42, 43, 44, 45, 46]
CONDITIONS = ["baseline", "normalized"]
N_BOOT = 2000
BOOT_SEED = 20260830

MODELS = ["model2_smallcnn_gap", "model3_mobilenetv3small_frozen",
          "model4_efficientnetb0_frozen"]
DISPLAY = {"model2_smallcnn_gap": "M2 CNN",
           "model3_mobilenetv3small_frozen": "M3 MobileNetV3",
           "model4_efficientnetb0_frozen": "M4 EfficientNet-B0"}


def verdicts(model_name, seed, condition, sets):
    """Per-image correctness vectors for one persisted checkpoint."""
    from result_io import load_chosen_lr, load_checkpoint

    tag = "seed{}_{}".format(seed, condition)
    normalize = condition == "normalized"
    out = {}

    if model_name == "model2_smallcnn_gap":
        from train_model2_cnn import SmallCNN
        from torch_utils import evaluate_model

        model = SmallCNN()
        load_checkpoint(model, model_name, tag,
                        expected_lr=load_chosen_lr(model_name))
        model.eval()
        for name, ex in sets.items():
            _, _, prob = evaluate_model(model, ex, normalize=normalize)
            out[name] = (np.array(prob) < 0.5).astype(int)
        return out

    import importlib
    from feature_cache import extract_features
    from torch_utils import evaluate_model_on_features

    module = ("train_model3_mobilenet" if model_name.startswith("model3")
              else "train_model4_efficientnet")
    mod = importlib.import_module(module)
    fe, gap = mod.build_backbone()
    head = mod.build_head()
    load_checkpoint(head, model_name, tag,
                    expected_lr=load_chosen_lr(model_name))
    head.eval()
    for name, ex in sets.items():
        X, y, ids = extract_features(fe, gap, ex, train=False, k_augment=1,
                                     normalize=normalize)
        _, _, prob = evaluate_model_on_features(head, X, y, ids)
        out[name] = (np.array(prob) < 0.5).astype(int)
    return out


def recorded():
    """seed_sweep.csv, keyed for the self-check."""
    rows = list(csv.DictReader(open(SEED_SWEEP, newline="", encoding="utf-8")))
    return {(r["model"], int(r["seed"]), r["condition"]):
            (float(r["split_c_acc"]), float(r["split_d_acc"])) for r in rows}


def mcnemar_exact(n01, n10):
    n = n01 + n10
    if n == 0:
        return 1.0
    k = min(n01, n10)
    tail = sum(math.comb(n, i) for i in range(k + 1)) * 0.5 ** n
    return min(1.0, 2 * tail)


def paired_bootstrap(base, norm, rng):
    """95% interval on the seed-mean accuracy difference, resampling images.

    base and norm are (n_seeds, n_images) correctness matrices. Resampling
    image indices keeps every seed's verdict on an image together, which is
    what makes the interval a paired one.
    """
    n = base.shape[1]
    diffs = np.empty(N_BOOT)
    for b in range(N_BOOT):
        idx = rng.integers(0, n, n)
        diffs[b] = norm[:, idx].mean() - base[:, idx].mean()
    return float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true",
                    help="seed 42 only, for a smoke test")
    args = ap.parse_args()
    seeds = [42] if args.quick else SEEDS

    from eval_external_from_checkpoints import split_c_examples, split_d_examples
    sets = {"split_c": split_c_examples(), "split_d": split_d_examples()}
    print("Split C: {}   Split D: {}".format(len(sets["split_c"]),
                                             len(sets["split_d"])))

    rec = recorded()
    store = {}
    for model in MODELS:
        for seed in seeds:
            for cond in CONDITIONS:
                v = verdicts(model, seed, cond, sets)
                store[(model, seed, cond)] = v
                want = rec[(model, seed, cond)]
                got = (v["split_c"].mean(), v["split_d"].mean())
                for split, g, w in zip(("split_c", "split_d"), got, want):
                    if abs(g - w) > 0.005:
                        raise SystemExit(
                            "{} seed {} {} {}: replay gives {:.4f}, "
                            "seed_sweep.csv recorded {:.4f}. Refusing to report "
                            "a paired test on checkpoints that do not reproduce "
                            "the run they came from.".format(
                                model, seed, cond, split, g, w))
                print("  {:<20} seed {} {:<10} C={:.3f} D={:.3f}".format(
                    DISPLAY[model], seed, cond, got[0], got[1]), flush=True)

    rng = np.random.default_rng(BOOT_SEED)
    rows = []
    for model in MODELS:
        for split in ("split_c", "split_d"):
            base = np.stack([store[(model, s, "baseline")][split] for s in seeds])
            norm = np.stack([store[(model, s, "normalized")][split] for s in seeds])
            n01 = int(((norm == 1) & (base == 0)).sum())
            n10 = int(((norm == 0) & (base == 1)).sum())
            lo, hi = paired_bootstrap(base, norm, rng)
            rows.append({
                "model": DISPLAY[model],
                "split": split.replace("_", " ").title(),
                "n_images": base.shape[1], "n_seeds": len(seeds),
                "baseline_mean": round(float(base.mean()), 4),
                "normalized_mean": round(float(norm.mean()), 4),
                "difference_pp": round(float(norm.mean() - base.mean()) * 100, 1),
                "ci_lo_pp": round(lo * 100, 1), "ci_hi_pp": round(hi * 100, 1),
                "n01_norm_only": n01, "n10_base_only": n10,
                "mcnemar_p": mcnemar_exact(n01, n10),
            })

    fields = list(rows[0].keys())
    for path in (OUT, PAPER_TABLE):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

    print()
    for r in rows:
        print("{:<20} {:<8} {:.3f} -> {:.3f}  {:+.1f} pp [{:+.1f}, {:+.1f}]  "
              "n01={} n10={} p={:.3g}".format(
                  r["model"], r["split"], r["baseline_mean"],
                  r["normalized_mean"], r["difference_pp"], r["ci_lo_pp"],
                  r["ci_hi_pp"], r["n01_norm_only"], r["n10_base_only"],
                  r["mcnemar_p"]))
    print("\nwrote {} and {}".format(OUT.name, PAPER_TABLE.name))


if __name__ == "__main__":
    main()

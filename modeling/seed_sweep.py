"""
Seed-to-seed variance for the results the paper's argument rests on.

Gap this closes. Every number in this study comes from one training run at
seed 42. The Wilson intervals in Table 8 quantify sampling uncertainty on a
fixed trained model; they say nothing about what a different initialisation
would have produced, and the Limitations section says so ("what remains
unmeasured is seed-to-seed variance itself"). That gap matters more here than
it usually would, because this project has already been burned once by
mistaking run-to-run movement for a real effect: M3's answer to "does
normalization help?" came out positive, negative and flat across three runs
before the unseeded-augmentation defect behind it was found (Section S-I-G).
A stated interval is the only thing that separates the two readings.

What it runs, per seed, for M2, M3 and M4:

    normalized   the production pipeline -- Split B test accuracy, then
                 external accuracy on Split C and Split D
    baseline     the same, with the three-way capture normalization bypassed

That is the priority set: the in-distribution number, the external number the
correction is claimed to move, and the second capture shift that qualifies it.
The ordering sweep is deliberately NOT repeated across seeds -- six orderings
times five seeds is thirty more training runs, and the claim it supports (a
28-point gap between two groups of three) is an order of magnitude larger than
any plausible seed effect.

M1 is excluded: it is a convex fit solved deterministically by L-BFGS, with no
random initialisation and no augmentation, so its accuracy is identical under
every seed.

Design notes, both of which matter for trusting the output:

  * Each seed runs in its own subprocess with PHARMAVISION_SEED set, so the
    seed is fixed before common.py is imported and every downstream consumer
    -- model init, DataLoader shuffling, the augmented extraction passes --
    derives from the same value. Running seeds in one process would let each
    inherit whatever RNG state the previous one left behind, which is the
    precise defect of Section S-I-G in a new costume.
  * Seed 42's normalized rows are checked against the values of record and a
    mismatch is reported loudly. This is the practice Section S-I-G argues for
    -- any script that rebuilds a model should compute one metric whose
    correct value is already known and refuse to be trusted if it disagrees.

The learning rate is the recorded one (results/chosen_lrs.json) for every
seed, not re-searched per seed: re-searching would vary two things at once
and the protocol of Table S2 fixes the rate from the Split A search anyway.

    python modeling/seed_sweep.py                 # all seeds, resumable
    python modeling/seed_sweep.py --seed 43       # one seed (worker mode)
    python modeling/seed_sweep.py --summary       # mean +/- sd tables

Output: modeling/results/seed_sweep.csv          (one row per seed/model/condition)
        modeling/results/seed_sweep_summary.csv  (mean +/- sd across seeds)
        paper/tables/table_seed_variance.csv     (the manuscript's table)
"""
import argparse
import csv
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "modeling" / "results"
OUT = RESULTS / "seed_sweep.csv"
SUMMARY = RESULTS / "seed_sweep_summary.csv"
PAPER_TABLE = ROOT / "paper" / "tables" / "table_seed_variance.csv"

SEEDS = [42, 43, 44, 45, 46]
CONDITIONS = ["normalized", "baseline"]

FIELDS = ["seed", "model", "condition", "split_b_test_acc", "split_b_test_n",
          "split_c_acc", "split_c_correct", "split_c_n",
          "split_d_acc", "split_d_correct", "split_d_n", "epochs_run"]

# Production values of record, seed 42, normalized pipeline. Sources:
# results/leakage_table.csv (Split B test accuracy) and
# results/external_from_checkpoints.csv (Split C and Split D).
OF_RECORD = {
    "model2_smallcnn_gap": (0.8649, 0.8600, 0.4631),
    "model3_mobilenetv3small_frozen": (0.9324, 0.7733, 0.7248),
    "model4_efficientnetb0_frozen": (0.9189, 0.8067, 0.8322),
}
DISPLAY = {
    "model2_smallcnn_gap": "M2 CNN",
    "model3_mobilenetv3small_frozen": "M3 MobileNetV3",
    "model4_efficientnetb0_frozen": "M4 EfficientNet-B0",
}
# Cheapest first, so a killed run still leaves the most conditions finished.
MODELS = ["model3_mobilenetv3small_frozen", "model2_smallcnn_gap",
          "model4_efficientnetb0_frozen"]


# ----------------------------------------------------------------- worker

def _splits():
    from common import load_examples
    from eval_external_from_checkpoints import split_c_examples, split_d_examples

    ex = load_examples("split_b")
    by = {s: [e for e in ex if e["split"] == s] for s in ("train", "val", "test")}
    return by, split_c_examples(), split_d_examples()


def _run_model2(by, split_c, split_d, normalize, run_tag):
    from common import set_seed, SEED
    from result_io import load_chosen_lr
    from torch_utils import train_model, evaluate_model
    from train_model2_cnn import SmallCNN, MODEL_NAME

    set_seed(SEED)
    model = SmallCNN()
    model, history = train_model(model, by["train"], by["val"],
                                 load_chosen_lr(MODEL_NAME),
                                 model_tag=MODEL_NAME, run_tag=run_tag,
                                 normalize=normalize)

    _, y_true, y_prob = evaluate_model(model, by["test"], normalize=normalize)
    b_acc = float(np.mean((np.array(y_prob) >= 0.5) == np.array(y_true)))

    ext = []
    for ex in (split_c, split_d):
        _, _, prob = evaluate_model(model, ex, normalize=normalize)
        ext.append((int((np.array(prob) < 0.5).sum()), len(ex)))
    return b_acc, len(by["test"]), ext, len(history)


def _run_frozen(module_name, by, split_c, split_d, normalize, run_tag):
    import importlib

    from common import set_seed, SEED
    from feature_cache import extract_features, K_AUGMENT
    from result_io import load_chosen_lr
    from torch_utils import train_model_on_features, evaluate_model_on_features

    mod = importlib.import_module(module_name)
    fe, gap = mod.build_backbone()

    def feats(examples, train, k):
        return extract_features(fe, gap, examples, train=train, k_augment=k,
                                normalize=normalize)

    X_tr, y_tr, _ = feats(by["train"], True, K_AUGMENT)
    X_va, y_va, _ = feats(by["val"], False, 1)
    X_te, y_te, _ = feats(by["test"], False, 1)

    set_seed(SEED)
    head = mod.build_head()
    head, history = train_model_on_features(head, X_tr, y_tr, X_va, y_va,
                                            load_chosen_lr(mod.MODEL_NAME),
                                            model_tag=mod.MODEL_NAME,
                                            run_tag=run_tag)

    _, y_true, y_prob = evaluate_model_on_features(head, X_te, y_te,
                                                   list(range(len(y_te))))
    b_acc = float(np.mean((np.array(y_prob) >= 0.5) == np.array(y_true)))

    ext = []
    for ex in (split_c, split_d):
        X, y, ids = feats(ex, False, 1)
        _, _, prob = evaluate_model_on_features(head, X, y, ids)
        ext.append((int((np.array(prob) < 0.5).sum()), len(ex)))
    return b_acc, len(y_te), ext, len(history)


def load_rows():
    if not OUT.exists():
        return []
    with open(OUT, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_rows(rows):
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def check_of_record(seed, model, condition, b_acc, c_acc, d_acc):
    """Seed 42 normalized must reproduce the published numbers, or nothing
    this script reports can be trusted (Section S-I-G's rule)."""
    if seed != 42 or condition != "normalized":
        return
    want = OF_RECORD[model]
    got = (b_acc, c_acc, d_acc)
    off = [f"{n}: got {g:.4f}, of record {w:.4f}"
           for n, g, w in zip(("Split B", "Split C", "Split D"), got, want)
           if abs(g - w) > 0.005]
    if off:
        print(f"  !! WARNING: seed 42 normalized does not reproduce "
              f"{DISPLAY[model]}'s values of record -- " + "; ".join(off))
        print("     The harness is not running the production pipeline; do not "
              "report the spread it measures.")
    else:
        print(f"  [ok] seed 42 normalized reproduces {DISPLAY[model]}'s "
              f"values of record")


def worker(seed):
    print(f"=== seed {seed} ===", flush=True)
    assert os.environ.get("PHARMAVISION_SEED") == str(seed), \
        "worker must run with PHARMAVISION_SEED set before import"

    by, split_c, split_d = _splits()
    rows = load_rows()
    done = {(r["seed"], r["model"], r["condition"]) for r in rows}

    for model in MODELS:
        for condition in CONDITIONS:
            if (str(seed), model, condition) in done:
                print(f"  skip (done): {DISPLAY[model]} / {condition}",
                      flush=True)
                continue
            normalize = condition == "normalized"
            tag = f"seed{seed}_{condition}"
            print(f"  {DISPLAY[model]} / {condition} ...", flush=True)

            if model == "model2_smallcnn_gap":
                b_acc, b_n, ext, epochs = _run_model2(
                    by, split_c, split_d, normalize, tag)
            else:
                module = ("train_model3_mobilenet"
                          if model.startswith("model3")
                          else "train_model4_efficientnet")
                b_acc, b_n, ext, epochs = _run_frozen(
                    module, by, split_c, split_d, normalize, tag)

            (c_k, c_n), (d_k, d_n) = ext
            c_acc, d_acc = c_k / c_n, d_k / d_n
            print(f"    Split B {b_acc:.4f}   Split C {c_k}/{c_n} = {c_acc:.4f}"
                  f"   Split D {d_k}/{d_n} = {d_acc:.4f}", flush=True)
            check_of_record(seed, model, condition, b_acc, c_acc, d_acc)

            rows.append({"seed": seed, "model": model, "condition": condition,
                         "split_b_test_acc": round(b_acc, 4),
                         "split_b_test_n": b_n,
                         "split_c_acc": round(c_acc, 4), "split_c_correct": c_k,
                         "split_c_n": c_n,
                         "split_d_acc": round(d_acc, 4), "split_d_correct": d_k,
                         "split_d_n": d_n, "epochs_run": epochs})
            write_rows(rows)      # checkpoint after every condition


# ----------------------------------------------------------------- summary

def summarise():
    rows = load_rows()
    if not rows:
        raise SystemExit("no rows yet; run the sweep first")

    out = []
    for model in MODELS:
        for condition in CONDITIONS:
            sub = [r for r in rows
                   if r["model"] == model and r["condition"] == condition]
            if not sub:
                continue
            rec = {"model": DISPLAY[model], "condition": condition,
                   "n_seeds": len(sub),
                   "seeds": " ".join(sorted(r["seed"] for r in sub))}
            for split in ("split_b_test_acc", "split_c_acc", "split_d_acc"):
                v = np.array([float(r[split]) for r in sub])
                rec[f"{split}_mean"] = round(float(v.mean()), 4)
                # Sample standard deviation: these are a sample of seeds, not
                # the population of them.
                rec[f"{split}_sd"] = (round(float(v.std(ddof=1)), 4)
                                      if len(v) > 1 else "")
                rec[f"{split}_min"] = round(float(v.min()), 4)
                rec[f"{split}_max"] = round(float(v.max()), 4)
            out.append(rec)

    fields = list(out[0].keys())
    for path in (SUMMARY, PAPER_TABLE):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(out)

    print(f"{'model':<20} {'condition':<11} {'seeds':>5}  "
          f"{'Split B':>16} {'Split C':>16} {'Split D':>16}")
    for r in out:
        def cell(k):
            sd = r[f"{k}_sd"]
            return f"{r[f'{k}_mean']:.3f}+/-{sd:.3f}" if sd != "" else \
                   f"{r[f'{k}_mean']:.3f}      "
        print(f"{r['model']:<20} {r['condition']:<11} {r['n_seeds']:>5}  "
              f"{cell('split_b_test_acc'):>16} {cell('split_c_acc'):>16} "
              f"{cell('split_d_acc'):>16}")
    print(f"\nwrote {SUMMARY.relative_to(ROOT)} and "
          f"{PAPER_TABLE.relative_to(ROOT)}")


# ----------------------------------------------------------------- driver

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, help="worker mode: run this seed only")
    ap.add_argument("--summary", action="store_true",
                    help="summarise the rows already collected")
    ap.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    args = ap.parse_args()

    if args.summary:
        summarise()
        return
    if args.seed is not None:
        worker(args.seed)
        return

    for seed in args.seeds:
        env = dict(os.environ, PHARMAVISION_SEED=str(seed))
        print(f"\n{'=' * 68}\nspawning worker for seed {seed}\n{'=' * 68}",
              flush=True)
        r = subprocess.run([sys.executable, str(Path(__file__).resolve()),
                            "--seed", str(seed)], env=env, cwd=str(ROOT))
        if r.returncode != 0:
            raise SystemExit(f"seed {seed} failed with exit {r.returncode}")
    summarise()


if __name__ == "__main__":
    main()

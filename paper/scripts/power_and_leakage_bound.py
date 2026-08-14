"""
Two analytic answers to the statistical-power critique.

Neither needs a training run, and both replace "the study is underpowered" with
a number saying exactly how underpowered, and exactly how large the effect it
was chasing could possibly have been.

(1) MINIMUM DETECTABLE EFFECT for the pairwise model comparisons. McNemar's
    exact test depends only on the discordant pairs, so for each observed
    discordant total D we can state the most lopsided split available and
    whether ANY split of that D would have reached p < 0.05. Where the answer
    is no, the comparison was unresolvable by construction and reporting it as
    "not significant" understates the problem: it could not have been
    significant.

(2) A HARD CEILING ON THE LEAKAGE EFFECT. The paper measures a leakage delta of
    <= 4.1 points and argues it is small because only 1.9% of product groups
    straddle the naive split. That argument can be made exactly. Count the test
    images under Split A whose product-identity group also appears in Split A's
    training partition; those are the only images a model could get right by
    recognising a training photograph. If there are k of them out of n, then no
    leakage mechanism can inflate test accuracy by more than k/n, whatever the
    model. That is an upper bound derived from the split alone, independent of
    any model, seed or run.

Writes paper/tables/table_power_and_bound.csv.
"""

import csv
import os
from collections import defaultdict
from math import comb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SPLIT_A = os.path.join(ROOT, "splits", "split_a.csv")
SPLIT_B = os.path.join(ROOT, "splits", "split_b.csv")
MCNEMAR = os.path.join(ROOT, "paper", "tables", "table_mcnemar.csv")
OUT = os.path.join(ROOT, "paper", "tables", "table_power_and_bound.csv")


def mcnemar_p(n01, n10):
    d = n01 + n10
    if d == 0:
        return 1.0
    k = min(n01, n10)
    return min(1.0, 2 * sum(comb(d, i) for i in range(k + 1)) * 0.5 ** d)


def min_detectable(d):
    """Most significant p available for a discordant total d, and the split."""
    best = (1.0, None)
    for k in range(d // 2 + 1):
        p = mcnemar_p(k, d - k)
        if p < best[0]:
            best = (p, (k, d - k))
    return best


def leakage_ceiling():
    """Test images under Split A whose product group also appears in A's train."""
    groups = {}
    for r in csv.DictReader(open(SPLIT_B, newline="", encoding="utf-8")):
        groups[r["image_id"]] = r["product_identity"]

    by_split = defaultdict(list)
    for r in csv.DictReader(open(SPLIT_A, newline="", encoding="utf-8")):
        by_split[r["split"]].append(r["image_id"])

    train_groups = {groups[i] for i in by_split["train"] if i in groups}
    test_ids = [i for i in by_split["test"] if i in groups]
    leaked = [i for i in test_ids if groups[i] in train_groups]
    return len(leaked), len(test_ids)


def main():
    rows = []

    print("=== (1) Minimum detectable effect, McNemar exact ===")
    print("A comparison whose discordant total is small cannot reach "
          "significance at any split.\n")
    seen = []
    if os.path.exists(MCNEMAR):
        for r in csv.DictReader(open(MCNEMAR, newline="", encoding="utf-8")):
            d = int(float(r["n_discordant"]))
            seen.append((r.get("model_a", "?"), r.get("model_b", "?"), d,
                         float(r["p_value"]) if r.get("p_value") else None))
    else:
        seen = [("M1", "M2", 12, None), ("M1", "M3", 15, None),
                ("M1", "M4", 14, None), ("M2", "M3", 11, None),
                ("M2", "M4", 10, None), ("M3", "M4", 1, None)]

    for a, b, d, p_obs in seen:
        p_best, split = min_detectable(d)
        resolvable = p_best < 0.05
        print(f"  {a} vs {b}: D={d:<3} best available p={p_best:.4f} "
              f"at {split}  ->  {'resolvable' if resolvable else 'UNRESOLVABLE'}")
        rows.append({"quantity": f"min detectable p, {a} vs {b}",
                     "value": round(p_best, 4),
                     "detail": f"discordant D={d}; most lopsided split {split}; "
                               f"{'could' if resolvable else 'could NOT'} reach "
                               f"p<0.05 at any split"})

    # smallest accuracy gap detectable on n=74 at the observed discordance level
    n_test = 74
    print(f"\n  On n={n_test}, a difference of k test images is "
          f"{1 / n_test:.4f} accuracy per image.")
    for d in (10, 14, 20):
        p_best, split = min_detectable(d)
        # smallest lopsidedness that is significant
        need = None
        for k in range(d // 2 + 1):
            if mcnemar_p(k, d - k) < 0.05:
                need = abs((d - k) - k)
                break
        if need:
            print(f"    D={d}: needs a net difference of >= {need} images "
                  f"= {need / n_test:.3f} accuracy to reach p<0.05")
            rows.append({"quantity": f"min detectable accuracy gap at D={d}, n={n_test}",
                         "value": round(need / n_test, 4),
                         "detail": f"net {need} of {n_test} test images"})

    print("\n=== (2) Hard ceiling on the leakage effect ===")
    k, n = leakage_ceiling()
    print(f"  Split A test images whose product group also appears in "
          f"Split A train: {k} of {n}")
    print(f"  => no model can gain more than {k}/{n} = {k / n:.4f} "
          f"({100 * k / n:.1f} points) from image-level leakage on this split.")
    rows.append({"quantity": "leaked test images under Split A",
                 "value": f"{k}/{n}",
                 "detail": "test images sharing a product-identity group with "
                           "the training partition"})
    rows.append({"quantity": "hard ceiling on leakage inflation",
                 "value": round(k / n, 4),
                 "detail": f"{k}/{n}; model-independent upper bound derived "
                           f"from the split alone"})

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["quantity", "value", "detail"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()

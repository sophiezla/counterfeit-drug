"""
Split E evaluation — external counterfeit recall, from persisted checkpoints.

WHAT THIS MEASURES, AND WHAT IT DOES NOT
----------------------------------------
Table 8 lists "counterfeit recall under acquisition shift" as *not measured*,
because Splits C and D are authentic-only by construction and every external
number in the paper is therefore a specificity. Split E is the complement: 28
photographs of products that FDA and WHO alerts confirm as falsified, so the
only quantity it can produce is **external counterfeit recall** — the rate at
which confirmed-falsified products are called counterfeit. It is not an
accuracy, and the Section V-A terminology rule applies to it exactly as it
applies to Splits C and D.

A recall figure read on its own is uninterpretable, and the paper already says
why: a degenerate classifier calling every image counterfeit scores 1.000 here
and 0.000 on Splits C and D. So this script prints Split E beside the Split C
and D specificities from external_from_checkpoints.csv and refuses to report
one without the other. The pair is the finding; neither half is.

FOUR THINGS THIS SET IS NOT
---------------------------
 1. It is NOT an acquisition-shift test. Step 26 measures Split E at brightness
    0.567 and median short side 330 px, against the training pool's 0.668 and
    225 px — close on both axes, and nothing like Split C (0.162, 2448 px) or
    Split D (0.389, 2419 px). Split E shifts the product, the source and the
    photographer; it does not meaningfully shift the acquisition statistics
    this paper is about. A Split E result therefore cannot be substituted for
    the missing acquisition-shifted recall measurement, and Table 8's row
    should be narrowed rather than deleted.
 2. It is NOT a balanced external test. Its authentic class was discarded by
    the eligibility screen (step 25) because the manifest's authentic-labelled
    images are flat carton artwork while its falsified ones are photographs —
    a deterministic class-acquisition confound of the species this paper
    documents. Building a two-class Split E from that manifest would have
    reproduced the paper's own headline defect inside its own external set.
 3. It is NOT 28 independent products. The 28 images come from 8 regulatory
    cases, so a naive binomial interval on n=28 overstates precision. This
    script reports a case-clustered bootstrap interval alongside the Wilson
    interval, and the clustered one is the one to quote.
 4. It is NOT redistributable in full. 9 of the 28 are FDA public domain; 19
    are WHO-hosted and metadata-only. The bytes live under data/raw, which is
    gitignored; the manifest and scripts/24 regenerate them.

Output: modeling/results/split_e_eval.csv
        modeling/results/predictions/<model>__split_e.csv
"""
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, set_seed, SEED, RAW  # noqa: E402
from result_io import load_chosen_lr  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "modeling" / "results"
PROVENANCE = ROOT / "data" / "metadata" / "split_e_candidate_provenance.csv"
EXTERNAL_CD = RESULTS / "external_from_checkpoints.csv"
OUT = RESULTS / "split_e_eval.csv"

N_BOOTSTRAP = 10000
BOOTSTRAP_SEED = 42

FIELDS = ["model", "n", "n_cases", "correct", "external_counterfeit_recall",
          "wilson_lo", "wilson_hi", "cluster_boot_lo", "cluster_boot_hi",
          "split_c_specificity", "split_d_specificity"]


def wilson(k, n, z=1.959963985):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def cluster_bootstrap(correct_by_case, n_boot=N_BOOTSTRAP, seed=BOOTSTRAP_SEED):
    """Percentile interval resampling whole regulatory cases with replacement.

    The unit of independence here is the case, not the image: several images of
    one seizure of one product share lighting, camera and packaging, so they
    carry far less than one image's worth of information each. Resampling cases
    rather than images is what makes the interval honest about n_cases=8.
    """
    rng = np.random.default_rng(seed)
    cases = list(correct_by_case)
    draws = np.empty(n_boot)
    for b in range(n_boot):
        picked = rng.choice(len(cases), size=len(cases), replace=True)
        hits = sum(correct_by_case[cases[i]][0] for i in picked)
        total = sum(correct_by_case[cases[i]][1] for i in picked)
        draws[b] = hits / total
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def split_e_examples():
    rows = list(csv.DictReader(open(PROVENANCE, newline="", encoding="utf-8")))
    return [{"image_id": r["image_id"], "path": RAW / r["orig_relpath"],
             "label": 1,  # counterfeit is the positive class (common.py)
             "split": "split_e", "product_identity": r["product_identity"],
             "case_id": r["case_id"], "cv_fold": None} for r in rows]


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


def external_cd_reference():
    """Split C and D specificities for the same checkpoints, so Split E is never
    printed on its own. Absent file is not fatal, but it is called out."""
    ref = {}
    if not EXTERNAL_CD.exists():
        return ref
    for r in csv.DictReader(open(EXTERNAL_CD, newline="", encoding="utf-8")):
        ref.setdefault(r["model"], {})[r["split"]] = round(float(r["accuracy"]), 4)
    return ref


def main():
    examples = split_e_examples()
    cases = sorted({e["case_id"] for e in examples})
    print(f"Split E: {len(examples)} images from {len(cases)} regulatory cases "
          f"(falsified-only)\n")

    ref = external_cd_reference()
    if not ref:
        print(f"WARNING: {EXTERNAL_CD.name} not found. Split E recall is not "
              f"interpretable without the Split C/D specificities; run "
              f"modeling/eval_external_from_checkpoints.py.\n")

    rows = list(csv.DictReader(open(OUT, newline="", encoding="utf-8"))) \
        if OUT.exists() else []
    done = {r["model"] for r in rows}

    for name, fn in MODELS:
        if name in done:
            print(f"=== skip (done): {name} ===")
            continue
        print(f"=== {name} on Split E ===", flush=True)
        try:
            prob = fn(examples)
        except FileNotFoundError as exc:
            print(f"    SKIPPED: {exc}")
            continue

        called_counterfeit = np.array(prob) >= 0.5
        k = int(called_counterfeit.sum())
        n = len(examples)
        recall = k / n
        w_lo, w_hi = wilson(k, n)

        by_case = {}
        for e, hit in zip(examples, called_counterfeit):
            h, t = by_case.get(e["case_id"], (0, 0))
            by_case[e["case_id"]] = (h + int(hit), t + 1)
        b_lo, b_hi = cluster_bootstrap(by_case)

        cd = ref.get(name, {})
        print(f"    external counterfeit recall {k}/{n} = {recall:.3f}")
        print(f"      Wilson (image-level, optimistic): [{w_lo:.3f}, {w_hi:.3f}]")
        print(f"      case-clustered bootstrap (quote this): [{b_lo:.3f}, {b_hi:.3f}]")
        print(f"      alongside: Split C specificity {cd.get('split_c', 'n/a')}, "
              f"Split D specificity {cd.get('split_d', 'n/a')}", flush=True)

        rows.append({
            "model": name, "n": n, "n_cases": len(cases), "correct": k,
            "external_counterfeit_recall": round(recall, 4),
            "wilson_lo": round(w_lo, 4), "wilson_hi": round(w_hi, 4),
            "cluster_boot_lo": round(b_lo, 4), "cluster_boot_hi": round(b_hi, 4),
            "split_c_specificity": cd.get("split_c", ""),
            "split_d_specificity": cd.get("split_d", ""),
        })

        pdir = RESULTS / "predictions"
        pdir.mkdir(parents=True, exist_ok=True)
        with open(pdir / f"{name}__split_e.csv", "w", newline="",
                  encoding="utf-8") as pf:
            pw = csv.DictWriter(pf, fieldnames=["image_id", "case_id",
                                                "y_true", "y_prob"])
            pw.writeheader()
            for e, p in zip(examples, prob):
                pw.writerow({"image_id": e["image_id"], "case_id": e["case_id"],
                             "y_true": e["label"], "y_prob": p})

        with open(OUT, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)

    print(f"\nwrote {OUT.name}")
    print(f"\n{'model':<38} {'E recall':>9} {'C spec':>8} {'D spec':>8}")
    for r in rows:
        # Not `x or '-'`: a specificity of 0.0 is falsy, and 0.0 is precisely
        # the value that identifies the degenerate all-counterfeit classifier
        # this table exists to expose. Printing it as a missing value would
        # hide the finding.
        def cell(x):
            return "-" if x in ("", None) else f"{float(x):.4g}"
        print(f"{r['model']:<38} {r['external_counterfeit_recall']:>9} "
              f"{cell(r['split_c_specificity']):>8} "
              f"{cell(r['split_d_specificity']):>8}")
    print("\nRead the three columns together. Split E alone cannot distinguish a "
          "model applying\na real decision rule from one that has shifted its "
          "operating point toward counterfeit;\nthe C and D specificities are "
          "what bound that.")


if __name__ == "__main__":
    main()

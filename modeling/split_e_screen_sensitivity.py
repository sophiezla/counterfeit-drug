"""
Does the Split E eligibility screen drive the Split E result?

The screen (step 25) removes 52 of 202 candidates on judgements a single
reviewer made by looking at each frame, and several of the exclusion codes
correlate with the class -- X_BANNER_COMPOSITE and X_NOT_PHOTOGRAPH by
construction, since only the falsified class carries alert banners and only the
authentic class is carton artwork. A reviewer is entitled to ask whether the
reported recall is a property of the models or of the screen.

This script answers that by scoring every FALSIFIED-labelled candidate once,
then re-reading the same predictions under different screen settings. If the
recall moves a lot between settings, the screen is doing the work and the result
should not be reported; if it barely moves, the screen is removing noise rather
than manufacturing a number.

Settings, from strictest to loosest:

  S1  Split E minus every multi-panel montage and label crop -- only single,
      whole-product photographs.
  S2  Split E minus multi-panel montages.
  S0  Split E as built (the reported set).
  S3  Split E plus the banner composites the screen removed.
  S4  every FALSIFIED-labelled candidate, including the ones excluded as
      not-a-product (the WHO logo, the laboratory TLC plates) and the rendered
      tables. This is the "no screen at all" bound.

Output: modeling/results/split_e_screen_sensitivity.csv
"""
import csv
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, set_seed, SEED, RAW  # noqa: E402
from result_io import load_chosen_lr, load_checkpoint  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "data" / "metadata"
RESULTS = ROOT / "modeling" / "results"
OUT = RESULTS / "split_e_screen_sensitivity.csv"

REVIEWS = [META / "split_e_eligibility_review.csv",
           META / "split_e_harvest_eligibility_review.csv"]
LOGS = [META / "split_e_download_log.csv",
        META / "split_e_harvest_download_log.csv"]
PROVENANCE = META / "split_e_candidate_provenance.csv"

N_BOOTSTRAP = 10000


def load_csv(path, key=None):
    rows = list(csv.DictReader(open(path, newline="", encoding="utf-8-sig")))
    return {r[key]: r for r in rows} if key else rows


def cluster_bootstrap(by_case, seed=42, n_boot=N_BOOTSTRAP):
    rng = np.random.default_rng(seed)
    cases = list(by_case)
    draws = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.choice(len(cases), len(cases), replace=True)
        hits = sum(by_case[cases[i]][0] for i in pick)
        tot = sum(by_case[cases[i]][1] for i in pick)
        draws[b] = hits / tot
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def eval_model1(ex):
    from train_model1_classical import extract_histogram
    from sklearn.linear_model import LogisticRegression
    tr = [e for e in load_examples("split_b") if e["split"] == "train"]
    X = np.stack([extract_histogram(e["path"]) for e in tr])
    y = np.array([e["label"] for e in tr])
    set_seed(SEED)
    clf = LogisticRegression(max_iter=2000, class_weight="balanced",
                             random_state=SEED).fit(X, y)
    return clf.predict_proba(np.stack([extract_histogram(e["path"]) for e in ex]))[:, 1]


def eval_model2(ex):
    from train_model2_cnn import SmallCNN
    from torch_utils import evaluate_model
    m = SmallCNN()
    load_checkpoint(m, "model2_smallcnn_gap", "split_b_final",
                    expected_lr=load_chosen_lr("model2_smallcnn_gap"))
    m.eval()
    return np.array(evaluate_model(m, ex)[2])


def eval_frozen(module, ex):
    import importlib
    from torch_utils import evaluate_model_on_features
    mod = importlib.import_module(module)
    head = mod.build_head()
    load_checkpoint(head, mod.MODEL_NAME, "split_b_final",
                    expected_lr=load_chosen_lr(mod.MODEL_NAME))
    head.eval()
    X, y, ids = mod.get_features(ex, train=False, k_augment=1)
    return np.array(evaluate_model_on_features(head, X, y, ids)[2])


MODELS = [
    ("model1_classical_colorhist_logreg", eval_model1),
    ("model2_smallcnn_gap", eval_model2),
    ("model3_mobilenetv3small_frozen", lambda e: eval_frozen("train_model3_mobilenet", e)),
    ("model4_efficientnetb0_frozen", lambda e: eval_frozen("train_model4_efficientnet", e)),
]


def main():
    review = {}
    for p in REVIEWS:
        review.update(load_csv(p, key="image_id"))
    log = {}
    for p in LOGS:
        key = "candidate_id" if "harvest" in p.name else "image_id"
        for iid, r in load_csv(p, key=key).items():
            if r.get("stored_relpath") and r.get("status", "kept") != "dropped":
                log[iid] = {"path": RAW / r["stored_relpath"],
                            "label": r.get("manifest_label", "FALSIFIED"),
                            "case": r.get("case_id") or r.get("alert_url", "")}

    ids = sorted(i for i in log if log[i]["label"] == "FALSIFIED")
    ex = [{"image_id": i, "path": log[i]["path"], "label": 1, "split": "split_e_all",
           "product_identity": log[i]["case"], "cv_fold": None} for i in ids]
    print(f"{len(ex)} FALSIFIED-labelled candidates, "
          f"{len({log[i]['case'] for i in ids})} cases\n")

    in_e = {r["image_id"].removeprefix("split_e_") for r in load_csv(PROVENANCE)}
    panel = {i for i in ids if review[i]["panel_composite"] == "yes"}
    crop = {i for i in ids if review[i].get("label_crop") == "yes"}
    banner = {i for i in ids if review[i]["exclusion_code"] == "X_BANNER_COMPOSITE"}

    SETS = [
        ("S1 whole-product photographs only", (in_e & set(ids)) - panel - crop),
        ("S2 minus multi-panel montages", (in_e & set(ids)) - panel),
        ("S0 Split E as built (reported)", in_e & set(ids)),
        ("S3 plus banner composites", (in_e & set(ids)) | banner),
        ("S4 no screen at all", set(ids)),
    ]

    probs = {}
    for name, fn in MODELS:
        print(f"scoring {name}...", flush=True)
        probs[name] = fn(ex)

    rows = []
    hdr = f"{'condition':<38}{'n':>5}{'cases':>7}" + "".join(
        f"{m.split('_')[0].upper():>20}" for m, _ in MODELS)
    print("\n" + hdr)
    print("-" * len(hdr))
    for label, subset in SETS:
        idx = [k for k, i in enumerate(ids) if i in subset]
        ncase = len({log[ids[k]]["case"] for k in idx})
        cells = []
        for name, _ in MODELS:
            hit = probs[name][idx] >= 0.5
            by_case = {}
            for k, h in zip(idx, hit):
                c = log[ids[k]]["case"]
                a, b = by_case.get(c, (0, 0))
                by_case[c] = (a + int(h), b + 1)
            lo, hi = cluster_bootstrap(by_case)
            cells.append(f"{hit.mean():.3f} [{lo:.2f},{hi:.2f}]".rjust(20))
            rows.append({"condition": label, "model": name, "n": len(idx),
                         "n_cases": ncase, "recall": round(float(hit.mean()), 4),
                         "cluster_boot_lo": round(lo, 4),
                         "cluster_boot_hi": round(hi, 4)})
        print(f"{label:<38}{len(idx):>5}{ncase:>7}" + "".join(cells))

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["condition", "model", "n", "n_cases",
                                          "recall", "cluster_boot_lo",
                                          "cluster_boot_hi"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()

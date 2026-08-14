"""
External evaluation from persisted checkpoints, on both external sets.

This is the first script in the project to consume the checkpoints added on
2026-07-29 rather than retraining, and the difference is the point. Every
previous external evaluation re-derived "the trained model" from scratch, which
cost roughly ten minutes per model, repeatedly exceeded this host's tolerance
for long-running processes, and was the structural cause of the reproducibility
divergences documented in Section 6.5. Loading the recorded weights and running
a forward pass costs seconds, so both external sets can be evaluated for all
four models in a single short run.

It also removes a class of error rather than merely being faster: the model
evaluated externally is now provably the same object that produced the
in-distribution numbers, instead of a re-derivation hoped to be equivalent.

Split C: 150 Mendeley "huawei cn" photographs, brightness 0.162.
Split D: 149 Mendeley "iphone 11 pro" photographs, brightness 0.389 -- same
         products, different camera and lighting protocol. See
         scripts/20_characterise_split_d.py. Both authentic-only, so both
         measure the false-positive rate.

M1 has no checkpoint (it is an sklearn fit, not a torch module) and is refitted
directly; it is cheap and bypasses the normalisation operator by design.

Output: modeling/results/external_from_checkpoints.csv
"""
import csv
from pathlib import Path
import sys

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, set_seed, SEED, RAW
from result_io import load_chosen_lr, checkpoint_path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "modeling" / "results"
OUT = RESULTS / "external_from_checkpoints.csv"
CANDIDATE_PROV = ROOT / "data" / "metadata" / "split_c_candidate_provenance.csv"
SPLIT_D_DIR = ROOT / "data" / "raw" / "mendeley_split_d"


def wilson(k, n, z=1.959963985):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def split_c_examples():
    rows = list(csv.DictReader(open(CANDIDATE_PROV, newline="", encoding="utf-8")))
    return [{"image_id": r["image_id"], "path": RAW / r["orig_relpath"],
             "label": 0, "split": "split_c", "product_identity": r["image_id"],
             "cv_fold": None} for r in rows]


def split_d_examples():
    paths = sorted(p for p in SPLIT_D_DIR.iterdir()
                   if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    return [{"image_id": f"split_d_{p.stem}", "path": p, "label": 0,
             "split": "split_d", "product_identity": p.stem, "cv_fold": None}
            for p in paths]


def eval_model1(sets):
    from train_model1_classical import extract_histogram
    from sklearn.linear_model import LogisticRegression

    train = [e for e in load_examples("split_b") if e["split"] == "train"]
    X = np.stack([extract_histogram(e["path"]) for e in train])
    y = np.array([e["label"] for e in train])
    set_seed(SEED)
    clf = LogisticRegression(max_iter=2000, class_weight="balanced",
                             random_state=SEED).fit(X, y)
    out = {}
    for name, ex in sets.items():
        prob = clf.predict_proba(
            np.stack([extract_histogram(e["path"]) for e in ex]))[:, 1]
        out[name] = int((prob < 0.5).sum()), len(ex), list(map(float, prob)), ex
    return out


def eval_model2(sets):
    from train_model2_cnn import SmallCNN
    from torch_utils import evaluate_model
    from result_io import load_checkpoint

    model = SmallCNN()
    ckpt = load_checkpoint(model, "model2_smallcnn_gap", "split_b_final",
                           expected_lr=load_chosen_lr("model2_smallcnn_gap"))
    print(f"    loaded checkpoint: lr={ckpt['lr']} seed={ckpt['seed']} "
          f"epochs_run={ckpt['epochs_run']}")
    model.eval()
    out = {}
    for name, ex in sets.items():
        _, _, prob = evaluate_model(model, ex)
        out[name] = (int((np.array(prob) < 0.5).sum()), len(ex),
                     list(map(float, prob)), ex)
    return out


def eval_frozen(module_name, sets):
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
    out = {}
    for name, ex in sets.items():
        X, y, ids = mod.get_features(ex, train=False, k_augment=1)
        _, _, prob = evaluate_model_on_features(head, X, y, ids)
        out[name] = (int((np.array(prob) < 0.5).sum()), len(ex),
                     list(map(float, prob)), ex)
    return out


MODELS = [
    ("model1_classical_colorhist_logreg", eval_model1),
    ("model2_smallcnn_gap", eval_model2),
    ("model3_mobilenetv3small_frozen",
     lambda sets: eval_frozen("train_model3_mobilenet", sets)),
    ("model4_efficientnetb0_frozen",
     lambda sets: eval_frozen("train_model4_efficientnet", sets)),
]

FIELDS = ["model", "split", "n", "correct", "accuracy", "ci_lo", "ci_hi"]


def main():
    sets = {"split_c": split_c_examples(), "split_d": split_d_examples()}
    print(f"Split C: {len(sets['split_c'])} images    "
          f"Split D: {len(sets['split_d'])} images\n")

    rows = []
    if OUT.exists():
        rows = list(csv.DictReader(open(OUT, newline="", encoding="utf-8")))
    done = {r["model"] for r in rows}

    for name, fn in MODELS:
        if name in done:
            print(f"=== skip (done): {name} ===")
            continue
        print(f"=== {name} ===", flush=True)
        try:
            res = fn(sets)
        except FileNotFoundError as exc:
            print(f"    SKIPPED: {exc}")
            continue
        for split, (k, n, prob, ex) in res.items():
            lo, hi = wilson(k, n)
            print(f"    {split}: {k}/{n} = {k / n:.3f} [{lo:.3f}, {hi:.3f}]",
                  flush=True)
            rows.append({"model": name, "split": split, "n": n, "correct": k,
                         "accuracy": round(k / n, 4), "ci_lo": round(lo, 4),
                         "ci_hi": round(hi, 4)})
            # Persist per-image scores. Earlier versions computed these and
            # discarded them, which is why external calibration could not be
            # reported without a re-run.
            pdir = OUT.parent / "predictions"
            pdir.mkdir(parents=True, exist_ok=True)
            with open(pdir / f"{name}__{split}.csv", "w", newline="",
                      encoding="utf-8") as pf:
                pw = csv.DictWriter(pf, fieldnames=["image_id", "y_true",
                                                    "y_prob"])
                pw.writeheader()
                for e, p in zip(ex, prob):
                    pw.writerow({"image_id": e["image_id"],
                                 "y_true": e["label"], "y_prob": p})
        with open(OUT, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)

    print(f"\nwrote {OUT.name}")


if __name__ == "__main__":
    main()

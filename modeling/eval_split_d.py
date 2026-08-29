"""
Split D evaluation: a SECOND external distribution, same products, different camera.

Answers the single-external-source objection to Split C. Split C is 150 images
from one camera against one dark backdrop, and this paper itself argues (Section
9.3) that a model can score well on one external set by matching a shortcut
specific to it. If the corrected models' 77-86% on Split C is such an artefact,
a second external distribution should expose it.

Split D is the Mendeley archive's "iphone 11 pro" subset, 149 unique images
(the archive ships one duplicate filename), one per product, covering the SAME
150 products as Split C but photographed on different hardware under the
source's deliberately different lighting protocol. Measured acquisition
statistics (scripts/20_characterise_split_d.py):

    Kaggle training pool   brightness 0.668   median short side  225 px
    Split C (huawei cn)    brightness 0.162   median short side 2448 px
    Split D (iphone 11pro) brightness 0.389   median short side 2419 px

So Split D sits between the training pool and Split C on the axis this paper
identifies as confounded -- a different point on the same axis rather than a
repeat of Split C. Rotation-canonical pHash finds only 1/149 within the
near-duplicate threshold of any Split C image (median distance 18), so despite
depicting the same products the two sets are not pixel-interchangeable.

What this is NOT: an independent second product sample. Content is held fixed
and only acquisition varies, which makes it a paired capture-shift test. For a
paper about acquisition confounding that is the sharper experiment, but it
cannot speak to generalisation across products.

Authentic-only, like Split C, so this measures specificity (counterfeit is
the positive class, so accuracy here is the true-negative rate).

Output: modeling/results/split_d_eval.csv
"""
import csv
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_examples, set_seed, SEED
from result_io import load_chosen_lr

ROOT = Path(__file__).resolve().parent.parent
SPLIT_D_DIR = ROOT / "data" / "raw" / "mendeley_split_d"
RESULTS_DIR = ROOT / "modeling" / "results"
OUT_PATH = RESULTS_DIR / "split_d_eval.csv"

FIELDNAMES = ["model", "split_d_authentic_acc", "split_d_n",
              "split_d_ci_lo", "split_d_ci_hi", "split_c_authentic_acc"]


def wilson(k, n, z=1.959963985):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def load_split_d_examples():
    paths = sorted(p for p in SPLIT_D_DIR.iterdir()
                   if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    return [{"image_id": f"split_d_{p.stem}", "path": p, "label": 0,
             "split": "split_d", "product_identity": p.stem, "cv_fold": None}
            for p in paths]


def split_c_reference(model_name):
    path = RESULTS_DIR / "split_c_eval.csv"
    if not path.exists():
        return ""
    for r in csv.DictReader(open(path, newline="", encoding="utf-8")):
        if r["model"] == model_name:
            return round(float(r["split_c_authentic_acc"]), 4)
    return ""


def eval_model1():
    from train_model1_classical import extract_histogram
    from sklearn.linear_model import LogisticRegression

    examples = load_examples("split_b")
    train_examples = [e for e in examples if e["split"] == "train"]
    X_train = np.stack([extract_histogram(e["path"]) for e in train_examples])
    y_train = np.array([e["label"] for e in train_examples])
    set_seed(SEED)
    clf = LogisticRegression(max_iter=2000, class_weight="balanced",
                             random_state=SEED)
    clf.fit(X_train, y_train)

    d = load_split_d_examples()
    y_prob = clf.predict_proba(np.stack([extract_histogram(e["path"]) for e in d]))[:, 1]
    return float((y_prob < 0.5).mean()), len(d)


def eval_model2():
    from train_model2_cnn import SmallCNN
    from torch_utils import train_model, evaluate_model

    examples = load_examples("split_b")
    train_examples = [e for e in examples if e["split"] == "train"]
    val_examples = [e for e in examples if e["split"] == "val"]
    lr = load_chosen_lr("model2_smallcnn_gap")

    set_seed(SEED)
    model = SmallCNN()
    model, _ = train_model(model, train_examples, val_examples, lr,
                           model_tag="model2_smallcnn_gap",
                           run_tag="split_d_eval_rebuild")

    d = load_split_d_examples()
    _, _, y_prob = evaluate_model(model, d)
    return float(np.mean(np.array(y_prob) < 0.5)), len(d)


def eval_frozen_backbone_model(module_name):
    import importlib
    mod = importlib.import_module(module_name)
    from torch_utils import train_model_on_features, evaluate_model_on_features

    examples = load_examples("split_b")
    train_examples = [e for e in examples if e["split"] == "train"]
    val_examples = [e for e in examples if e["split"] == "val"]
    X_train, y_train, _ = mod.get_features(train_examples, train=True, k_augment=3)
    X_val, y_val, _ = mod.get_features(val_examples, train=False, k_augment=1)
    lr = load_chosen_lr(mod.MODEL_NAME)

    set_seed(SEED)
    head = mod.build_head()
    head, _ = train_model_on_features(head, X_train, y_train, X_val, y_val, lr,
                                     model_tag=mod.MODEL_NAME,
                                     run_tag="split_d_eval_rebuild")

    d = load_split_d_examples()
    X_d, y_d, ids_d = mod.get_features(d, train=False, k_augment=1)
    _, _, y_prob = evaluate_model_on_features(head, X_d, y_d, ids_d)
    return float(np.mean(np.array(y_prob) < 0.5)), len(d)


MODELS = [
    ("model1", "model1_classical_colorhist_logreg", eval_model1),
    ("model2", "model2_smallcnn_gap", eval_model2),
    ("model3", "model3_mobilenetv3small_frozen",
     lambda: eval_frozen_backbone_model("train_model3_mobilenet")),
    ("model4", "model4_efficientnetb0_frozen",
     lambda: eval_frozen_backbone_model("train_model4_efficientnet")),
]


def load_done():
    if not OUT_PATH.exists():
        return {}, []
    rows = list(csv.DictReader(open(OUT_PATH, newline="", encoding="utf-8")))
    return {r["model"] for r in rows}, rows


def write_all(rows):
    with open(OUT_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows)


def main():
    done, rows = load_done()
    if done:
        print(f"resuming; {len(done)} model(s) already evaluated")

    for _key, name, fn in MODELS:
        if name in done:
            print(f"=== skip (done): {name} ===")
            continue
        print(f"=== {name} on Split D ===", flush=True)
        acc, n = fn()
        k = int(round(acc * n))
        lo, hi = wilson(k, n)
        print(f"  Split D authentic accuracy {k}/{n} = {acc:.3f} "
              f"[{lo:.3f}, {hi:.3f}]", flush=True)
        rows.append({"model": name, "split_d_authentic_acc": round(acc, 4),
                     "split_d_n": n, "split_d_ci_lo": round(lo, 4),
                     "split_d_ci_hi": round(hi, 4),
                     "split_c_authentic_acc": split_c_reference(name)})
        write_all(rows)   # checkpoint after every model

    print(f"\nWrote {OUT_PATH}")
    for r in rows:
        print(f"  {r['model']:<38} D={r['split_d_authentic_acc']}  "
              f"C={r['split_c_authentic_acc']}")


if __name__ == "__main__":
    main()

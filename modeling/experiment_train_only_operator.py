"""
The operator a train-only audit nominates, run for all three models.

Gap this closes. The three normalization axes of Eq. (8) were chosen after
Table 4 showed those statistics separating the training pool from Split C,
which makes Split C target-informed development data for that experiment
(Sections V-D, VI-C, VIII). Section S-I-S removes the dependency in principle:
applying the audit inside the Split B *training partition alone*, under a
threshold declared in advance (0.650), nominates resolution, brightness and
compression -- the three actually used -- plus aspect ratio, which the square
224x224 input resize already removes, and gray-world colour balance, which
fires marginally at 0.684.

What was missing is the other half of that argument. Section S-I-S shows the
axes are *derivable* without target knowledge; it does not report what a
practitioner following the rule would have *obtained*, because the operator it
nominates is not the operator the paper reports. The nominated operator
includes colour balance. Running it closes the gap: it is a result with no
target information anywhere in its construction, for which Split C is an
untouched external set.

Conditions, per model, in one execution so the comparison is within-run:

    RBC     resolution -> brightness -> compression, the reported operator
    RBWC    resolution -> brightness -> white balance -> compression, the
            operator the train-only rule of Section S-I-S nominates

Colour balance is composed with brightness and before the compression
bottleneck, as a photometric channel scaling, which is the placement
experiment_colorbalance_norm.py established. That script already ran both
conditions for M4 (0.820 and 0.780 on Split C); this one covers M2 and M3 as
well and adds Split D, so the train-only arm is complete across the roster and
both external sets.

Expect the nominated operator to be somewhat worse than the reported one:
Section S-I-N ruled colour balance out on the evidence that it recovers 0.067
alone and costs points in combination. That is the point. The question is not
whether the train-only rule finds the best operator -- it does not -- but
whether the recovery survives when no target information is used at all.

Every condition appends its row immediately and a re-run skips what is already
recorded, so a killed process loses at most one condition.

    python modeling/experiment_train_only_operator.py

Output: modeling/results/train_only_operator_experiment.csv
"""
import csv
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (load_examples, build_transform, set_seed, SEED,   # noqa: E402
                    IMG_SIZE)
from eval_external_from_checkpoints import (split_c_examples,          # noqa: E402
                                            split_d_examples)
from experiment_colorbalance_norm import normalize_color_balance      # noqa: E402
from normalization import (normalize_resolution, normalize_brightness, # noqa: E402
                           normalize_compression)
from result_io import load_chosen_lr                                   # noqa: E402
from torch_utils import (_run_training_loop, train_model_on_features,  # noqa: E402
                         evaluate_model_on_features, BATCH_SIZE,
                         compute_class_weights)

from torch.utils.data import Dataset, DataLoader                       # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "modeling" / "results" / "train_only_operator_experiment.csv"

OPS = {
    "R": normalize_resolution,
    "B": normalize_brightness,
    "W": normalize_color_balance,
    "C": normalize_compression,
}

CONDITIONS = [
    ("reported operator (R->B->C)", "RBC"),
    ("train-only nominated (R->B->W->C)", "RBWC"),
]

MODELS = ["model2_smallcnn_gap", "model3_mobilenetv3small_frozen",
          "model4_efficientnetb0_frozen"]

FIELDS = ["model", "condition", "operators", "split_b_test_acc",
          "split_c_k", "split_c_n", "split_c_spec",
          "split_d_k", "split_d_n", "split_d_spec"]


def make_preprocess(sequence):
    def preprocess(im):
        im = im.convert("RGB")
        for key in sequence:
            im = OPS[key](im)
        return im
    return preprocess


class OperatorDataset(Dataset):
    """PharmaImageDataset with an arbitrary operator sequence in place of the
    production three-way normalization."""

    def __init__(self, examples, train, preprocess):
        self.examples = examples
        self.transform = build_transform(train)
        self.preprocess = preprocess

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        ex = self.examples[idx]
        with Image.open(ex["path"]) as im:
            img = self.transform(self.preprocess(im))
        return img, ex["label"], ex["image_id"]


def _loader(examples, train, preprocess):
    g = torch.Generator()
    g.manual_seed(SEED)
    return DataLoader(OperatorDataset(examples, train, preprocess),
                      batch_size=BATCH_SIZE, shuffle=train,
                      generator=g if train else None, num_workers=0)


@torch.no_grad()
def _specificity(model, examples, preprocess):
    """Fraction of authentic-only images called authentic."""
    model.eval()
    k, n = 0, 0
    for x, _, _ in _loader(examples, False, preprocess):
        prob_counterfeit = torch.softmax(model(x), dim=1)[:, 1]
        k += int((prob_counterfeit < 0.5).sum())
        n += x.shape[0]
    return k, n


def run_model2(by, ext, preprocess, run_tag):
    from train_model2_cnn import SmallCNN, MODEL_NAME

    set_seed(SEED)
    model = SmallCNN()
    model, _ = _run_training_loop(
        model, _loader(by["train"], True, preprocess),
        _loader(by["val"], False, preprocess),
        load_chosen_lr(MODEL_NAME), compute_class_weights(by["train"]),
        MODEL_NAME, run_tag, 50, 4, has_ids=True)

    k, n = 0, 0
    for x, y, _ in _loader(by["test"], False, preprocess):
        pred = torch.softmax(model(x), dim=1)[:, 1] >= 0.5
        k += int((pred == y.bool()).sum())
        n += x.shape[0]
    return k / n, [_specificity(model, e, preprocess) for e in ext]


def run_frozen(module_name, by, ext, preprocess, run_tag):
    import importlib
    from torchvision import transforms
    from common import IMAGENET_MEAN, IMAGENET_STD

    mod = importlib.import_module(module_name)
    fe, gap = mod.build_backbone()
    fe.eval()          # BatchNorm backbones; the defect of Section S-I-G

    def build_tf(train):
        if train:
            ops = [transforms.Resize((IMG_SIZE, IMG_SIZE)),
                   transforms.RandomRotation(degrees=12),
                   transforms.ColorJitter(brightness=0.25, contrast=0.25),
                   transforms.RandomResizedCrop(IMG_SIZE, scale=(0.85, 1.0)),
                   transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 0.8))]
        else:
            ops = [transforms.Resize((IMG_SIZE, IMG_SIZE))]
        return transforms.Compose(ops + [transforms.ToTensor(),
                                         transforms.Normalize(IMAGENET_MEAN,
                                                              IMAGENET_STD)])

    @torch.no_grad()
    def extract(examples, train, k_augment):
        Xs, ys = [], []
        tf = build_tf(train)
        for pass_idx in range(k_augment):
            set_seed(SEED + pass_idx)          # Section S-I-G, defect 1
            for start in range(0, len(examples), 32):
                batch = examples[start:start + 32]
                imgs = []
                for e in batch:
                    with Image.open(e["path"]) as im:
                        imgs.append(tf(preprocess(im)))
                Xs.append(gap(fe(torch.stack(imgs))).flatten(1).numpy())
                ys.extend([e["label"] for e in batch])
        return np.concatenate(Xs, axis=0), np.array(ys)

    X_tr, y_tr = extract(by["train"], True, 3)
    X_va, y_va = extract(by["val"], False, 1)
    X_te, y_te = extract(by["test"], False, 1)

    set_seed(SEED)
    head = mod.build_head()
    head, _ = train_model_on_features(head, X_tr, y_tr, X_va, y_va,
                                      load_chosen_lr(mod.MODEL_NAME),
                                      model_tag=mod.MODEL_NAME, run_tag=run_tag)

    _, y_true, y_prob = evaluate_model_on_features(head, X_te, y_te,
                                                   list(range(len(y_te))))
    b_acc = float(np.mean((np.array(y_prob) >= 0.5) == np.array(y_true)))

    out = []
    for examples in ext:
        X, y = extract(examples, False, 1)
        _, _, prob = evaluate_model_on_features(head, X, y,
                                                list(range(len(y))))
        out.append((int((np.array(prob) < 0.5).sum()), len(y)))
    return b_acc, out


def load_done():
    if not OUT.exists():
        return []
    with open(OUT, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    examples = load_examples("split_b")
    by = {s: [e for e in examples if e["split"] == s]
          for s in ("train", "val", "test")}
    ext = [split_c_examples(), split_d_examples()]

    rows = load_done()
    done = {(r["model"], r["operators"]) for r in rows}

    for model_name in MODELS:
        for label, seq in CONDITIONS:
            if (model_name, seq) in done:
                print(f"skip {model_name} {seq} (already recorded)")
                continue
            print(f"\n=== {model_name}  {label} ===")
            preprocess = make_preprocess(seq)
            tag = f"trainonly_{seq}"
            if model_name == "model2_smallcnn_gap":
                b_acc, spec = run_model2(by, ext, preprocess, tag)
            else:
                module = ("train_model3_mobilenet"
                          if "mobilenet" in model_name
                          else "train_model4_efficientnet")
                b_acc, spec = run_frozen(module, by, ext, preprocess, tag)

            (ck, cn), (dk, dn) = spec
            rows.append({
                "model": model_name, "condition": label, "operators": seq,
                "split_b_test_acc": round(b_acc, 4),
                "split_c_k": ck, "split_c_n": cn,
                "split_c_spec": round(ck / cn, 4),
                "split_d_k": dk, "split_d_n": dn,
                "split_d_spec": round(dk / dn, 4),
            })
            OUT.parent.mkdir(parents=True, exist_ok=True)
            with open(OUT, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=FIELDS)
                w.writeheader()
                w.writerows(rows)
            print(f"  Split B {b_acc:.4f}   Split C {ck}/{cn}={ck/cn:.4f}   "
                  f"Split D {dk}/{dn}={dk/dn:.4f}")

    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

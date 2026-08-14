"""
Shared utilities for all 4 models: data loading, transforms, metrics.

Label convention (fixed across the whole project): authentic=0, counterfeit=1.
Counterfeit is treated as the positive class throughout (precision/recall/F1/
ROC-AUC are all with respect to counterfeit), matching the plan's framing of
counterfeit detection as the task of interest.
"""
import csv
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import Dataset
from torchvision import transforms

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROVENANCE = ROOT / "data" / "metadata" / "provenance.csv"
SPLITS_DIR = ROOT / "splits"
RESULTS_DIR = ROOT / "modeling" / "results"
CHECKPOINTS_DIR = ROOT / "modeling" / "checkpoints"

LABEL_TO_INT = {"authentic": 0, "counterfeit": 1}
INT_TO_LABEL = {v: k for k, v in LABEL_TO_INT.items()}

IMG_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

SEED = 42


def set_seed(seed: int = SEED):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(False)  # some CPU ops lack det. kernels


def load_provenance():
    with open(PROVENANCE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {r["image_id"]: r for r in rows}


def load_examples(split_name: str):
    """
    split_name: 'split_a' or 'split_b'
    Returns list of dicts: image_id, path (absolute), label (int), split
    ('train'/'val'/'test'), product_identity, cv_fold (int or None, only
    meaningful for split_b's train partition).
    """
    prov = load_provenance()
    split_path = SPLITS_DIR / f"{split_name}.csv"
    with open(split_path, newline="", encoding="utf-8") as f:
        split_rows = list(csv.DictReader(f))

    examples = []
    for r in split_rows:
        iid = r["image_id"]
        p = prov[iid]
        cv_fold = r.get("cv_fold", "")
        examples.append({
            "image_id": iid,
            "path": RAW / p["orig_relpath"],
            "label": LABEL_TO_INT[p["class_label"]],
            "split": r["split"],
            "product_identity": p["product_identity"],
            "cv_fold": int(cv_fold) if cv_fold not in ("", None) else None,
        })
    return examples


def build_transform(train: bool):
    if train:
        return transforms.Compose([
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.RandomRotation(degrees=12),               # rotation +/-10-15 deg
            transforms.ColorJitter(brightness=0.25, contrast=0.25),  # brightness/contrast jitter
            transforms.RandomResizedCrop(IMG_SIZE, scale=(0.85, 1.0)),  # mild crop/zoom
            transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 0.8)),   # slight blur
            # NO horizontal/vertical flip: would mirror printed packaging text unnaturally.
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])
    return transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


class PharmaImageDataset(Dataset):
    """
    normalize=True (the default) applies the capture-method-confound
    normalization (modeling/normalization.py: resolution + brightness +
    compression bottlenecks) before the usual train/eval transform. This
    became the project default after Finding 11
    (data/metadata/capture_method_confound_findings.md) showed it improves
    Split C external generalization for Models 2/3/4. Model 1 (classical
    histogram baseline) does not use this class at all -- it reads images
    directly in train_model1_classical.py -- so it is unaffected by this
    default, which is deliberate: normalization collapses Model 1's
    in-distribution accuracy toward chance with no Split C benefit
    (Finding 11), since it has no signal beyond the shortcuts to begin with.
    """
    def __init__(self, examples, train: bool, normalize: bool = True):
        self.examples = examples
        self.transform = build_transform(train)
        self.normalize = normalize

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        ex = self.examples[idx]
        img = Image.open(ex["path"]).convert("RGB")
        if self.normalize:
            from normalization import normalize_capture_confounds
            img = normalize_capture_confounds(img)
        img = self.transform(img)
        return img, ex["label"], ex["image_id"]

"""
One-time feature extraction for frozen-backbone models (3, 4).

Running a full MobileNetV3/EfficientNet-B0 forward pass every epoch on CPU,
just to train a 2-class linear head, is wasted work: the backbone never
updates, so its output for a given input is fixed. We extract pooled
backbone features once per split, then train the head on those cached
vectors (see torch_utils.train_model_on_features) — orders of magnitude
faster, since an "epoch" over cached features involves no image decoding
and no convolution.

To keep some benefit of the plan's augmentation policy (Part 2.7) despite
caching, the TRAIN partition is expanded via K_AUGMENT independently
augmented passes through the backbone (so the head still sees K distinct
augmented views of every training image, just all extracted up front rather
than re-extracted every epoch). VAL/TEST use a single deterministic
(eval-transform) pass, as usual.
"""
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader

from common import PharmaImageDataset, set_seed, SEED

DEVICE = torch.device("cpu")
K_AUGMENT = 3
EXTRACT_BATCH_SIZE = 32


@torch.no_grad()
def extract_features(feature_extractor: torch.nn.Module, gap: torch.nn.Module,
                      examples, train: bool, k_augment: int = 1,
                      batch_size: int = EXTRACT_BATCH_SIZE,
                      normalize: bool = True):
    """
    normalize=False bypasses the three-way capture normalization, i.e. the
    un-normalized baseline condition. It is a parameter so that both conditions
    of a comparison run through this one extraction path instead of through a
    reimplementation of it per experiment script; the default is the production
    behaviour and is unchanged.

    Each augmented pass is seeded with SEED + pass_idx before iterating, so
    the augmented views are reproducible regardless of what RNG-consuming
    code ran earlier in the process. This was previously unseeded, which is
    the root cause identified in Finding 12/13
    (data/metadata/capture_method_confound_findings.md) for Model 3's
    high run-to-run variance under normalization experiments -- with this
    fix, re-running feature extraction for the same examples/split now
    reproduces the same cached features every time, not just within a
    single script invocation.
    """
    feature_extractor.eval()
    feature_extractor = feature_extractor.to(DEVICE)
    gap = gap.to(DEVICE)

    all_X, all_y, all_ids = [], [], []
    for pass_idx in range(k_augment):
        set_seed(SEED + pass_idx)
        ds = PharmaImageDataset(examples, train=train, normalize=normalize)
        loader = DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=0)
        for x, y, ids in loader:
            x = x.to(DEVICE)
            feats = feature_extractor(x)
            feats = gap(feats).flatten(1)
            all_X.append(feats.cpu().numpy())
            all_y.append(y.numpy())
            all_ids.extend(ids)

    X = np.concatenate(all_X, axis=0)
    y = np.concatenate(all_y, axis=0)
    return X, y, all_ids

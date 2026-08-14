"""
Canonical capture-method-confound normalization, promoted from the
standalone experiment scripts (experiment_brightness_norm.py,
experiment_resolution_norm.py, experiment_compression_norm.py) to
production status after Finding 11
(data/metadata/capture_method_confound_findings.md): 3-way normalization
(resolution + brightness + compression) improved Split C external
generalization for 3 of 4 models (Models 2/3/4), including reversing an
earlier regression on Model 3, and was neutral (neither helped nor hurt
Split C, though it does collapse in-distribution accuracy toward chance)
for Model 1.

This module is the single source of truth for the normalization logic; the
experiment scripts that originated each piece are left as-is (historical
record of how each axis was isolated and tested) rather than refactored to
import from here.

Applied identically to train/test/Split C, label-free — a real, deployable
preprocessing step, not something that uses the answer.
"""
import io

import numpy as np
from PIL import Image

RESOLUTION_BOTTLENECK = 128  # short-side px; below Kaggle's own 10th percentile (~287px)
BRIGHTNESS_TARGET = 0.5      # target mean RGB value (0-1 scale)
JPEG_QUALITY = 40            # aggressive; below Kaggle's own images*.jpg typical quality


def normalize_resolution(im: Image.Image) -> Image.Image:
    w, h = im.size
    if min(w, h) <= RESOLUTION_BOTTLENECK:
        return im
    scale = RESOLUTION_BOTTLENECK / min(w, h)
    return im.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.BILINEAR)


def normalize_brightness(im: Image.Image) -> Image.Image:
    arr = np.asarray(im).astype(np.float32) / 255.0
    mean = arr.mean()
    if mean > 1e-6:
        arr = arr * (BRIGHTNESS_TARGET / mean)
    arr = np.clip(arr, 0.0, 1.0)
    return Image.fromarray((arr * 255).astype(np.uint8))


def normalize_compression(im: Image.Image) -> Image.Image:
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="JPEG", quality=JPEG_QUALITY)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def normalize_capture_confounds(im: Image.Image) -> Image.Image:
    """Resolution -> brightness -> compression, in that order (matches
    experiment_compression_norm.py's combined_preprocess ordering)."""
    im = im.convert("RGB")
    im = normalize_resolution(im)
    im = normalize_brightness(im)
    im = normalize_compression(im)
    return im

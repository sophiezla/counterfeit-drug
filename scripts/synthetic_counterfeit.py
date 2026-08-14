"""
Synthetic counterfeit-packaging perturbation pipeline.

Motivation (data/metadata/synthetic_counterfeit_findings.md has the full
writeup): no genuinely independent counterfeit-labeled external dataset
could be found for Split C (see data/README.md "Sources"), so Split C has
been authentic-only throughout this project. Rather than leave Split C
unable to measure counterfeit-class recall at all, this module perturbs
independent, never-before-used authentic photos (the Mendeley "iPhone 11
Pro" subset, see 13_download_mendeley_iphone11pro.py) into synthetic
"counterfeit-style" versions, using degradation modes commonly cited in
pharma anti-counterfeiting literature (print-quality defects, color/ink
mismatch, print misregistration) as a stand-in for real counterfeit visual
cues.

This is explicitly a SYNTHETIC PROXY, analogous to ImageNet-C-style
synthetic corruption benchmarks used in the robustness literature — it
does not claim to measure true counterfeit-detection recall on real
fraudulent products (which may differ in ways not modeled here: security
feature omission, packaging material, barcode/serial errors, etc.). See
the findings doc for the full limitations discussion.

Anti-shortcut design: every perturbation draws its parameters randomly per
image (not fixed constants), and each image gets a randomly-chosen SUBSET
of the available effects, not all of them uniformly — the goal is to avoid
creating a new single, uniform "tell" a model could detect instead of
learning anything resembling a counterfeit-recognition cue (the same
failure mode as the original capture-method confound this project spent
most of its effort removing).

No OpenCV/Tesseract available in this environment -- text-region detection
here is a from-scratch classical-CV approach using only PIL + numpy +
scipy.ndimage (edge-density thresholding + connected-component blob
detection + text-line-shaped aspect-ratio filtering), not OCR. It finds
plausible text/logo regions without reading or understanding the text
itself.
"""
import random

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage


# ---------------------------------------------------------------------
# Text/logo region detection (classical CV, no OCR)
# ---------------------------------------------------------------------

def detect_text_regions(im: Image.Image, max_regions: int = 8):
    """
    Finds candidate text/logo regions via edge-density blobs: text lines
    have many closely-packed high-contrast edges in a wide, short bounding
    box. Returns a list of (top, left, bottom, right) boxes, largest-edge-
    density first, capped at max_regions.
    """
    gray = np.asarray(im.convert("L"), dtype=np.float32)
    h, w = gray.shape

    edges = np.asarray(im.convert("L").filter(ImageFilter.FIND_EDGES), dtype=np.float32)
    edge_mask = edges > (edges.mean() + edges.std())

    # merge nearby edge pixels into blobs representing text lines/logos
    structure = np.ones((5, 15))  # wider than tall: bridges gaps between letters
    dilated = ndimage.binary_dilation(edge_mask, structure=structure, iterations=2)

    labeled, n = ndimage.label(dilated)
    if n == 0:
        return []

    objects = ndimage.find_objects(labeled)
    candidates = []
    for obj in objects:
        if obj is None:
            continue
        y0, y1 = obj[0].start, obj[0].stop
        x0, x1 = obj[1].start, obj[1].stop
        bh, bw = y1 - y0, x1 - x0
        if bh < 8 or bw < 20:
            continue  # too small to be a meaningful text/logo region
        if bh > h * 0.4 or bw > w * 0.9:
            continue  # too large, likely background/product outline, not text
        aspect = bw / max(bh, 1)
        if aspect < 1.2:
            continue  # text lines/logos are wider than tall
        density = edge_mask[y0:y1, x0:x1].mean()
        candidates.append((density, (y0, x0, y1, x1)))

    candidates.sort(key=lambda c: -c[0])
    return [box for _, box in candidates[:max_regions]]


# ---------------------------------------------------------------------
# Text-region tampering (NOT font rendering/OCR — simulates real print
# defects: misregistration ghosting, garbled/scrambled print, ink dropout)
# ---------------------------------------------------------------------

def _tamper_ghost(arr, box, rng):
    """Duplicate the region shifted a few px, alpha-blended -- simulates
    print misregistration/double-strike, a well-documented real defect."""
    y0, x0, y1, x1 = box
    shift = rng.randint(2, 5) * rng.choice([-1, 1])
    region = arr[y0:y1, x0:x1].copy()
    alpha = rng.uniform(0.35, 0.55)
    x0s, x1s = max(0, x0 + shift), min(arr.shape[1], x1 + shift)
    w = x1s - x0s
    if w <= 0:
        return
    src = region[:, :w] if shift > 0 else region[:, -w:]
    arr[y0:y1, x0s:x1s] = (arr[y0:y1, x0s:x1s] * (1 - alpha) + src * alpha)


def _tamper_scramble(arr, box, rng):
    """Shifts 1-2 thin strips within the region by a few px, alpha-blended
    -- simulates slight print jitter/misalignment on a small part of the
    text, not full scrambling (an earlier version reordered many strips
    across the whole region, which read as an obvious digital glitch
    rather than a believable print defect -- toned down after manual
    review, data/metadata/synthetic_counterfeit_findings.md)."""
    y0, x0, y1, x1 = box
    width = x1 - x0
    strip_w = max(3, width // 12)
    n_strips = max(1, width // strip_w)
    n_shift = rng.randint(1, 2)
    for _ in range(n_shift):
        i = rng.randint(0, n_strips - 1)
        sx0 = x0 + i * strip_w
        sx1 = min(x1, sx0 + strip_w)
        if sx1 <= sx0:
            continue
        shift = rng.randint(1, 3) * rng.choice([-1, 1])
        tx0, tx1 = max(x0, sx0 + shift), min(x1, sx1 + shift)
        w = min(sx1 - sx0, tx1 - tx0)
        if w <= 0:
            continue
        strip = arr[y0:y1, sx0:sx0 + w].copy()
        alpha = rng.uniform(0.5, 0.75)
        arr[y0:y1, tx0:tx0 + w] = arr[y0:y1, tx0:tx0 + w] * (1 - alpha) + strip * alpha


def _tamper_dropout(arr, box, rng):
    """Lighten random patches within the region -- simulates faded/
    incomplete ink coverage from a low-quality print run."""
    y0, x0, y1, x1 = box
    h, w = y1 - y0, x1 - x0
    n_patches = rng.randint(1, 3)
    for _ in range(n_patches):
        ph, pw = rng.randint(h // 4, max(h // 2, h // 4 + 1)), rng.randint(w // 6, max(w // 3, w // 6 + 1))
        py = y0 + rng.randint(0, max(1, h - ph))
        px = x0 + rng.randint(0, max(1, w - pw))
        fade = rng.uniform(0.3, 0.6)
        arr[py:py + ph, px:px + pw] = arr[py:py + ph, px:px + pw] * (1 - fade) + 255 * fade


TEXT_TAMPER_OPS = [_tamper_ghost, _tamper_scramble, _tamper_dropout]


def apply_text_tampering(im: Image.Image, rng: random.Random) -> Image.Image:
    im = im.convert("RGB")
    arr = np.asarray(im, dtype=np.float32).copy()
    regions = detect_text_regions(im)
    if not regions:
        return im
    n_affect = rng.randint(1, max(1, len(regions) // 2 + 1))
    chosen = rng.sample(regions, min(n_affect, len(regions)))
    for box in chosen:
        op = rng.choice(TEXT_TAMPER_OPS)
        op(arr, box, rng)
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


# ---------------------------------------------------------------------
# Whole-image photographic defects
# ---------------------------------------------------------------------

def apply_color_shift(im: Image.Image, rng: random.Random) -> Image.Image:
    """Per-channel intensity scaling -- mimics ink/pigment mismatch. Each
    channel's factor is sampled away from 1.0 by at least 0.15 (two-sided)
    so the shift always produces a visible tint, rather than allowing a
    near-1.0 draw that nets out imperceptible (the bug that made ~13% of
    the first full batch too subtle to see -- data/metadata/
    synthetic_counterfeit_findings.md)."""
    arr = np.asarray(im.convert("RGB"), dtype=np.float32)
    for c in range(3):
        factor = 1.0 + rng.uniform(0.15, 0.4) * rng.choice([-1, 1])
        arr[:, :, c] = np.clip(arr[:, :, c] * factor, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def apply_halftone(im: Image.Image, rng: random.Random) -> Image.Image:
    """Overlays a faint dot-grid pattern to mimic cheap offset-print
    halftone screening, a common visual tell of low-quality counterfeit
    packaging print. Dot spacing is scaled to image size (not a fixed
    small px count) so the pattern survives downscaling to a normal
    browser-review display size instead of aliasing away to nothing."""
    w, h = im.size
    spacing = max(6, min(w, h) // 120)
    strength = rng.uniform(0.18, 0.32)
    yy, xx = np.mgrid[0:h, 0:w]
    dot_pattern = ((xx % spacing < spacing // 2) & (yy % spacing < spacing // 2)).astype(np.float32)
    arr = np.asarray(im.convert("RGB"), dtype=np.float32)
    for c in range(3):
        arr[:, :, c] = arr[:, :, c] * (1 - strength * dot_pattern)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def apply_registration_warp(im: Image.Image, rng: random.Random) -> Image.Image:
    """Per-channel pixel offset -- mimics color-plate misregistration
    (the colored "fringing" seen on poorly-printed packaging)."""
    arr = np.asarray(im.convert("RGB"), dtype=np.float32)
    out = arr.copy()
    for c in range(3):
        dx, dy = rng.randint(-6, 6), rng.randint(-6, 6)
        out[:, :, c] = np.roll(np.roll(arr[:, :, c], dy, axis=0), dx, axis=1)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def apply_blur(im: Image.Image, rng: random.Random) -> Image.Image:
    radius = rng.uniform(1.4, 3.2)
    return im.filter(ImageFilter.GaussianBlur(radius=radius))


def apply_contrast_reduction(im: Image.Image, rng: random.Random) -> Image.Image:
    arr = np.asarray(im.convert("RGB"), dtype=np.float32)
    factor = rng.uniform(0.4, 0.65)
    mean = arr.mean()
    arr = (arr - mean) * factor + mean
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


PHOTOGRAPHIC_OPS = [apply_color_shift, apply_halftone, apply_registration_warp,
                    apply_blur, apply_contrast_reduction]


def generate_synthetic_counterfeit(im: Image.Image, seed: int, include_text_tamper: bool) -> Image.Image:
    """
    Applies text-region tampering (if enabled) plus a randomly-chosen
    subset of the photographic defects, all parameterized by `seed` for
    full reproducibility. Order: text tampering first (works on cleaner
    pixels), then photographic defects (so blur/halftone also soften the
    text-tamper edits, avoiding an obvious "this exact patch was edited"
    seam).

    Severity ranges and effect count were increased after a full-batch
    review found ~13% of images landed on weak random draws that were
    nearly imperceptible (mean per-pixel diff <5/255) -- randomization for
    anti-shortcut diversity is still in the exact combination and
    parameters chosen, but every image is now guaranteed at least 3 of the
    5 photographic effects at a strength high enough to survive
    downscaling to a normal browser-review display size, not just
    detectable via pixel-difference math on the full-resolution original.
    """
    rng = random.Random(seed)
    im = im.convert("RGB")

    if include_text_tamper:
        im = apply_text_tampering(im, rng)

    n_effects = rng.randint(3, 5)
    chosen_ops = rng.sample(PHOTOGRAPHIC_OPS, n_effects)
    for op in chosen_ops:
        im = op(im, rng)

    return im

"""
Step 14 (preview) — Generate a small side-by-side preview grid so the user
can judge the quality of the text-region tampering approach
(scripts/synthetic_counterfeit.py) before committing to full-scale
generation. NOT the final generation script (see
15_generate_synthetic_counterfeit.py for that, run only after this preview
is approved).

For a sample of base images (iPhone 11 Pro subset), builds one row per
image: [original | photographic-defects-only | photographic+text-tamper],
labeled, so the specific effect of text tampering can be judged in
isolation from the other photographic defects.

Output: data/metadata/synthetic_counterfeit_preview/preview_grid.png
"""
import random
from pathlib import Path

from PIL import Image, ImageDraw

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from synthetic_counterfeit import generate_synthetic_counterfeit

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "data" / "raw" / "mendeley_split_c"
OUT_DIR = ROOT / "data" / "metadata" / "synthetic_counterfeit_preview"
OUT_DIR.mkdir(parents=True, exist_ok=True)

N_SAMPLES = 12
THUMB = 260
LABEL_H = 22


def make_cell(im, label):
    cell = Image.new("RGB", (THUMB, THUMB + LABEL_H), "white")
    im2 = im.copy()
    im2.thumbnail((THUMB, THUMB))
    x, y = (THUMB - im2.width) // 2, (THUMB - im2.height) // 2
    cell.paste(im2, (x, y))
    d = ImageDraw.Draw(cell)
    d.rectangle([0, THUMB, THUMB, THUMB + LABEL_H], fill="black")
    d.text((4, THUMB + 3), label, fill="white")
    return cell


def main():
    random.seed(777)
    files = sorted(SRC_DIR.glob("*.jpg"))
    sample = random.sample(files, min(N_SAMPLES, len(files)))

    cols = 3
    grid = Image.new("RGB", (cols * THUMB, len(sample) * (THUMB + LABEL_H)), "white")

    for row, path in enumerate(sample):
        with Image.open(path) as im:
            im = im.convert("RGB")
            orig_cell = make_cell(im, path.stem[:28])

            photo_only = generate_synthetic_counterfeit(im, seed=hash(path.stem) % 100000,
                                                          include_text_tamper=False)
            photo_cell = make_cell(photo_only, "photographic only")

            with_text = generate_synthetic_counterfeit(im, seed=hash(path.stem) % 100000,
                                                        include_text_tamper=True)
            text_cell = make_cell(with_text, "+ text tampering")

        y = row * (THUMB + LABEL_H)
        grid.paste(orig_cell, (0, y))
        grid.paste(photo_cell, (THUMB, y))
        grid.paste(text_cell, (2 * THUMB, y))

    out_path = OUT_DIR / "preview_grid.png"
    grid.save(out_path)
    print(f"Wrote {out_path} ({len(sample)} rows x 3 cols: original | photographic-only | +text-tamper)")


if __name__ == "__main__":
    main()

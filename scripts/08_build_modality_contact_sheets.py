"""
Step 8 — Build contact sheets (image grids) for the manual outer-packaging
vs. blister-pack vs. loose-pills vs. label-close-up modality review (plan
Part 2.2), covering the full 564-image Kaggle modeling pool (the only
source actually used in Splits A/B/C).

Rationale: reviewing 564 images one at a time is impractical; tiling them
into labeled grids (30 thumbnails per sheet, ~19 sheets total) lets a human
(or an LLM doing visual review) cover every image while looking at far
fewer files. Each thumbnail is captioned with its grid position so
judgments can be recorded against a position->image_id index without
needing to open individual files.

Output:
  data/metadata/modality_review_sheets/sheet_NN.png  (grids)
  data/metadata/modality_review_sheets/index.csv      (sheet, position, image_id, class_label)
  data/metadata/modality_review_template.csv          (one row per image,
    empty `modality` column ready to fill in from the sheets)
"""
import csv
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
PROVENANCE = ROOT / "data" / "metadata" / "provenance.csv"
RAW = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "metadata" / "modality_review_sheets"
OUT_DIR.mkdir(parents=True, exist_ok=True)

THUMB = 160
LABEL_H = 18
COLS, ROWS = 6, 5
PER_SHEET = COLS * ROWS


def load_kaggle_rows():
    with open(PROVENANCE, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["source_dataset"] == "Kaggle - Fake vs Real Medicine"]
    rows.sort(key=lambda r: r["image_id"])
    return rows


def make_thumb(path, label):
    cell = Image.new("RGB", (THUMB, THUMB + LABEL_H), "white")
    try:
        with Image.open(path) as im:
            im = im.convert("RGB")
            im.thumbnail((THUMB, THUMB))
            x = (THUMB - im.width) // 2
            y = (THUMB - im.height) // 2
            cell.paste(im, (x, y))
    except Exception as e:
        d = ImageDraw.Draw(cell)
        d.text((4, 4), f"ERR", fill="red")
    d = ImageDraw.Draw(cell)
    d.rectangle([0, THUMB, THUMB, THUMB + LABEL_H], fill="black")
    d.text((2, THUMB + 2), label, fill="white")
    return cell


def main():
    rows = load_kaggle_rows()
    n_sheets = (len(rows) + PER_SHEET - 1) // PER_SHEET
    print(f"{len(rows)} images -> {n_sheets} sheets of up to {PER_SHEET}")

    index_rows = []
    for sheet_idx in range(n_sheets):
        batch = rows[sheet_idx * PER_SHEET: (sheet_idx + 1) * PER_SHEET]
        sheet = Image.new("RGB", (COLS * THUMB, ROWS * (THUMB + LABEL_H)), "white")
        for pos, r in enumerate(batch):
            row_i, col_i = divmod(pos, COLS)
            short_id = r["image_id"].replace("kaggle_fake_real_medicine_", "")
            label = f"{pos:02d} {short_id} {r['class_label'][:4]}"
            path = RAW / r["orig_relpath"]
            thumb = make_thumb(path, label)
            sheet.paste(thumb, (col_i * THUMB, row_i * (THUMB + LABEL_H)))
            index_rows.append({"sheet": sheet_idx, "position": pos,
                                "image_id": r["image_id"], "class_label": r["class_label"]})
        out_path = OUT_DIR / f"sheet_{sheet_idx:02d}.png"
        sheet.save(out_path)
        print(f"  wrote {out_path} ({len(batch)} images)")

    with open(OUT_DIR / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["sheet", "position", "image_id", "class_label"])
        w.writeheader()
        w.writerows(index_rows)

    template_path = ROOT / "data" / "metadata" / "modality_review_template.csv"
    with open(template_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image_id", "class_label", "modality", "notes"])
        for r in rows:
            w.writerow([r["image_id"], r["class_label"], "", ""])
    print(f"Wrote {OUT_DIR / 'index.csv'} and {template_path}")


if __name__ == "__main__":
    main()

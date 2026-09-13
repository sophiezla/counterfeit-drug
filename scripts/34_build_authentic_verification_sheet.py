"""
Step 34 — Build a verification sheet for the 46 authentic-labeled images.

WHY THIS EXISTS
---------------
The two classes of the balanced external test are not established on the same
footing. Every counterfeit frame carries an FDA or WHO finding that the product
photographed is falsified. The authentic side carries no corresponding
assurance: the subject-matter screen of step 32/33 decides whether a frame
shows a photograph of a current retail medicine package, and nothing visible in
a photograph can establish that the contents of a carton were made by the
manufacturer named on it. Sections III-D and V-D say so.

That limitation cannot be removed by any amount of automated screening, but it
can be *narrowed* by a human looking at the 46 selected images beside their
source pages and confirming that each depicts manufacturer-consistent retail
packaging. This step lays out exactly what such a pass needs and nothing more:
the 46 images at legible size, numbered, each with the product term it was
matched on and the Commons page that carries its licence, author and
description.

It does not perform the verification and does not record a verdict. If a pass
is made, its outcome belongs in `data/metadata/balanced_authentic_verification.csv`
and the manuscript's disclosure has to be updated to say who made it. Until
then the paper claims no human verification of this class, which is the
accurate position.

Output
------
  data/metadata/balanced_authentic_verification_sheet_NN.png   (gitignored)
  data/metadata/balanced_authentic_verification.csv            (blank verdicts)
"""
import csv
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "data" / "metadata"
PROV = META / "balanced_external_provenance.csv"
OUT_CSV = META / "balanced_authentic_verification.csv"

CELL = 300
COLS, ROWS = 4, 4
PER_SHEET = COLS * ROWS
BAND = 34          # caption strip under each thumbnail


def main():
    if not PROV.exists():
        print(f"missing {PROV}; run steps 32-33 first")
        return 1

    rows = [r for r in csv.DictReader(open(PROV, newline="", encoding="utf-8"))
            if r["class_label"] == "authentic"]
    rows.sort(key=lambda r: r["image_id"])
    print(f"{len(rows)} authentic-labeled images")

    for old in META.glob("balanced_authentic_verification_sheet_*.png"):
        old.unlink()

    for start in range(0, len(rows), PER_SHEET):
        chunk = rows[start:start + PER_SHEET]
        sheet = Image.new("RGB", (CELL * COLS, (CELL + BAND) * ROWS), "white")
        draw = ImageDraw.Draw(sheet)
        for j, r in enumerate(chunk):
            x, y = (j % COLS) * CELL, (j // COLS) * (CELL + BAND)
            try:
                with Image.open(ROOT / r["relpath_from_root"]) as im:
                    im = im.convert("RGB")
                    im.thumbnail((CELL - 8, CELL - 8), Image.LANCZOS)
                    sheet.paste(im, (x + 4, y + 4))
            except Exception as exc:                        # noqa: BLE001
                draw.text((x + 8, y + 8), f"unreadable: {exc}", fill="red")
            n = start + j + 1
            draw.text((x + 6, y + CELL + 4),
                      f"{n:>2}. {r['image_id']}", fill="black")
            draw.text((x + 6, y + CELL + 18),
                      f"    {r['product_identity'][:44]}", fill="black")
        k = start // PER_SHEET + 1
        sheet.save(META / f"balanced_authentic_verification_sheet_{k:02d}.png")

    n_sheets = (len(rows) + PER_SHEET - 1) // PER_SHEET
    print(f"wrote {n_sheets} verification sheets")

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "n", "image_id", "product_term", "commons_page", "license",
            "attribution", "verdict", "reviewer", "review_date", "note"])
        w.writeheader()
        for i, r in enumerate(rows, start=1):
            w.writerow({
                "n": i, "image_id": r["image_id"],
                "product_term": r["product_identity"],
                "commons_page": r["source_ref"], "license": r["licence"],
                "attribution": r["attribution"][:120],
                "verdict": "", "reviewer": "", "review_date": "", "note": "",
            })

    print(f"wrote {OUT_CSV.relative_to(ROOT)} with blank verdicts")
    print("\nVerdict vocabulary, if a pass is made:")
    print("  ok             manufacturer-consistent retail packaging")
    print("  not_retail     not a current retail medicine package")
    print("  unclear        cannot be determined from the image and its page")
    print("\nNothing in the manuscript claims this pass has been made.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

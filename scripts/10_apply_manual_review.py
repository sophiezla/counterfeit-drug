"""
Step 10 — Apply the exported manual review (scripts/09_build_manual_review_tool.py
+ data/metadata/manual_watermark_review.csv) back into the data pipeline.

Reads the CSV exported from the browser tool's "Export CSV" button. Rows
flagged "screenshot" are treated the same as the earlier confirmed
non-medicine contaminant (excluded outright — not a medicine photo).
Rows flagged "watermark" are excluded per the user's decision (same
treatment as the Roboflow bulletin-graphic exclusion: a confirmed,
class-correlated confound). Rows flagged "unsure" are NOT auto-excluded —
they're written to a follow-up queue for a judgment call, since "unsure"
by definition isn't a clear-cut exclusion. Rows flagged "clean" require no
action.

This script does not overwrite 02_filter.py's exclusion sets directly
(those are meant to be readably hand-edited); instead it:
  1. Prints the exact filenames to add to KAGGLE_NON_MEDICINE_FILENAMES /
     a new KAGGLE_WATERMARK_FILENAMES set, for a human/assistant to paste in.
  2. Writes data/metadata/manual_review_unsure_queue.csv for the "unsure" rows.
  3. If run with --apply, edits 02_filter.py automatically and re-runs the
     full data pipeline (scripts/run_all.py).

Usage:
    python scripts/10_apply_manual_review.py            # dry run, just reports
    python scripts/10_apply_manual_review.py --apply     # edits + rebuilds
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEW_CSV = ROOT / "data" / "metadata" / "manual_watermark_review.csv"
FILTER_SCRIPT = ROOT / "scripts" / "02_filter.py"
UNSURE_QUEUE = ROOT / "data" / "metadata" / "manual_review_unsure_queue.csv"


def main():
    apply = "--apply" in sys.argv

    if not REVIEW_CSV.exists():
        print(f"ERROR: {REVIEW_CSV} not found.")
        print("Open data/metadata/manual_review_tool.html in a browser, tag images,")
        print("then click 'Export CSV' and save it to that exact path.")
        sys.exit(1)

    with open(REVIEW_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    watermark_rows = [r for r in rows if r["flag"] == "watermark"]
    screenshot_rows = [r for r in rows if r["flag"] == "screenshot"]
    unsure_rows = [r for r in rows if r["flag"] == "unsure"]
    untagged = [r for r in rows if not r["flag"]]

    print(f"Total rows: {len(rows)}")
    print(f"  watermark: {len(watermark_rows)}")
    print(f"  screenshot/not-medicine: {len(screenshot_rows)}")
    print(f"  unsure: {len(unsure_rows)}")
    print(f"  untagged (review not finished): {len(untagged)}")

    def filename_of(relpath):
        # relpath looks like "../raw/kaggle_fake_real/dataset/Fake/Foo.png"
        return Path(relpath).name

    watermark_filenames = sorted({filename_of(r["orig_relpath"]) for r in watermark_rows})
    screenshot_filenames = sorted({filename_of(r["orig_relpath"]) for r in screenshot_rows})

    print("\n--- Filenames to exclude (watermark) ---")
    for fn in watermark_filenames:
        print(f'  "{fn}",')
    print("\n--- Filenames to exclude (screenshot/not-medicine) ---")
    for fn in screenshot_filenames:
        print(f'  "{fn}",')

    if unsure_rows:
        with open(UNSURE_QUEUE, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["image_id", "orig_relpath", "class_label", "notes"])
            w.writeheader()
            for r in unsure_rows:
                w.writerow({"image_id": r["image_id"], "orig_relpath": r["orig_relpath"],
                            "class_label": r["class_label"], "notes": r["notes"]})
        print(f"\nWrote {UNSURE_QUEUE} ({len(unsure_rows)} rows) -- not auto-excluded, needs a judgment call.")

    if not apply:
        print("\nDry run only. Re-run with --apply to edit scripts/02_filter.py and rebuild the pipeline.")
        return

    if untagged:
        print(f"\nWARNING: {len(untagged)} images are untagged (review incomplete). Applying anyway.")

    src = FILTER_SCRIPT.read_text(encoding="utf-8")

    watermark_set_literal = "KAGGLE_WATERMARK_FILENAMES = {\n" + \
        "\n".join(f'    "{fn}",' for fn in watermark_filenames) + "\n}\n"

    if "KAGGLE_WATERMARK_FILENAMES" in src:
        src = re.sub(r"KAGGLE_WATERMARK_FILENAMES = \{[^}]*\}\n", watermark_set_literal, src)
    else:
        src = src.replace(
            "KAGGLE_NON_MEDICINE_FILENAMES = {\"Screenshot 2025-09-17 180529.png\"}",
            "KAGGLE_NON_MEDICINE_FILENAMES = {\"Screenshot 2025-09-17 180529.png\""
            + (", " if screenshot_filenames else "")
            + ", ".join(f'"{fn}"' for fn in screenshot_filenames) + "}\n\n"
            "# Manually confirmed via data/metadata/manual_review_tool.html:\n"
            "# watermark/stock-photo overlays, checked to be 100% correlated with\n"
            "# the authentic label in the AI-suggested subset -- excluded as a\n"
            "# confirmed class-correlated confound (same treatment as Roboflow's\n"
            "# bulletin graphics).\n" + watermark_set_literal
        )
        src = src.replace(
            'if Path(r["orig_relpath"]).name in KAGGLE_NON_MEDICINE_FILENAMES:\n'
            '                r["excluded"] = "True"\n'
            '                r["exclusion_reason"] = "not_a_medicine_photo_browser_screenshot"',
            'if Path(r["orig_relpath"]).name in KAGGLE_NON_MEDICINE_FILENAMES:\n'
            '                r["excluded"] = "True"\n'
            '                r["exclusion_reason"] = "not_a_medicine_photo_browser_screenshot"\n'
            '            elif Path(r["orig_relpath"]).name in KAGGLE_WATERMARK_FILENAMES:\n'
            '                r["excluded"] = "True"\n'
            '                r["exclusion_reason"] = "watermark_stock_photo_confound"'
        )

    FILTER_SCRIPT.write_text(src, encoding="utf-8")
    print(f"\nEdited {FILTER_SCRIPT}. Re-running the full data pipeline...")

    import runpy
    runpy.run_path(str(ROOT / "scripts" / "run_all.py"), run_name="__main__")


if __name__ == "__main__":
    main()

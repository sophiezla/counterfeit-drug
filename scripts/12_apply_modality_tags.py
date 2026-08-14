"""
Step 12 — Apply the exported modality tags (scripts/11_build_modality_tagging_tool.py
+ data/metadata/manual_modality_tags.csv) into provenance.csv's `modality`
column. Labels only -- does not exclude anything. Deciding whether to
filter to outer-packaging-only (which would remove a large fraction of the
pool per data/metadata/modality_review_findings.md) is a separate,
deliberate decision to make with the real counts this produces, not
something this script does on its own.

Usage:
    python scripts/12_apply_modality_tags.py
"""
import csv
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
TAGS_CSV = ROOT / "data" / "metadata" / "manual_modality_tags.csv"
PROVENANCE = ROOT / "data" / "metadata" / "provenance.csv"


def main():
    if not TAGS_CSV.exists():
        print(f"ERROR: {TAGS_CSV} not found.")
        print("Open data/metadata/modality_tagging_tool.html in a browser, tag images,")
        print("then click 'Export CSV' and save it to that exact path.")
        sys.exit(1)

    with open(TAGS_CSV, newline="", encoding="utf-8") as f:
        tag_rows = list(csv.DictReader(f))

    def normalize(relpath: str) -> str:
        # tool exports use "../raw/kaggle_fake_real/..." with forward
        # slashes; provenance.csv uses "kaggle_fake_real\..." with
        # backslashes (no "../raw/" prefix) -- normalize both to the same
        # form so matching works regardless of image_id scheme changes.
        # image_id is NOT used for matching here: it's a hash of
        # orig_relpath as of whenever this ran, and is not guaranteed
        # stable against exports taken under a different ID scheme.
        r = relpath.replace("../raw/", "").replace("\\", "/")
        return r

    tags_by_path = {normalize(r["orig_relpath"]): r for r in tag_rows}

    untagged = [r for r in tag_rows if not r["modality"]]
    print(f"Total rows in export: {len(tag_rows)}")
    print(f"Untagged (incomplete): {len(untagged)}")
    print(Counter(r["modality"] for r in tag_rows if r["modality"]))

    with open(PROVENANCE, newline="", encoding="utf-8") as f:
        prov_rows = list(csv.DictReader(f))

    updated = 0
    for r in prov_rows:
        t = tags_by_path.get(normalize(r["orig_relpath"]))
        if t and t["modality"]:
            new_modality = t["modality"]
            if t["notes"]:
                new_modality += f" ({t['notes']})"
            r["modality"] = new_modality
            updated += 1

    fieldnames = list(prov_rows[0].keys())
    with open(PROVENANCE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(prov_rows)

    print(f"\nUpdated modality for {updated} rows in {PROVENANCE}")
    if untagged:
        print(f"NOTE: {len(untagged)} images were not tagged (review incomplete) -- rerun after finishing.")


if __name__ == "__main__":
    main()

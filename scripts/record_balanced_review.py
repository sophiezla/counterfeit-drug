"""
Helper — turn a compact per-sheet review note into balanced_external_review.csv.

The subject-matter review of step 32's contact sheets is recorded as one line
per sheet, listing the cells to exclude and the code for each:

    sheet_01: 0,3,5=A_NOT_PRODUCT; 7,11=A_NO_PACKAGE; 22=A_PERSON

Everything not named is included. This exists so the reviewer writes cell
numbers rather than 400 candidate ids, and so the mapping from a cell to a
candidate is done by the same code that laid the sheet out rather than by hand.

Usage
-----
    python scripts/record_balanced_review.py notes.txt

`notes.txt` holds one `sheet_NN: ...` line per sheet. Sheets with no exclusions
may be omitted or written with an empty right-hand side.
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "data" / "metadata"
TEMPLATE = META / "balanced_external_review_template.csv"
OUT = META / "balanced_external_review.csv"

REASONS = {
    "A_NOT_PRODUCT": "no medical product in the frame",
    "A_NOT_PHOTOGRAPH": "diagram, rendering or illustration, not a photograph",
    "A_NO_PACKAGE": "loose dose form with no packaging in the frame",
    "A_PERSON": "a person is the subject",
    "A_ANNOTATED": "arrows, callouts or burned-in caption",
    "A_HISTORICAL": "antique or museum object, not a current retail package",
    "A_AMBIGUOUS": "subject could not be determined",
}


def main(notes_path):
    rows = list(csv.DictReader(open(TEMPLATE, newline="", encoding="utf-8")))
    per_sheet = {}
    for i, r in enumerate(rows):
        per_sheet.setdefault(r["sheet"], []).append((i, r))

    verdict = {}
    for line in Path(notes_path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        sheet, _, body = line.partition(":")
        sheet = sheet.strip()
        if sheet not in per_sheet:
            print(f"unknown sheet {sheet!r}")
            return 1
        base = per_sheet[sheet][0][0]
        for clause in body.split(";"):
            clause = clause.strip()
            if not clause:
                continue
            cells, _, code = clause.partition("=")
            code = code.strip()
            if code not in REASONS:
                print(f"unknown code {code!r} on {sheet}")
                return 1
            for tok in re.split(r"[,\s]+", cells.strip()):
                if not tok:
                    continue
                idx = base + int(tok)
                if idx >= len(rows):
                    print(f"cell {tok} on {sheet} is past the end of the sheet")
                    return 1
                verdict[rows[idx]["candidate_id"]] = code

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["candidate_id", "sheet", "cell",
                                           "commons_title", "decision",
                                           "exclusion_code", "reason"])
        w.writeheader()
        for r in rows:
            code = verdict.get(r["candidate_id"], "")
            w.writerow({**r,
                        "decision": "exclude" if code else "include",
                        "exclusion_code": code,
                        "reason": REASONS.get(code, "")})

    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows) - len(verdict)} included, "
          f"{len(verdict)} excluded")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))

"""
Assemble the Grad-CAM review tool from the three heatmap manifests.

The heatmaps were regenerated 2026-07-30 after the batch-norm defect (the
Grad-CAM scripts ran the backbone in training mode, so every published map
described a mis-configured network -- see modeling/README.md and paper.md
Section 6.5). The earlier human categorisation described those compromised
maps and cannot be carried forward, so the review has to be redone.

This reads the three manifests, injects them into the tool template as a
single ordered list, and writes a self-contained HTML file that opens next to
the images. Same pattern as the project's earlier review tools
(scripts/09-12): keyboard-driven, one keypress tags and advances, progress
auto-saved to localStorage, CSV export at the end.

Run scripts/22_apply_gradcam_review.py afterwards to fold the exported CSV
back into the manifests and print the summary the paper needs.

Output: modeling/results/gradcam_review.html
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "modeling" / "results"
TEMPLATE = RESULTS / "gradcam_review_tool.html"
OUT = RESULTS / "gradcam_review.html"

SETS = [
    ("M4 in-distribution (Split B)", "gradcam"),
    ("M4 external (Split C)", "gradcam_split_c"),
    ("M3 external (Split C)", "gradcam_split_c_model3"),
]


def detail_for(row):
    """A short, honest caption: what the model predicted and how confidently."""
    if "y_prob_counterfeit" in row and row["y_prob_counterfeit"]:
        p = float(row["y_prob_counterfeit"])
        return (f"P(counterfeit) = {p:.3f} — model called it "
                f"{'counterfeit' if p >= 0.5 else 'authentic'}; "
                f"ground truth authentic")
    if "y_true" in row:
        yt, yp = row.get("y_true", "?"), row.get("y_pred", "?")
        name = {"0": "authentic", "1": "counterfeit"}
        prob = row.get("y_prob", "")
        p = f", P(counterfeit) = {float(prob):.3f}" if prob else ""
        return (f"true {name.get(yt, yt)}, predicted {name.get(yp, yp)}{p}")
    return ""


def main():
    items = []
    for label, folder in SETS:
        man = RESULTS / folder / "manifest.csv"
        if not man.exists():
            print(f"  skip {folder}: no manifest yet")
            continue
        rows = list(csv.DictReader(open(man, newline="", encoding="utf-8")))
        for r in rows:
            items.append({
                "set": label,
                "group": r.get("group", ""),
                "image_id": r.get("image_id", ""),
                "file": r["file"],
                # relative path: the HTML sits in results/ alongside the folders
                "path": f"{folder}/{r['file']}",
                "detail": detail_for(r),
                "key": f"{folder}::{r['file']}",
            })
        print(f"  {label}: {len(rows)} heatmaps")

    if not items:
        raise SystemExit("no manifests found — run the gradcam scripts first")

    html = TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("__ITEMS__", json.dumps(items, indent=1))
    OUT.write_text(html, encoding="utf-8")
    print(f"\nwrote {OUT}  ({len(items)} heatmaps)")
    print(f"open it with:  start {OUT}")


if __name__ == "__main__":
    main()

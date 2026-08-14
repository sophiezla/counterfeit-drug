"""
Fold the completed Grad-CAM review back into the manifests and summarise it.

Usage:
    python scripts/22_apply_gradcam_review.py path/to/gradcam_review_completed.csv

Writes the human tag and note into each set's manifest.csv (columns
`attention_tag` and `review_note`), then prints the per-set breakdown that
Section 7.7 of the paper reports, including the split by whether the model's
prediction was correct -- which is the comparison the earlier review used to
argue that M3 attends to the backdrop when right and to the product when
wrong.

Nothing here interprets the tags; it counts them. The interpretation belongs
in the paper and should be written after looking at these numbers, not before.
"""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "modeling" / "results"
SETS = {
    "M4 in-distribution (Split B)": "gradcam",
    "M4 external (Split C)": "gradcam_split_c",
    "M3 external (Split C)": "gradcam_split_c_model3",
}
TAG_LABEL = {
    "packaging_relevant": "on the product",
    "incidental": "incidental (background/corners)",
    "mixed": "mixed / ambiguous",
    "diffuse": "diffuse, no clear focus",
}


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    review_path = Path(sys.argv[1])
    review = list(csv.DictReader(open(review_path, newline="", encoding="utf-8")))
    tagged = [r for r in review if r.get("attention_tag")]
    print(f"{len(tagged)} of {len(review)} heatmaps tagged\n")

    by_file = {(r["set"], r["file"]): r for r in review}

    for label, folder in SETS.items():
        man = RESULTS / folder / "manifest.csv"
        if not man.exists():
            continue
        rows = list(csv.DictReader(open(man, newline="", encoding="utf-8")))
        fields = list(rows[0].keys())
        for extra in ("attention_tag", "review_note"):
            if extra not in fields:
                fields.append(extra)
        for r in rows:
            hit = by_file.get((label, r["file"]))
            r["attention_tag"] = hit["attention_tag"] if hit else ""
            r["review_note"] = hit["note"] if hit else ""
        with open(man, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)

        counts = Counter(r["attention_tag"] for r in rows if r["attention_tag"])
        n = sum(counts.values())
        print(f"=== {label} ===  ({n} of {len(rows)} tagged)")
        for tag, c in counts.most_common():
            print(f"    {TAG_LABEL.get(tag, tag):<34} {c:>3}  ({c / n:.0%})")

        # split by whether the model was right, where the manifest records it
        split = defaultdict(Counter)
        for r in rows:
            if not r["attention_tag"]:
                continue
            if "y_true" in r and r.get("y_pred"):
                ok = r["y_true"] == r["y_pred"]
            elif "group" in r:
                ok = r["group"].startswith("correct")
            else:
                continue
            split["correct" if ok else "incorrect"][r["attention_tag"]] += 1
        for kind in ("correct", "incorrect"):
            if split[kind]:
                tot = sum(split[kind].values())
                inner = ", ".join(f"{TAG_LABEL.get(t, t)} {c}"
                                  for t, c in split[kind].most_common())
                print(f"    when {kind:<9} (n={tot}): {inner}")
        print()

    print("Manifests updated. Quote these counts in paper.md Section 7.7 and "
          "state the sample size explicitly.")


if __name__ == "__main__":
    main()

"""
Step 25 — Independence and eligibility screening for Split E.

Two jobs, in the order the project has always done them for a new source
(cf. 07_verify_split_c_independence.py, which established the procedure).

(1) INDEPENDENCE. Is any Split E candidate a near-duplicate of anything already
    in this project's data? The check is the same rotation-canonical pHash used
    by 03_dedup.py at the same Hamming threshold of 8/64, but the reference set
    is deliberately wider than Split C's was: *every* image under data/raw,
    which covers the Roboflow and Kaggle modelling pool, the Mendeley Split C
    and Split D sets, the iphone11pro archive, and the synthetic counterfeits.
    Split C was checked against the deduplicated Roboflow+Kaggle pool only,
    because Splits C and D did not exist yet; there is no reason to keep the
    narrower reference now, and a candidate that duplicated a Split C image
    would be just as disqualifying as one that duplicated a training image.

    Within-set duplication is checked too. Split C could skip this — its images
    came from a single archive with one photograph per product — but Split E is
    assembled from regulatory alerts that reuse and re-crop each other's
    photographs, so a within-set duplicate is a live possibility.

(2) ELIGIBILITY. A URL in the manifest is not by itself an evaluable image.
    The screen is recorded in data/metadata/split_e_eligibility_review.csv, one
    row per candidate with a decision, an exclusion code and a written reason,
    so it can be read and overruled without editing code. This file applies it;
    it does not decide it. The codes:

      X_NOT_PRODUCT       no medical product in the frame (the WHO logo)
      X_TEXT_ONLY         a rendered table or a cropped lot-number block
      X_MIXED_CLASS       one frame containing both an authentic and a
                          counterfeit exemplar; unlabelable under a binary scheme
      X_ANNOTATED         regulator markup drawn onto the image
      X_BANNER_COMPOSITE  a burned-in caption naming the contents as falsified
      X_LABEL_UNVERIFIED  the manifest itself does not assert a class
      X_NOT_PHOTOGRAPH    flat carton artwork rather than a photograph
      X_CLASS_TOO_SMALL   a class with too few surviving images to evaluate

    X_BANNER_COMPOSITE and X_NOT_PHOTOGRAPH are the two that matter most for
    this paper specifically. A burned-in "PHOTOGRAPHS OF CONFIRMED FALSIFIED …"
    banner appears on falsified images and on no authentic one, so it is a
    perfect class-conditional cue of exactly the kind Section VI documents; and
    the authentic-labelled images in this manifest are vector carton artwork
    while the falsified ones are field photographs, which is the same
    class-conditional acquisition confound the case-study dataset carries. A
    two-class Split E built without this screen would reproduce the paper's own
    headline defect.

Output
------
  data/metadata/split_e_independence_report.txt
  data/metadata/split_e_candidate_provenance.csv — the images that pass both
    screens, in the column shape the modelling code expects.
"""
import csv
from pathlib import Path

import imagehash
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
# Split E draws on two acquisitions of the same kind of source, kept separate on
# disk so each stays traceable to the step that produced it: the 57 images named
# by the delivered manifest (step 24) and the images harvested from the wider
# FDA/WHO alert archive, including those extracted from alert PDFs (steps 27-28).
SPLIT_E_DIRS = [RAW / "split_e_regulatory", RAW / "split_e_harvested"]
DOWNLOAD_LOGS = [ROOT / "data" / "metadata" / "split_e_download_log.csv",
                 ROOT / "data" / "metadata" / "split_e_harvest_download_log.csv"]
REVIEWS = [ROOT / "data" / "metadata" / "split_e_eligibility_review.csv",
           ROOT / "data" / "metadata" / "split_e_harvest_eligibility_review.csv"]
REPORT_OUT = ROOT / "data" / "metadata" / "split_e_independence_report.txt"
PROVENANCE_OUT = ROOT / "data" / "metadata" / "split_e_candidate_provenance.csv"

HAMMING_THRESHOLD = 8  # same threshold as 03_dedup.py and step 07
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")

# Split E's label vocabulary is the regulatory one (FALSIFIED / AUTHENTIC); the
# modelling code's vocabulary is authentic/counterfeit. Map once, here, so the
# two never have to be reconciled downstream.
CLASS_LABEL = {"FALSIFIED": "counterfeit", "AUTHENTIC": "authentic"}


def rotation_canonical_hash(path: Path) -> int:
    """Identical to 03_dedup.py: min pHash over the four 90-degree rotations."""
    with Image.open(path) as im:
        im = im.convert("RGB")
        return min(int(str(imagehash.phash(im.rotate(angle, expand=True))), 16)
                   for angle in (0, 90, 180, 270))


def load_csv(path, key=None):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return {r[key]: r for r in rows} if key else rows


def main():
    review, log = {}, {}
    for path in REVIEWS:
        review.update(load_csv(path, key="image_id"))
    for path in DOWNLOAD_LOGS:
        for iid, r in load_csv(path, key="candidate_id" if "harvest" in path.name
                               else "image_id").items():
            if not r.get("stored_relpath"):
                continue
            # Normalise the two logs onto one shape. The harvest log calls the
            # label `alert_title` and has no case_id; a harvested image's case is
            # its alert, which is the same unit of independence a PC_ case_id is.
            log[iid] = {
                "case_id": r.get("case_id") or r.get("alert_url", ""),
                "manifest_label": r.get("manifest_label", "FALSIFIED"),
                "source_organization": r["source_organization"],
                "stored_relpath": r["stored_relpath"],
                "redistributable": r.get(
                    "redistributable",
                    str(r.get("redistribution_status", "").startswith("permitted"))),
                "alert_title": r.get("alert_title", ""),
            }

    candidates = sorted((p for d in SPLIT_E_DIRS if d.exists() for p in d.iterdir()
                         if p.suffix.lower() in IMAGE_SUFFIXES),
                        key=lambda p: p.stem)
    if not candidates:
        raise SystemExit("no Split E images; run scripts/24 and 27-28 first")

    reference = sorted(p for p in RAW.rglob("*")
                       if p.suffix.lower() in IMAGE_SUFFIXES
                       and not any(d in p.parents for d in SPLIT_E_DIRS))
    print(f"Split E candidates: {len(candidates)}    reference pool: {len(reference)} images")

    print("Hashing reference pool (this is the slow part; ~7k images)...")
    ref_hashes = np.zeros(len(reference), dtype=np.uint64)
    for i, p in enumerate(reference):
        ref_hashes[i] = np.uint64(rotation_canonical_hash(p))
        if (i + 1) % 1000 == 0:
            print(f"  {i + 1}/{len(reference)}", flush=True)

    print("Hashing Split E candidates...")
    cand_hashes = np.array([np.uint64(rotation_canonical_hash(p)) for p in candidates],
                           dtype=np.uint64)

    # --- (1a) against the existing pool ---
    results = []
    for i, p in enumerate(candidates):
        dist = np.bitwise_count(np.bitwise_xor(ref_hashes, cand_hashes[i]))
        j = int(np.argmin(dist))
        results.append({
            "image_id": p.stem,
            "min_hamming_distance": int(dist[j]),
            "nearest_existing_match": str(reference[j].relative_to(RAW)).replace("\\", "/"),
            "flagged_duplicate": bool(dist[j] <= HAMMING_THRESHOLD),
        })
    dists = [r["min_hamming_distance"] for r in results]
    flagged = [r for r in results if r["flagged_duplicate"]]

    # --- (1b) within Split E ---
    n = len(candidates)
    within = np.bitwise_count(np.bitwise_xor(cand_hashes.reshape(-1, 1),
                                             cand_hashes.reshape(1, -1)))
    iu, ju = np.triu_indices(n, k=1)
    pair_mask = within[iu, ju] <= HAMMING_THRESHOLD
    within_pairs = [(candidates[a].stem, candidates[b].stem, int(within[a, b]))
                    for a, b in zip(iu[pair_mask], ju[pair_mask])]

    # --- (2) eligibility ---
    included, excluded = [], []
    for p in candidates:
        r = review.get(p.stem)
        if r is None:
            raise SystemExit(f"{p.stem} has no row in either eligibility review; the "
                             f"screen must be complete before a Split E can be built")
        (included if r["decision"] == "include" else excluded).append(r)

    by_code = {}
    for r in excluded:
        by_code.setdefault(r["exclusion_code"], []).append(r["image_id"])

    dup_ids = {r["image_id"] for r in flagged}
    final = [r for r in included if r["image_id"] not in dup_ids]

    # product_identity: images from one regulatory case are photographs of one
    # seizure of one product, so the case is the grouping unit. This matters if
    # Split E is ever used for anything but a single held-out evaluation, and it
    # is what the paper's own leakage discipline (Section IV) requires.
    labels = {r["image_id"]: CLASS_LABEL[log[r["image_id"]]["manifest_label"]] for r in final}
    cases = {r["image_id"]: log[r["image_id"]]["case_id"] for r in final}
    dist_by_id = {r["image_id"]: r["min_hamming_distance"] for r in results}

    # ------------------------------------------------------------------ report
    lines = [
        "Split E independence and eligibility report",
        "(regulatory-alert candidate set: FDA and WHO falsified-medicine alerts)",
        "",
        f"Candidates fetched from the manifest: {len(candidates)}",
        f"Reference pool checked against: {len(reference)} images "
        f"(all of data/raw: Roboflow, Kaggle, Mendeley Splits C and D, "
        f"iphone11pro, synthetic counterfeits)",
        f"Hamming threshold (same as 03_dedup.py and step 07): {HAMMING_THRESHOLD}/64 bits",
        "",
        "=== (1a) Split E vs. everything already in this project ===",
        f"Candidates flagged as near-duplicates: {len(flagged)}/{len(results)}",
        f"Nearest-neighbour distance distribution: min={min(dists)}, "
        f"median={int(np.median(dists))}, max={max(dists)}",
    ]
    if flagged:
        lines.append("Flagged:")
        lines += [f"  {r['image_id']} (dist={r['min_hamming_distance']}) "
                  f"~= {r['nearest_existing_match']}" for r in flagged]
    else:
        lines += [
            "No candidate matched any existing image within threshold.",
            "VERDICT: no overlap with the training pool or with either existing",
            "external set. The closest approach is distance "
            f"{min(dists)}, against a threshold of {HAMMING_THRESHOLD}; for",
            "reference, Split C's closest approach to the training pool was 10.",
        ]
    lines += ["", "Ten closest candidates (all above threshold unless flagged above):"]
    for r in sorted(results, key=lambda r: r["min_hamming_distance"])[:10]:
        lines.append(f"  {r['image_id']} dist={r['min_hamming_distance']} "
                     f"-> {r['nearest_existing_match']}")

    lines += ["", "=== (1b) Duplication within Split E ===",
              f"Near-duplicate pairs within the candidate set: {len(within_pairs)}"]
    for a, b, d in within_pairs:
        la = CLASS_LABEL.get(log[a]["manifest_label"], log[a]["manifest_label"])
        lb = CLASS_LABEL.get(log[b]["manifest_label"], log[b]["manifest_label"])
        lines.append(f"  {a} ({la}, {log[a]['case_id']}) <-> {b} ({lb}, "
                     f"{log[b]['case_id']}) dist={d}")
    if within_pairs:
        surviving = [(a, b) for a, b, _ in within_pairs
                     if a in labels and b in labels]
        lines.append(f"  of which both members survive the eligibility screen: {len(surviving)}")

    lines += ["", "=== (2) Eligibility screen ===",
              f"Reviewed: {len(candidates)}   include: {len(included)}   "
              f"exclude: {len(excluded)}"]
    for code in sorted(by_code):
        lines.append(f"  {code:<20} {len(by_code[code]):>3}  "
                     f"{', '.join(by_code[code])}")

    lines += ["", "=== Final Split E ==="]
    counts = {}
    for iid, lab in labels.items():
        counts[lab] = counts.get(lab, 0) + 1
    lines.append(f"Images: {len(final)}   class counts: {counts}")
    lines.append(f"Distinct regulatory cases (product_identity groups): "
                 f"{len(set(cases.values()))}")
    redist = sum(1 for iid in labels if log[iid]["redistributable"] == "True")
    lines.append(f"Redistributable bytes (FDA public domain): {redist}; "
                 f"metadata-only (WHO): {len(final) - redist}")
    if len(counts) < 2:
        lines += [
            "",
            "SINGLE-CLASS SET. Split E carries only the counterfeit class, so it",
            "measures external counterfeit recall (sensitivity) and nothing else --",
            "the exact complement of Splits C and D, which are authentic-only and",
            "measure specificity. It is not an accuracy and must never be reported",
            "as one. Read on its own a recall figure is uninterpretable: a model",
            "that called every image counterfeit would score 1.000 here. It is",
            "interpretable only jointly with the Split C and D specificities, which",
            "bound that degenerate solution from the other side.",
        ]

    report = "\n".join(lines)
    REPORT_OUT.write_text(report, encoding="utf-8")
    print("\n" + report)

    with open(PROVENANCE_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["image_id", "source_dataset", "orig_relpath", "class_label",
                    "product_identity", "case_id", "source_organization",
                    "redistributable", "panel_composite", "label_crop",
                    "min_hamming_distance_to_existing_pool"])
        # Short stable ids for the grouping unit; a harvested image's case is an
        # alert URL, which is unwieldy as a product_identity string.
        case_key = {c: (c if c.startswith("CASE_") else f"ALERT_{i:04d}")
                    for i, c in enumerate(sorted({cases[r["image_id"]] for r in final}), 1)}
        for r in sorted(final, key=lambda r: r["image_id"]):
            iid = r["image_id"]
            w.writerow([f"split_e_{iid}",
                        f"{log[iid]['source_organization']} regulatory alert",
                        log[iid]["stored_relpath"],
                        labels[iid],
                        f"case_{case_key[cases[iid]]}",
                        cases[iid],
                        log[iid]["source_organization"],
                        log[iid]["redistributable"],
                        r["panel_composite"],
                        r.get("label_crop", "no"),
                        dist_by_id[iid]])

    print(f"\nWrote {REPORT_OUT}")
    print(f"Wrote {PROVENANCE_OUT} ({len(final)} images)")


if __name__ == "__main__":
    main()

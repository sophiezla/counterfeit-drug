"""
Step 33 — Apply the subject-matter review and build the locked balanced set.

Step 32 decided what is *eligible*; this step decides what is *selected*, builds
the images and locks the set. Everything it does is deterministic and consults
no random number generator.

  1. APPLY THE REVIEW. `data/metadata/balanced_external_review.csv` carries one
     row per eligible candidate with a decision, an exclusion code and a
     written reason. This file applies it; it does not decide it. The codes are
     the authentic-side counterparts of step 25's:

       A_NOT_PRODUCT       no medical product in the frame -- a building, a
                           landscape, a pharmacy interior, laboratory glassware
       A_NOT_PHOTOGRAPH    a diagram, a molecular rendering, an illustration or
                           period advertising art rather than a photograph
       A_NO_PACKAGE        loose tablets, capsules or powder with no packaging
                           in the frame; the counterfeit class is photographs of
                           packaged product and this would not be comparable
       A_PERSON            a person is the subject
       A_ANNOTATED         arrows, callouts or burned-in captions
       A_HISTORICAL        an antique or museum object rather than a current
                           retail medicine package
       A_AMBIGUOUS         the reviewer could not determine what it shows

  2. SELECT 46, MATCHED. The counterfeit side is one image per regulatory case,
     which is 46 by construction and makes each counterfeit image an
     independent case rather than one of several frames of one seizure. The
     authentic side is then chosen by nearest-neighbour brightness matching to
     those 46, at most one per Commons search term while the terms last, so the
     two classes are matched on the one acquisition axis that ingestion cannot
     equalise and spread across products rather than concentrated on whichever
     drug Commons happens to photograph most.

  3. INGEST BOTH CLASSES IDENTICALLY. One pipeline, both classes: RGB, short
     side to 448 px, JPEG at one quality with metadata stripped. Container
     format, encoder, encoder settings and stored short side are therefore
     constant across the classes by construction.

  4. AUDIT AND LOCK. The paper's own procedure (Section III-E) is run on the
     finished set and its result is reported with it, then the provenance CSV
     is hashed and the set is frozen.

Outputs
-------
  data/processed/balanced_external/{authentic,counterfeit}/*.jpg
  data/metadata/balanced_external_provenance.csv     (the locked set)
  data/metadata/balanced_external_build_report.txt
"""
import csv
import hashlib
import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
META = ROOT / "data" / "metadata"
PROCESSED = ROOT / "data" / "processed" / "balanced_external"

SCREEN = META / "balanced_external_screen.csv"
REVIEW = META / "balanced_external_review.csv"
SPLIT_E = META / "split_e_candidate_provenance.csv"
PROV_OUT = META / "balanced_external_provenance.csv"
REPORT_OUT = META / "balanced_external_build_report.txt"

N_PER_CLASS = 46


def _load_step32():
    spec = importlib.util.spec_from_file_location(
        "step32", Path(__file__).resolve().parent / "32_build_balanced_external.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    s32 = _load_step32()
    for f in (SCREEN, REVIEW, SPLIT_E):
        if not f.exists():
            print(f"missing {f}; run step 32 and record the review first")
            return 1

    report = []
    screen = {r["candidate_id"]: r for r in
              csv.DictReader(open(SCREEN, newline="", encoding="utf-8"))}
    review = list(csv.DictReader(open(REVIEW, newline="", encoding="utf-8")))

    eligible = [c for c, r in screen.items() if r["decision"] == "pending_review"]
    reviewed = {r["candidate_id"] for r in review}
    missing = set(eligible) - reviewed
    if missing:
        print(f"FATAL: {len(missing)} eligible candidates carry no review row, "
              f"e.g. {sorted(missing)[:5]}")
        return 1

    import collections
    codes = collections.Counter(r["exclusion_code"] for r in review)
    accepted = [screen[r["candidate_id"]] for r in review
                if r["decision"] == "include"]
    report.append("SUBJECT-MATTER REVIEW")
    report.append(f"  eligible after the automated screens: {len(eligible)}")
    for code, k in sorted(codes.items(), key=lambda t: -t[1]):
        report.append(f"    {code or '(included)':<20} {k}")
    report.append(f"  accepted: {len(accepted)}")
    report.append("")
    print(f"review: {len(accepted)}/{len(eligible)} accepted", flush=True)

    if len(accepted) < N_PER_CLASS:
        print(f"FATAL: only {len(accepted)} accepted, need {N_PER_CLASS}")
        REPORT_OUT.write_text("\n".join(report) + "\n", encoding="utf-8")
        return 1

    # --- the counterfeit side: one image per regulatory case ----------------
    e_rows = list(csv.DictReader(open(SPLIT_E, newline="", encoding="utf-8")))
    by_case = {}
    for r in e_rows:
        by_case.setdefault(r["case_id"], []).append(r)
    e_pick = []
    for case in sorted(by_case):
        group = sorted(by_case[case], key=lambda r: r["image_id"])
        stats = [s32.image_stats(RAW / r["orig_relpath"]) for r in group]
        order = np.argsort([s["brightness"] for s in stats])
        pick = int(order[(len(order) - 1) // 2])
        row = dict(group[pick])
        row.update(stats[pick])
        e_pick.append(row)
    e_pick.sort(key=lambda r: r["image_id"])
    report.append(f"COUNTERFEIT SIDE: {len(e_pick)} case representatives drawn "
                  f"from {len(e_rows)} images across {len(by_case)} regulatory "
                  f"cases (the within-case median-brightness frame)")
    report.append("")

    # --- matched selection ---------------------------------------------------
    pool = sorted(accepted, key=lambda r: r["candidate_id"])
    chosen, used_terms, taken = [], set(), set()
    for target in e_pick:
        cands = [c for c in pool if c["candidate_id"] not in taken
                 and c["query_term"] not in used_terms]
        if not cands:
            cands = [c for c in pool if c["candidate_id"] not in taken]
        best = min(cands, key=lambda c: abs(float(c["brightness"])
                                            - float(target["brightness"])))
        chosen.append(best)
        taken.add(best["candidate_id"])
        used_terms.add(best["query_term"])
    report.append(f"AUTHENTIC SIDE: {len(chosen)} selected by "
                  f"nearest-neighbour brightness matching, across "
                  f"{len(used_terms)} distinct product search terms")
    report.append("")
    print(f"selected {len(chosen)} authentic images", flush=True)

    # --- ingestion -----------------------------------------------------------
    print(f"ingesting both classes at short side {s32.INGEST_SHORT_SIDE}, "
          f"JPEG q={s32.INGEST_QUALITY}", flush=True)
    for sub in ("authentic", "counterfeit"):
        d = PROCESSED / sub
        d.mkdir(parents=True, exist_ok=True)
        for old in d.glob("*.jpg"):
            old.unlink()

    rows = []
    for i, c in enumerate(chosen, start=1):
        iid = f"bx_auth_{i:03d}"
        dst = PROCESSED / "authentic" / f"{iid}.jpg"
        s32.ingest(Path(c["path"]), dst)
        s = s32.image_stats(dst)
        rows.append({
            "image_id": iid, "class_label": "authentic",
            "relpath_from_root":
                f"data/processed/balanced_external/authentic/{iid}.jpg",
            "source": "Wikimedia Commons", "source_ref": c["page_url"],
            "product_identity": c["query_term"], "group_id": f"auth_{i:03d}",
            "licence": c["licence_short"], "attribution": c["artist"],
            "candidate_id": c["candidate_id"],
            "min_hamming_to_pool": c.get("min_hamming_to_pool", ""),
            **{k: s[k] for k in ("format", "width", "height", "min_side",
                                 "file_size_bytes", "brightness")},
        })
    for i, c in enumerate(e_pick, start=1):
        iid = f"bx_cft_{i:03d}"
        dst = PROCESSED / "counterfeit" / f"{iid}.jpg"
        s32.ingest(RAW / c["orig_relpath"], dst)
        s = s32.image_stats(dst)
        rows.append({
            "image_id": iid, "class_label": "counterfeit",
            "relpath_from_root":
                f"data/processed/balanced_external/counterfeit/{iid}.jpg",
            "source": f"{c['source_organization']} regulatory alert",
            "source_ref": c["case_id"],
            "product_identity": c["product_identity"],
            "group_id": c["product_identity"], "licence": "",
            "attribution": c["source_organization"],
            "candidate_id": c["image_id"],
            "min_hamming_to_pool": c["min_hamming_distance_to_existing_pool"],
            **{k: s[k] for k in ("format", "width", "height", "min_side",
                                 "file_size_bytes", "brightness")},
        })

    s32.provenance_audit(rows, report)

    with open(PROV_OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    report.append("LOCK")
    report.append(f"  balanced_external_provenance.csv sha256 "
                  f"{hashlib.sha256(PROV_OUT.read_bytes()).hexdigest()}")
    report.append("  The set is frozen at this point. Nothing downstream may "
                  "change the model, its preprocessing, its normalisation, its "
                  "decision threshold or this set; the evaluation runs once.")

    REPORT_OUT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n" + "\n".join(report))
    print(f"\nwrote {PROV_OUT.relative_to(ROOT)} ({len(rows)} images)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

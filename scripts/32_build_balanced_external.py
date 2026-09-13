"""
Step 32 — Screen the authentic candidates for the balanced external test.

Steps 32 and 33 split the work the way every other screened source in this
project is handled (09/10, 11/12, 16/17, 21/22, 29/25): this step decides what
is *eligible* and records why, step 33 decides what is *selected* and builds
the set. The division exists so the screen can be re-run, widened or overruled
without re-hashing the reference tree or rebuilding the images.

WHAT THIS SET IS FOR
--------------------
Every external number this project had before it was one-sided. Splits C and D
are authentic-only and yield a specificity; Split E is falsified-only and
yields a recall. Neither can produce an accuracy, a balanced accuracy, an F1 or
an ROC-AUC, and a one-sided evaluation cannot separate a model applying a real
decision rule from one that has shifted its operating point -- which is not a
hypothetical, M1 having scored 0.000/0.000 specificity against 0.967 recall.
This set closes that: two classes, equal counts, evaluated once.

THE DESIGN PROBLEM, AND HOW IT IS ANSWERED
------------------------------------------
Assembling a two-class external set out of two sources is precisely the
manoeuvre this paper exists to warn about, and doing it carelessly here would
have reproduced the headline defect inside the paper's own validation. Three
things are done about it, in this order.

  1. SOURCE. The counterfeit class is Split E's regulatory photographs. The
     authentic class is NOT taken from the same archives (step 25 found their
     authentic-labelled imagery to be vector carton artwork, brightness gap
     +0.233) and NOT taken from Splits C and D (brightness gap +0.396, short
     side 2448 px against 439 px -- worse than the gap that disqualified the
     artwork). It is harvested independently from Wikimedia Commons and
     product-matched to Split E's 46 alerts (step 30).

  2. INGESTION. Both classes are then passed through ONE identical pipeline:
     RGB, short side resampled to INGEST_SHORT_SIDE, re-encoded at one JPEG
     quality with metadata stripped. Container format, encoder, encoder
     settings and stored resolution are therefore constant across the two
     classes *by construction*. In the paper's notation A_pure is eliminated by
     design rather than measured, and the size and dimension components of
     A_mix go with it. This is a dataset-construction step, not a model
     preprocessing step: it is applied to both classes identically, before any
     model sees anything, and the models' own preprocessing (224 px resize)
     is untouched.

  3. MATCHING AND AUDIT. Brightness cannot be normalised away without
     intervening on content, so it is handled by matched selection instead:
     authentic candidates are screened to Split E's observed brightness support
     and then selected by nearest-neighbour matching to the 46 counterfeit
     images. What survives all of that is then AUDITED by the paper's own
     procedure (Section III-E) and the result is reported with the set. If the
     audit on this set returned 1.000 the set would be worthless and we would
     have to say so; running it is not optional.

THE ELIGIBILITY SCREEN IS CALIBRATED, NOT ASSERTED
--------------------------------------------------
The one screen that decides most exclusions is "is this a photograph, or is it
flat artwork?" -- the rule that removed 8 of 9 authentic candidates in step 25.
Rather than pick thresholds by eye, they are fitted here on labelled data this
project already holds: the 9 authentic-labelled regulatory candidates step 25
judged by hand (8 artwork, 1 photograph) as positives for "artwork", and Split
E's 150 accepted photographs as negatives. The calibration set, the chosen
thresholds and the separation achieved are all written to the report.

WHY AN AUTOMATED SCREEN IS NOT ENOUGH, AND WHAT RUNS AFTER IT
-------------------------------------------------------------
The screens here read file properties and pixel statistics. They catch flat
artwork, out-of-band brightness and near-duplicates, and they catch nothing
about *subject matter* -- and Commons, searched for drug names, returns a great
deal that is not a photograph of a medicine package: cell-biology diagrams,
ball-and-stick molecular renderings, pharmacy interiors, hospital buildings,
landscapes, a computer keyboard, a glass of water, people receiving injections,
and loose tablets tipped out of their packaging. None of that is excluded by
any statistic computed here, and every one of them would be a defect in an
authentic class meant to be comparable to photographs of seized product.

So this step ends by marking its survivors `pending_review` and writing contact
sheets. A per-image subject-matter review is then recorded in
`balanced_external_review.csv` and applied by step 33. Section III-D and the
Acknowledgment state who performed that review; it is published per image with
its reason so it can be overruled without editing code.

Outputs
-------
  data/metadata/balanced_external_screen.csv         (every candidate + verdict)
  data/metadata/balanced_external_report.txt         (screen + independence)
  data/metadata/balanced_external_sheets/*.png       (contact sheets to review)
  data/metadata/balanced_external_review_template.csv
"""
import csv
import hashlib
import re
import sys
from pathlib import Path

import imagehash
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
META = ROOT / "data" / "metadata"
PROCESSED = ROOT / "data" / "processed" / "balanced_external"

HARVEST = META / "balanced_authentic_harvest_manifest.csv"
DLOG = META / "balanced_authentic_download_log.csv"
SPLIT_E = META / "split_e_candidate_provenance.csv"
E_REVIEW = META / "split_e_eligibility_review.csv"

SCREEN_OUT = META / "balanced_external_screen.csv"
SHEETS_DIR = META / "balanced_external_sheets"
REVIEW_TEMPLATE = META / "balanced_external_review_template.csv"
REPORT_OUT = META / "balanced_external_report.txt"

N_PER_CLASS = 46                 # = Split E's distinct regulatory cases
INGEST_SHORT_SIDE = 448          # close to Split E's 439 px median; models see 224
INGEST_QUALITY = 92
HAMMING_THRESHOLD = 8            # same as 03_dedup.py, step 07 and step 25
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")
RNG_SEED = 42

# Commons files a great deal of non-photographic material in drug categories:
# chemical structures rendered to PNG, logos, package inserts, charts. Title
# and credit text catches most of it before a pixel is decoded, which is the
# cheap half of the screen; FLATNESS catches the rest.
TITLE_BLOCK = re.compile(
    r"\b(structure|structural|molecul|skeletal|formula|chemical|synthesis|"
    r"reaction|logo|icon|diagram|chart|graph|plot|map|schema|flowchart|"
    r"poster|leaflet|insert|advert|banner|signature|portrait|statue|"
    r"building|pharmacy shop|protest|meme|screenshot|scan of)\b",
    re.IGNORECASE)


# ---------------------------------------------------------------- image stats

def image_stats(path):
    """Everything the screens read, from one decode."""
    with Image.open(path) as im:
        fmt = im.format
        w, h = im.size
        rgb = im.convert("RGB")
        small = np.asarray(rgb.resize((64, 64), Image.BILINEAR),
                           dtype=np.float32) / 255.0
        mid = np.asarray(rgb.resize((256, 256), Image.BILINEAR),
                         dtype=np.float32) / 255.0

    grey = mid.mean(axis=2)
    gx = np.abs(np.diff(grey, axis=1)).mean()
    gy = np.abs(np.diff(grey, axis=0)).mean()

    # A flat carton rendering has a large near-white ground, few distinct
    # colours and almost no texture anywhere. A photograph has none of those.
    near_white = float((mid.min(axis=2) > 0.95).mean())
    q = (mid * 31).astype(np.uint8)
    ncol = len(np.unique(q.reshape(-1, 3), axis=0))

    return {
        "format": fmt, "width": w, "height": h, "min_side": min(w, h),
        "file_size_bytes": Path(path).stat().st_size,
        "brightness": float(small.mean()),
        "grad": float((gx + gy) / 2.0),
        "near_white_frac": near_white,
        "quantized_colours": int(ncol),
    }


def rotation_canonical_hash(path):
    with Image.open(path) as im:
        im = im.convert("RGB")
        return min(int(str(imagehash.phash(im.rotate(a, expand=True))), 16)
                   for a in (0, 90, 180, 270))


def hamming(a, b):
    return bin(a ^ b).count("1")


# ------------------------------------------------------------- flatness calib

def calibrate_flatness(report):
    """Fit the artwork rule on step 25's own hand-labelled candidates.

    Positives: the authentic-labelled regulatory candidates step 25 excluded as
    X_NOT_PHOTOGRAPH. Negatives: Split E's accepted photographs. Three
    candidate axes are scored, the one that separates the two calibration
    classes best is selected, and its threshold is set at the midpoint of the
    widest gap between the classes on that axis. All three are reported, so the
    reader can see why one was chosen rather than take it on trust.

    A single axis is used rather than a conjunction of three. The first version
    of this function required all three at once and caught 0 of 8 artwork
    images, because two of the axes do not separate the classes at all: on
    mean gradient the artwork range [0.0197, 0.0225] sits inside the
    photographs' 5th-95th percentile band, and on quantised colour count the
    artwork range [198, 867] straddles the photographs' 5th percentile. Only
    the near-white fraction separates, and it separates completely. A
    conjunction of one discriminating axis and two noise axes is a rule that
    fires on nothing, which is the worst possible screen: it excludes nothing
    and looks careful.
    """
    review = {r["image_id"]: r for r in
              csv.DictReader(open(E_REVIEW, newline="", encoding="utf-8"))}
    art_ids = [k for k, r in review.items()
               if r["exclusion_code"] == "X_NOT_PHOTOGRAPH"]

    def find(image_id):
        for d in (RAW / "split_e_regulatory", RAW / "split_e_harvested"):
            for suf in IMAGE_SUFFIXES:
                p = d / f"{image_id}{suf}"
                if p.exists():
                    return p
        return None

    art = [image_stats(p) for p in (find(i) for i in art_ids) if p]
    photo = []
    for r in csv.DictReader(open(SPLIT_E, newline="", encoding="utf-8")):
        photo.append(image_stats(RAW / r["orig_relpath"]))

    report.append("FLATNESS CALIBRATION")
    report.append(f"  artwork positives (step 25 X_NOT_PHOTOGRAPH): {len(art)}")
    report.append(f"  photograph negatives (Split E accepted):      {len(photo)}")

    if not art:
        report.append("  no positives found; falling back to a fixed rule")
        return {"axis": "near_white_frac", "direction": "hi",
                "threshold": 0.24}

    def score(key, direction):
        """Youden's J for the best single threshold on this axis."""
        a = np.array([s[key] for s in art], dtype=float)
        p = np.array([s[key] for s in photo], dtype=float)
        cuts = np.unique(np.concatenate([a, p]))
        best = (-1.0, float(cuts[0]))
        for c in cuts:
            tpr = float((a > c).mean() if direction == "hi" else (a < c).mean())
            fpr = float((p > c).mean() if direction == "hi" else (p < c).mean())
            if tpr - fpr > best[0]:
                best = (tpr - fpr, float(c))
        return best[0], best[1], a, p

    ranked = []
    for key, direction in (("near_white_frac", "hi"), ("grad", "lo"),
                           ("quantized_colours", "lo")):
        j, cut, a, p = score(key, direction)
        ranked.append((j, key, direction, cut, a, p))
        report.append(f"  {key:<20} artwork [{a.min():.4g}, {a.max():.4g}]  "
                      f"photo p5={np.percentile(p, 5):.4g} "
                      f"p95={np.percentile(p, 95):.4g}   Youden J {j:.3f}")

    ranked.sort(key=lambda t: -t[0])
    j, key, direction, cut, a, p = ranked[0]

    # Place the threshold in the middle of the gap the classes leave around the
    # J-maximising cut, rather than on top of one class's extreme value.
    if direction == "hi":
        lo_edge = float(p[p <= a.min()].max()) if (p <= a.min()).any() else float(cut)
        th_val = (lo_edge + float(a.min())) / 2.0
        tp = int((a > th_val).sum())
        fp = int((p > th_val).sum())
    else:
        hi_edge = float(p[p >= a.max()].min()) if (p >= a.max()).any() else float(cut)
        th_val = (hi_edge + float(a.max())) / 2.0
        tp = int((a < th_val).sum())
        fp = int((p < th_val).sum())

    th = {"axis": key, "direction": direction, "threshold": th_val}
    report.append(f"  selected axis: {key} ({direction}), threshold "
                  f"{th_val:.4g}, Youden J {j:.3f}")
    report.append(f"  on the calibration data: {tp}/{len(art)} artwork caught, "
                  f"{fp}/{len(photo)} photographs wrongly caught")
    report.append("")
    return th


def is_flat(stats, th):
    v = stats[th["axis"]]
    return v > th["threshold"] if th["direction"] == "hi" else v < th["threshold"]


# ------------------------------------------------------------------ ingestion

def ingest(src, dst):
    """The single pipeline both classes go through. See module docstring (2)."""
    with Image.open(src) as im:
        im = im.convert("RGB")
        w, h = im.size
        scale = INGEST_SHORT_SIDE / min(w, h)
        new = (max(1, round(w * scale)), max(1, round(h * scale)))
        im = im.resize(new, Image.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst, "JPEG", quality=INGEST_QUALITY, optimize=False,
                subsampling=0)      # fixed, so encoder settings cannot vary
    return dst


# ---------------------------------------------------------------------- audit

def provenance_audit(rows, report):
    """Section III-E's procedure, run on the finished balanced set."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold
    from sklearn.metrics import balanced_accuracy_score

    y = np.array([1 if r["class_label"] == "counterfeit" else 0 for r in rows])
    fmts = {r["format"] for r in rows}

    report.append("PROVENANCE AUDIT ON THE FINISHED SET (Section III-E)")
    report.append(f"  A_pure, container format: {sorted(fmts)} -- "
                  f"{'constant by construction, no information' if len(fmts) == 1 else 'NOT CONSTANT, INVESTIGATE'}")

    dims = {(int(r['width']), int(r['height'])) for r in rows}
    short = {min(int(r['width']), int(r['height'])) for r in rows}
    report.append(f"  stored short side: {sorted(short)} "
                  f"({len(dims)} distinct (w,h) pairs, aspect follows content)")

    axes = {
        "log10 file size": lambda r: [np.log10(float(r["file_size_bytes"]))],
        "aspect ratio": lambda r: [float(r["width"]) / float(r["height"])],
        "mean brightness": lambda r: [float(r["brightness"])],
    }
    axes["all three jointly"] = lambda r: (
        axes["log10 file size"](r) + axes["aspect ratio"](r)
        + axes["mean brightness"](r))

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=RNG_SEED)
    for name, fx in axes.items():
        X = np.array([fx(r) for r in rows], dtype=float)
        preds = np.zeros_like(y)
        for tr, te in skf.split(X, y):
            clf = LogisticRegression(max_iter=2000, class_weight="balanced")
            clf.fit(X[tr], y[tr])
            preds[te] = clf.predict(X[te])
        ba = balanced_accuracy_score(y, preds)
        report.append(f"  A_mix, {name:<22} balanced accuracy {ba:.3f} "
                      f"(chance 0.500)")

    b_auth = np.array([float(r["brightness"]) for r in rows if r["class_label"] == "authentic"])
    b_cft = np.array([float(r["brightness"]) for r in rows if r["class_label"] == "counterfeit"])
    report.append(f"  brightness: authentic {b_auth.mean():.3f}, "
                  f"counterfeit {b_cft.mean():.3f}, "
                  f"gap {b_auth.mean() - b_cft.mean():+.3f}  "
                  f"(the gap that disqualified the regulatory artwork: +0.233)")
    report.append("")


# ------------------------------------------------------------------------ run

def main():
    report = []
    for f in (HARVEST, DLOG, SPLIT_E, E_REVIEW):
        if not f.exists():
            print(f"missing {f}")
            return 1

    manifest = {r["candidate_id"]: r for r in
                csv.DictReader(open(HARVEST, newline="", encoding="utf-8"))}
    dl = [r for r in csv.DictReader(open(DLOG, newline="", encoding="utf-8"))
          if r["status"] == "ok"]
    print(f"{len(dl)} downloaded authentic candidates", flush=True)

    th = calibrate_flatness(report)
    print(f"artwork rule: {th['axis']} {'>' if th['direction'] == 'hi' else '<'} "
          f"{th['threshold']:.4g}", flush=True)

    # --- Split E side: one image per regulatory case ------------------------
    e_rows = list(csv.DictReader(open(SPLIT_E, newline="", encoding="utf-8")))
    by_case = {}
    for r in e_rows:
        by_case.setdefault(r["case_id"], []).append(r)
    print(f"Split E: {len(e_rows)} images, {len(by_case)} cases", flush=True)

    e_pick = []
    for case in sorted(by_case):
        group = sorted(by_case[case], key=lambda r: r["image_id"])
        stats = [image_stats(RAW / r["orig_relpath"]) for r in group]
        # the within-case median-brightness image, lower median on ties: a
        # deterministic, seed-free representative rather than the first file.
        order = np.argsort([s["brightness"] for s in stats])
        pick = int(order[(len(order) - 1) // 2])
        r = dict(group[pick]); r.update(stats[pick])
        e_pick.append(r)
    print(f"  -> {len(e_pick)} case representatives", flush=True)

    # --- authentic screen ---------------------------------------------------
    e_bright = np.array([r["brightness"] for r in e_pick])
    lo, hi = float(e_bright.min()), float(e_bright.max())
    report.append(f"BRIGHTNESS SUPPORT of the 46 counterfeit representatives: "
                  f"[{lo:.3f}, {hi:.3f}]")
    report.append("")

    screen, survivors = [], []
    for n, d in enumerate(dl, start=1):
        cid = d["candidate_id"]
        m = manifest.get(cid, {})
        path = RAW / d["relpath"]
        row = {"candidate_id": cid, "commons_title": d["commons_title"],
               "page_url": m.get("page_url", ""),
               "licence_short": m.get("licence_short", ""),
               "artist": m.get("artist", ""),
               "query_term": m.get("query_term", "")}
        try:
            s = image_stats(path)
        except Exception as exc:                        # noqa: BLE001
            row.update({"decision": "exclude", "exclusion_code": "A_UNREADABLE",
                        "reason": str(exc)[:120]})
            screen.append(row)
            continue
        row.update({k: v for k, v in s.items()})

        text = f"{d['commons_title']} {m.get('credit', '')}"
        code = reason = ""
        if TITLE_BLOCK.search(text):
            code, reason = "A_TITLE_EXCLUDED", TITLE_BLOCK.search(text).group(0)
        elif s["min_side"] < INGEST_SHORT_SIDE // 2:
            code = "A_TOO_SMALL"
            reason = f"min side {s['min_side']} px"
        elif is_flat(s, th):
            code = "A_NOT_PHOTOGRAPH"
            reason = (f"grad {s['grad']:.4f}, white {s['near_white_frac']:.2f}, "
                      f"colours {s['quantized_colours']}")
        elif not (lo <= s["brightness"] <= hi):
            code = "A_ACQUISITION_OUT_OF_BAND"
            reason = (f"brightness {s['brightness']:.3f} outside the "
                      f"counterfeit support [{lo:.3f}, {hi:.3f}]")

        row["decision"] = "exclude" if code else "include"
        row["exclusion_code"] = code
        row["reason"] = reason
        row["path"] = str(path)
        screen.append(row)
        if not code:
            survivors.append(row)
        if n % 200 == 0:
            print(f"  screened {n}/{len(dl)}, {len(survivors)} surviving",
                  flush=True)

    print(f"screen: {len(survivors)}/{len(dl)} survive the content screens",
          flush=True)

    # --- independence -------------------------------------------------------
    print("hashing the reference tree (every image under data/raw)", flush=True)
    ref = []
    for p in sorted(RAW.rglob("*")):
        if p.suffix.lower() in IMAGE_SUFFIXES and "balanced_authentic" not in p.parts:
            try:
                ref.append((p, rotation_canonical_hash(p)))
            except Exception:                            # noqa: BLE001
                pass
    print(f"  {len(ref)} reference images", flush=True)

    kept, nearest_overall = [], (10**9, None, None)
    seen_hashes = []
    for row in survivors:
        try:
            h = rotation_canonical_hash(Path(row["path"]))
        except Exception:                                # noqa: BLE001
            row["decision"], row["exclusion_code"] = "exclude", "A_UNREADABLE"
            continue
        d_pool = min(((hamming(h, rh), rp) for rp, rh in ref),
                     key=lambda t: t[0])
        row["min_hamming_to_pool"] = d_pool[0]
        if d_pool[0] < nearest_overall[0]:
            nearest_overall = (d_pool[0], row["candidate_id"], d_pool[1])
        if d_pool[0] <= HAMMING_THRESHOLD:
            row["decision"], row["exclusion_code"] = "exclude", "A_NEAR_DUPLICATE_POOL"
            row["reason"] = f"Hamming {d_pool[0]} to {d_pool[1].name}"
            continue
        dup = next((c for c, hh in seen_hashes
                    if hamming(h, hh) <= HAMMING_THRESHOLD), None)
        if dup:
            row["decision"], row["exclusion_code"] = "exclude", "A_NEAR_DUPLICATE_WITHIN"
            row["reason"] = f"near-duplicate of {dup}"
            continue
        seen_hashes.append((row["candidate_id"], h))
        kept.append(row)

    report.append("INDEPENDENCE")
    report.append(f"  reference set: {len(ref)} images, every image under "
                  f"data/raw (Kaggle, Roboflow, Mendeley C/D, iphone11pro, "
                  f"synthetic, Split E)")
    report.append(f"  threshold: {HAMMING_THRESHOLD}/64 bits, as 03_dedup.py, "
                  f"step 07 and step 25")
    n_dup = sum(1 for r in survivors
                if r.get("exclusion_code") == "A_NEAR_DUPLICATE_POOL")
    report.append(f"  candidates matching the pool within threshold: {n_dup} "
                  f"of {len(survivors)}")
    report.append(f"  closest approach: Hamming {nearest_overall[0]} "
                  f"({nearest_overall[1]} vs "
                  f"{nearest_overall[2].name if nearest_overall[2] else '-'})")
    report.append(f"  eligible after every screen: {len(kept)}")
    report.append("")
    print(f"independence: {len(kept)} eligible", flush=True)


    # --- contact sheets and the review template -----------------------------
    # The subject-matter review is the one screen no statistic here can stand
    # in for, so this step ends by making it as cheap as possible to perform
    # and as easy as possible to overrule: a numbered contact sheet per 36
    # candidates, and a CSV pre-filled with one row per eligible candidate.
    kept.sort(key=lambda r: r["candidate_id"])
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    for old in SHEETS_DIR.glob("*.png"):
        old.unlink()

    cell, cols, rows_per = 200, 6, 6
    per_sheet = cols * rows_per
    for start in range(0, len(kept), per_sheet):
        chunk = kept[start:start + per_sheet]
        sheet = Image.new("RGB", (cell * cols, cell * rows_per), "white")
        for j, row in enumerate(chunk):
            try:
                with Image.open(row["path"]) as im:
                    im = im.convert("RGB")
                    im.thumbnail((cell - 4, cell - 4), Image.LANCZOS)
                    sheet.paste(im, ((j % cols) * cell + 2,
                                     (j // cols) * cell + 2))
            except Exception:                              # noqa: BLE001
                pass
        n = start // per_sheet + 1
        sheet.save(SHEETS_DIR / f"sheet_{n:02d}.png")
        idx = SHEETS_DIR / f"sheet_{n:02d}.txt"
        idx.write_text("\n".join(
            f"{j:>2}  r{j // cols}c{j % cols}  {r['candidate_id']}  "
            f"{r['commons_title']}" for j, r in enumerate(chunk)),
            encoding="utf-8")
    n_sheets = (len(kept) + per_sheet - 1) // per_sheet
    print(f"wrote {n_sheets} contact sheets to "
          f"{SHEETS_DIR.relative_to(ROOT)}", flush=True)

    with open(REVIEW_TEMPLATE, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["candidate_id", "sheet", "cell",
                                           "commons_title", "decision",
                                           "exclusion_code", "reason"])
        w.writeheader()
        for i, r in enumerate(kept):
            w.writerow({"candidate_id": r["candidate_id"],
                        "sheet": f"sheet_{i // per_sheet + 1:02d}",
                        "cell": f"r{(i % per_sheet) // cols}c{i % cols}",
                        "commons_title": r["commons_title"],
                        "decision": "", "exclusion_code": "", "reason": ""})

    for r in kept:
        r["decision"] = "pending_review"

    scr_fields = sorted({k for r in screen for k in r})
    with open(SCREEN_OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=scr_fields)
        w.writeheader()
        w.writerows(screen)

    import collections
    counts = collections.Counter(r.get("exclusion_code", "") for r in screen)
    report.append("AUTOMATED SCREEN OUTCOME (authentic candidates)")
    report.append(f"  downloaded: {len(dl)}")
    for code, k in sorted(counts.items(), key=lambda t: -t[1]):
        report.append(f"    {code or '(passes every automated screen)':<34} {k}")
    report.append(f"  eligible, pending subject-matter review: {len(kept)}")
    report.append(f"  contact sheets: {n_sheets}")
    report.append("")
    report.append("NEXT: record a subject-matter decision per candidate in")
    report.append("  data/metadata/balanced_external_review.csv")
    report.append("then run scripts/33_apply_review_and_build.py.")

    REPORT_OUT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n" + "\n".join(report))
    print(f"\nwrote {SCREEN_OUT.relative_to(ROOT)} and "
          f"{REVIEW_TEMPLATE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Step 28 — Download the harvested candidates, extract the photographs out of the
alert PDFs, and strip everything that is not an alert photograph.

Step 27 collects every image URL on each alert page. Most of them are not alert
imagery: WHO's page template carries related-story thumbnails, campaign banners
and the organisation emblem, and those appear on many pages at once. Four
filters run here, in this order, each recorded so the attrition is auditable:

  F0 PDF        a harvested PDF is opened and its embedded raster images are
                pulled out as individual candidates. WHO moved to PDF-only
                alerts around 2022, so without this the last five years of the
                archive contribute nothing. A raster that repeats on several
                pages of the same PDF is the letterhead and is dropped here.
  F1 CHROME     the same image URL (or the same bytes) appears on more than
                MAX_PAGES distinct alert pages. A photograph of one seizure of
                one product does not appear on six unrelated alerts; a template
                asset does. This is the filter that removes most of the harvest.
  F2 TOO_SMALL  min side below MIN_SIDE px. Icons and social buttons.
  F3 BYTE_DUP   identical SHA-256 to a candidate already kept, including the
                57 images step 24 already fetched. The alert archive re-uses
                photographs across related alerts (the 2013 and 2014 Coartem
                alerts, the two Defitelio alerts), so this fires on real
                photographs too, not only on chrome.
  F4 POOL_DUP   rotation-canonical pHash within HAMMING_THRESHOLD of anything
                under data/raw, which now includes the existing Split E images.
                Same procedure and threshold as 03_dedup.py and step 25.

What survives is a *candidate*, not a Split E member. It still has to pass the
step-25 eligibility screen, which is a recorded human judgement about what the
frame actually shows, and which this script cannot and does not make.

Output
------
  data/raw/split_e_harvested/HV_XXXXXX.<ext>   (gitignored; WHO bytes are not
    redistributable, see step 24's header)
  data/metadata/split_e_harvest_download_log.csv — every harvested URL with the
    filter that removed it, or `kept`.
"""
import csv
import hashlib
import io
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

import imagehash
import numpy as np
import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT_DIR = RAW / "split_e_harvested"
HARVEST = ROOT / "data" / "metadata" / "split_e_harvest_manifest.csv"
LOG_OUT = ROOT / "data" / "metadata" / "split_e_harvest_download_log.csv"

USER_AGENT = "pharmavision-research/1.0 (external-validation set construction)"
DELAY_S = 0.35
MAX_PAGES = 2          # an image on 3+ alert pages is template chrome
MIN_SIDE = 120         # px
MAX_PDF_PAGES_FOR_RASTER = 1   # a raster on >1 page of one PDF is letterhead
HAMMING_THRESHOLD = 8  # same as 03_dedup.py, step 07, step 25
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png")
EXT_BY_FORMAT = {"PNG": ".png", "JPEG": ".jpg", "GIF": ".gif", "WEBP": ".webp"}

FIELDNAMES = ["candidate_id", "source_organization", "alert_title", "alert_url",
              "image_url", "status", "filter", "bytes", "sha256", "format",
              "width", "height", "min_side", "stored_relpath",
              "n_alert_pages", "nearest_pool_match", "min_hamming_to_pool",
              "image_license", "redistribution_status"]


def rotation_canonical_hash_im(im) -> int:
    im = im.convert("RGB")
    return min(int(str(imagehash.phash(im.rotate(a, expand=True))), 16)
               for a in (0, 90, 180, 270))


def rotation_canonical_hash(path: Path) -> int:
    with Image.open(path) as im:
        return rotation_canonical_hash_im(im)


def pdf_rasters(body, candidate_id):
    """Embedded raster images of a WHO alert PDF, minus the letterhead.

    Returns (suffix, png_bytes, width, height). Images are re-encoded to PNG so
    that everything downstream sees one lossless format regardless of how the
    PDF stored them; CMYK and separation colourspaces are converted to RGB,
    which pymupdf will not do implicitly.
    """
    out = []
    with pymupdf.open(stream=body, filetype="pdf") as doc:
        pages_per_xref = {}
        for pno in range(doc.page_count):
            for info in doc[pno].get_images(full=True):
                pages_per_xref.setdefault(info[0], set()).add(pno)
        for xref, pages in sorted(pages_per_xref.items()):
            if len(pages) > MAX_PDF_PAGES_FOR_RASTER:
                continue  # letterhead / footer mark
            try:
                px = pymupdf.Pixmap(doc, xref)
                if px.n - px.alpha >= 4:          # CMYK or separation
                    px = pymupdf.Pixmap(pymupdf.csRGB, px)
                out.append((f"_x{xref}", px.tobytes("png"), px.width, px.height))
            except Exception:  # noqa: BLE001 - a broken xref is not fatal
                continue
    return out


def fetch(url):
    safe = urllib.parse.quote(url, safe=":/?=&%#")
    req = urllib.request.Request(safe, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(HARVEST, newline="", encoding="utf-8")))
    print(f"{len(rows)} harvested URLs")

    # --- F1a: URL appearing on many alert pages ------------------------------
    pages_per_url = defaultdict(set)
    for r in rows:
        pages_per_url[r["image_url"]].add(r["alert_url"])

    # One row per distinct URL; keep the first alert that referenced it.
    by_url = {}
    for r in rows:
        by_url.setdefault(r["image_url"], r)
    print(f"{len(by_url)} distinct URLs")

    log = []
    kept = []          # (candidate_id, path, hash)
    seen_sha = {}

    # Byte hashes of the images step 24 already fetched, so F3 is checked
    # against the existing Split E candidates too, not only within this harvest.
    existing_dir = RAW / "split_e_regulatory"
    for p in sorted(existing_dir.glob("*")):
        if p.suffix.lower() in IMAGE_SUFFIXES:
            seen_sha[hashlib.sha256(p.read_bytes()).hexdigest()] = p.stem

    for i, (url, r) in enumerate(sorted(by_url.items()), 1):
        entry = {k: r.get(k, "") for k in
                 ("candidate_id", "source_organization", "alert_title",
                  "alert_url", "image_url", "image_license",
                  "redistribution_status")}
        entry["n_alert_pages"] = len(pages_per_url[url])
        entry.update({"status": "", "filter": "", "bytes": 0, "sha256": "",
                      "format": "", "width": "", "height": "", "min_side": "",
                      "stored_relpath": "", "nearest_pool_match": "",
                      "min_hamming_to_pool": ""})

        if entry["n_alert_pages"] > MAX_PAGES:
            entry.update(status="dropped", filter="F1_CHROME")
            log.append(entry)
            continue

        try:
            body = fetch(url)
        except Exception as exc:  # noqa: BLE001
            entry.update(status="dropped", filter=f"FETCH_FAIL:{type(exc).__name__}")
            log.append(entry)
            time.sleep(DELAY_S)
            continue
        time.sleep(DELAY_S)

        # One harvested resource yields one image, or -- for a PDF -- several.
        if r.get("resource_type") == "pdf":
            try:
                rasters = pdf_rasters(body, r["candidate_id"])
            except Exception as exc:  # noqa: BLE001
                entry.update(status="dropped", filter=f"PDF_FAIL:{type(exc).__name__}")
                log.append(entry)
                continue
            if not rasters:
                entry.update(status="dropped", filter="F0_PDF_NO_RASTER")
                log.append(entry)
                continue
            units = [(f"{r['candidate_id']}{sfx}", png, "PNG", w, h)
                     for sfx, png, w, h in rasters]
        else:
            try:
                with Image.open(io.BytesIO(body)) as im:
                    fmt, (w, h) = im.format, im.size
            except Exception as exc:  # noqa: BLE001
                entry.update(status="dropped", filter=f"DECODE_FAIL:{type(exc).__name__}")
                log.append(entry)
                continue
            units = [(r["candidate_id"], body, fmt, w, h)]

        for cid, blob, fmt, w, h in units:
            e = dict(entry)
            e.update(candidate_id=cid, bytes=len(blob), format=fmt, width=w,
                     height=h, min_side=min(w, h),
                     sha256=hashlib.sha256(blob).hexdigest())
            if min(w, h) < MIN_SIDE:
                e.update(status="dropped", filter="F2_TOO_SMALL")
                log.append(e)
                continue
            if e["sha256"] in seen_sha:
                e.update(status="dropped",
                         filter=f"F3_BYTE_DUP_OF:{seen_sha[e['sha256']]}")
                log.append(e)
                continue
            path = OUT_DIR / f"{cid}{EXT_BY_FORMAT.get(fmt, '.bin')}"
            path.write_bytes(blob)
            seen_sha[e["sha256"]] = cid
            e["stored_relpath"] = f"split_e_harvested/{path.name}"
            e.update(status="kept_pending_dedup")
            kept.append((cid, path, e))
            log.append(e)
        if i % 25 == 0:
            print(f"  {i}/{len(by_url)}  kept so far: {len(kept)}", flush=True)

    print(f"\n{len(kept)} images survive F1-F3; running F4 pHash dedup...")

    # --- F4: near-duplicate of anything already under data/raw ---------------
    reference = sorted(p for p in RAW.rglob("*")
                       if p.suffix.lower() in IMAGE_SUFFIXES
                       and OUT_DIR not in p.parents)
    print(f"  reference pool: {len(reference)} images")
    ref_h = np.array([np.uint64(rotation_canonical_hash(p)) for p in reference],
                     dtype=np.uint64)

    cand_h = []
    for cid, path, entry in kept:
        h = np.uint64(rotation_canonical_hash(path))
        dist = np.bitwise_count(np.bitwise_xor(ref_h, h))
        j = int(np.argmin(dist))
        entry["min_hamming_to_pool"] = int(dist[j])
        entry["nearest_pool_match"] = str(reference[j].relative_to(RAW)).replace("\\", "/")
        if dist[j] <= HAMMING_THRESHOLD:
            # Clear stored_relpath together with the unlink. Leaving it set
            # advertises a file that is no longer on disk, and step 26 duly
            # crashed on one; a dropped row must not name a path.
            entry.update(status="dropped", filter="F4_POOL_DUP",
                         stored_relpath="")
            path.unlink()
        else:
            cand_h.append((cid, path, entry, int(h)))

    # and against each other
    final = []
    for cid, path, entry, h in cand_h:
        clash = next((c for c, _, _, hh in final
                      if bin(h ^ hh).count("1") <= HAMMING_THRESHOLD), None)
        if clash:
            entry.update(status="dropped", filter=f"F4_HARVEST_DUP_OF:{clash}",
                         stored_relpath="")
            path.unlink()
        else:
            entry.update(status="kept")
            final.append((cid, path, entry, h))

    with open(LOG_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(log)

    counts = defaultdict(int)
    for e in log:
        counts[e["filter"].split(":")[0] or e["status"]] += 1
    print("\nAttrition:")
    for k in sorted(counts):
        print(f"  {k:<22} {counts[k]:>4}")
    print(f"\n{len(final)} new candidates in {OUT_DIR}")
    print(f"Wrote {LOG_OUT}")


if __name__ == "__main__":
    main()

"""
Step 31 — Download the harvested authentic candidates.

Downloads at a bounded width rather than at native size. Commons originals for
this material run to 20 MB and 6000 px, and nothing downstream can use that:
the models resize to 224 px (modeling/common.py, IMG_SIZE) and step 32 ingests
both classes at a 448 px short side. Fetching a 1024 px rendition is enough for
every screen step 32 runs and is a courtesy to the API.

That choice has a consequence worth stating plainly, because it is the kind of
thing this paper exists to catch: the *encoded file size and stored dimensions*
of an authentic candidate as it lands on disk here are a property of this
download step, not of the photograph. They are therefore useless as acquisition
evidence, and step 32 does not use them -- it normalises both classes to one
size and one encoder before anything is measured, so that the audit it runs on
the finished set reports the residual, not this script's artefacts.

Byte-identical repeats are collapsed by SHA-256 before anything else; the
Commons search returns the same file under several product terms.

WHY A PRE-DOWNLOAD FILTER EXISTS, AND WHAT IT MAY AND MAY NOT DO
----------------------------------------------------------------
Step 30 returns some 3,700 candidates and the set needs 46. Downloading all of
them would take hours and gigabytes for no gain, so two filters run here, on
manifest fields alone, before any byte is fetched:

  * TITLE_BLOCK -- the title or credit names the file as something other than a
    photograph of a product (chemical structure, logo, chart, package insert).
    Commons files a great deal of that in drug categories.
  * a minimum native short side, and a per-product-term cap so that no single
    search term can dominate the pool.

Both are recorded in the log as `prefiltered` with the reason, so the screen
step 32 reports covers every candidate step 30 found and not only the ones that
were fetched. Neither filter reads a pixel and neither can see a class label:
every candidate here is authentic, so no filter applied at this stage can move
the two classes relative to each other. The screens that *could* -- brightness
band, flatness, near-duplicate -- are all in step 32, applied after download,
where they are recorded per image with a reason.

Output
------
  data/raw/balanced_authentic/<candidate_id>.<ext>   (gitignored)
  data/metadata/balanced_authentic_download_log.csv
"""
import collections
import csv
import hashlib
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "metadata" / "balanced_authentic_harvest_manifest.csv"
OUTDIR = ROOT / "data" / "raw" / "balanced_authentic"
LOG = ROOT / "data" / "metadata" / "balanced_authentic_download_log.csv"

API = "https://commons.wikimedia.org/w/api.php"
UA = ("pharmavision-provenance-audit/1.0 "
      "(academic dataset audit; sophiezhu2028@gmail.com)")
THUMB_WIDTH = 1024
SLEEP = 0.35
RETRIES = 4

MIN_NATIVE_SHORT_SIDE = 300     # step 32 ingests at 448; below this it upsamples
PER_TERM_CAP = 24               # no one search term may dominate the pool
WORKERS = 8                     # concurrent fetches; the API calls stay serial

# Kept identical to step 32's TITLE_BLOCK. Duplicated rather than imported
# because a `scripts.` package would have to exist for the import and the two
# steps are meant to be runnable on their own; step 32 re-applies it anyway, so
# a drift between the two would show up there as an extra exclusion, not as a
# silent inclusion.
TITLE_BLOCK = re.compile(
    r"\b(structure|structural|molecul|skeletal|formula|chemical|synthesis|"
    r"reaction|logo|icon|diagram|chart|graph|plot|map|schema|flowchart|"
    r"poster|leaflet|insert|advert|banner|signature|portrait|statue|"
    r"building|pharmacy shop|protest|meme|screenshot|scan of)\b",
    re.IGNORECASE)

FIELDS = ["candidate_id", "commons_title", "status", "relpath", "sha256",
          "bytes", "fetched_url", "note"]


def api(**kw):
    kw.setdefault("format", "json")
    kw.setdefault("action", "query")
    kw.setdefault("formatversion", "2")
    url = API + "?" + urllib.parse.urlencode(kw)
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as fh:
                payload = json.load(fh)
            time.sleep(SLEEP)
            return payload
        except Exception:                              # noqa: BLE001
            time.sleep(2.0 * (attempt + 1))
    return {}


def thumb_urls(titles):
    """Map title -> a rendition at most THUMB_WIDTH wide, 50 titles per call."""
    out = {}
    titles = list(titles)
    for i in range(0, len(titles), 50):
        d = api(titles="|".join(titles[i:i + 50]), prop="imageinfo",
                iiprop="url|size|mime", iiurlwidth=THUMB_WIDTH)
        for p in d.get("query", {}).get("pages", []):
            ii = (p.get("imageinfo") or [{}])[0]
            # Thumbnail only, never the original. The first version of this
            # fell back to `ii["url"]` when no thumburl came back, which pulled
            # 13 MB originals one at a time and made the step take hours; a
            # candidate with no rendition is simply skipped instead.
            if ii and ii.get("thumburl"):
                out[p["title"]] = ii["thumburl"]
        print(f"    thumburl {min(i + 50, len(titles))}/{len(titles)}",
              flush=True)
    return out


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=60) as fh:
                return fh.read()
        except Exception:                              # noqa: BLE001
            time.sleep(1.5 * (attempt + 1))
    return None


def main():
    if not MANIFEST.exists():
        print(f"missing {MANIFEST}; run step 30 first")
        return 1
    all_rows = list(csv.DictReader(open(MANIFEST, newline="", encoding="utf-8")))
    print(f"{len(all_rows)} candidates in the manifest", flush=True)

    log = []
    rows, per_term = [], collections.Counter()
    for r in all_rows:
        text = f"{r['commons_title']} {r.get('credit', '')}"
        hit = TITLE_BLOCK.search(text)
        why = ""
        if hit:
            why = f"title/credit names '{hit.group(0)}'"
        elif int(r["min_side"] or 0) < MIN_NATIVE_SHORT_SIDE:
            why = f"native short side {r['min_side']} px"
        elif per_term[r["query_term"]] >= PER_TERM_CAP:
            why = f"per-term cap {PER_TERM_CAP} reached for '{r['query_term']}'"
        if why:
            log.append({"candidate_id": r["candidate_id"],
                        "commons_title": r["commons_title"],
                        "status": "prefiltered", "relpath": "", "sha256": "",
                        "bytes": "", "fetched_url": "", "note": why})
            continue
        per_term[r["query_term"]] += 1
        rows.append(r)
    print(f"pre-filtered to {len(rows)} across {len(per_term)} product terms "
          f"({len(all_rows) - len(rows)} dropped without fetching)", flush=True)

    OUTDIR.mkdir(parents=True, exist_ok=True)
    print("resolving renditions", flush=True)
    thumbs = thumb_urls([r["commons_title"] for r in rows])

    # Fetched in a small thread pool. Serially this step took hours, which is
    # not a courtesy to the API so much as a courtesy to nobody: eight
    # concurrent connections to a CDN edge is ordinary traffic, and the API
    # calls above are still serial and still rate-limited.
    from concurrent.futures import ThreadPoolExecutor

    def one(r):
        cid = r["candidate_id"]
        url = thumbs.get(r["commons_title"])
        base = {"candidate_id": cid, "commons_title": r["commons_title"],
                "relpath": "", "sha256": "", "bytes": "",
                "fetched_url": url or "", "note": ""}
        if not url:
            return {**base, "status": "no_url",
                    "note": "no thumbnail rendition returned by the API"}
        ext = ".png" if url.lower().endswith(".png") else ".jpg"
        path = OUTDIR / f"{cid}{ext}"
        if path.exists() and path.stat().st_size:      # resume
            blob = path.read_bytes()
        else:
            blob = fetch(url)
            if not blob:
                return {**base, "status": "fetch_failed"}
            path.write_bytes(blob)
        return {**base, "status": "ok",
                "relpath": f"balanced_authentic/{path.name}",
                "sha256": hashlib.sha256(blob).hexdigest(),
                "bytes": len(blob)}

    fetched = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for n, rec in enumerate(pool.map(one, rows), start=1):
            fetched.append(rec)
            if n % 50 == 0:
                print(f"  {n}/{len(rows)}", flush=True)

    # De-duplicate by content afterwards rather than inside the pool, so the
    # verdict does not depend on which thread finished first.
    by_hash = {}
    ok = dup = fail = 0
    for rec in fetched:
        if rec["status"] != "ok":
            fail += 1
            log.append(rec)
            continue
        first = by_hash.get(rec["sha256"])
        if first:
            Path(ROOT / "data" / "raw" / rec["relpath"]).unlink(missing_ok=True)
            log.append({**rec, "status": "byte_duplicate", "relpath": "",
                        "note": f"identical to {first}"})
            dup += 1
            continue
        by_hash[rec["sha256"]] = rec["candidate_id"]
        log.append(rec)
        ok += 1

    with open(LOG, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(log)

    print(f"\nok {ok}, byte-duplicate {dup}, failed {fail}")
    print(f"wrote {LOG.relative_to(ROOT)}")
    print("Nothing is selected yet. Step 32 screens and builds the set.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Step 30 — Harvest independent authentic candidates for the balanced external test.

WHY THIS SOURCE, AND WHY NOT ANY OF THE ONES ALREADY HERE
---------------------------------------------------------
The balanced external test needs an authentic class that is (a) independent of
the modelling pool, (b) independent of the counterfeit class's source, and
(c) not acquisition-separable from it. Every source already in this project
fails at least one:

  * Splits C and D (Mendeley). Independent of the pool, but their acquisition
    statistics are nowhere near Split E's. Split C sits at brightness 0.162 and
    a 2448 px median short side against Split E's 0.558 and 439 px. Pairing
    them would produce a class-acquisition gap of +0.396 in brightness alone --
    larger than the +0.233 gap that caused step 25 to discard the regulatory
    manifest's own authentic class. Splits C and D are the acquisition-shift
    experiment and stay there.
  * The regulatory archives (Split E's own source). Step 25 screened nine
    authentic-labelled candidates and excluded eight as X_NOT_PHOTOGRAPH: flat
    vector carton artwork against field photographs for every falsified one.
    A regulator publishes photographs of what it seized and artwork of what the
    genuine article looks like. That asymmetry is structural, not an accident
    of this harvest, and re-adding the artwork is the one thing this project
    must not do.
  * Roboflow. 42.3% of the Kaggle pool has a near-duplicate in it, so it is not
    external at all.

Wikimedia Commons is used instead: a third-party photographic archive, no
relationship to any source above, per-file licence and authorship recorded at
the point of upload, and photographs rather than manufacturer artwork.

PRODUCT MATCHING
----------------
Candidates are not harvested at random. Split E's 46 regulatory cases name
their products in the alert titles, and PRODUCT_QUERIES below is that list
turned into search terms -- brand names, INNs and, where the alert names a
class rather than a product ("falsified antimalarial medicines"), the class.
Harvesting authentic exemplars of the same products is what makes the two
classes comparable in product type rather than only in count.

WHAT THIS STEP DOES NOT DO
--------------------------
It does not select the 46. It records every candidate it can find, with
licence, author and source URL, and step 31 screens them. Keeping harvest and
screen in separate steps is what lets the screen be re-run, overruled or
widened without re-hitting the API, exactly as steps 27-28 and step 25 are
separated for Split E.

Output
------
  data/metadata/balanced_authentic_harvest_manifest.csv
"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "metadata" / "balanced_authentic_harvest_manifest.csv"

API = "https://commons.wikimedia.org/w/api.php"
UA = ("pharmavision-provenance-audit/1.0 "
      "(academic dataset audit; sophiezhu2028@gmail.com)")
SLEEP = 0.5          # courtesy delay between API calls
RETRIES = 5

# One entry per Split E regulatory case product, read off the alert titles in
# data/metadata/split_e_candidate_provenance.csv. Where an alert names a class
# rather than a brand, the class is used, because Commons categorises by
# substance rather than by the regulator's wording.
PRODUCT_QUERIES = [
    "Augmentin", "amoxicillin", "amoxicillin clavulanate", "penicillin V",
    "meningococcal vaccine", "meningitis vaccine", "yellow fever vaccine",
    "hepatitis B vaccine", "COVID-19 vaccine AstraZeneca", "Covishield",
    "Comirnaty", "COVID-19 vaccine vial", "diazepam", "phenobarbital",
    "oxycodone OxyContin", "oxymorphone", "remdesivir", "daratumumab",
    "defibrotide", "basiliximab", "vitamin A capsules", "propylene glycol",
    "durvalumab", "bevacizumab Avastin", "sunitinib Sutent",
    "levonorgestrel emergency contraceptive", "semaglutide Ozempic",
    "quinine sulfate", "botulinum toxin Dysport",
    "artemether lumefantrine", "antimalarial tablets", "sofosbuvir",
    "propofol Diprivan", "human normal immunoglobulin",
    # generic packaging terms, to widen the pool where a product returns little
    "medicine box package", "medication carton", "blister pack tablets",
    "pharmaceutical packaging photograph", "drug packaging box",
    "medicine bottle label", "vaccine vial box", "tablet strip package",
]

# Walked to depth 2. Commons files a great deal of packaging imagery by
# substance rather than by any packaging category, which is why the search
# above carries most of the load and these are a supplement.
SEED_CATEGORIES = [
    "Category:Blister packs",
    "Category:Tablets (pharmacy)",
    "Category:Drug packaging",
    "Category:Pharmaceutical products",
    "Category:Medicine bottles",
]
CATEGORY_DEPTH = 2

# SVG is excluded at the API level rather than at the screen: a vector file is
# the exact failure mode that disqualified the regulatory manifest's authentic
# class, and there is no reading of this project under which one belongs here.
WANTED_MIME = {"image/jpeg", "image/png"}

FIELDS = ["candidate_id", "commons_title", "page_url", "image_url",
          "mime", "width", "height", "min_side", "file_size_bytes",
          "licence_short", "licence_url", "artist", "credit",
          "upload_date", "found_via", "query_term", "harvest_date"]


def api(**kw):
    kw.setdefault("format", "json")
    kw.setdefault("action", "query")
    kw.setdefault("formatversion", "2")
    url = API + "?" + urllib.parse.urlencode(kw)
    last = None
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=45) as fh:
                payload = json.load(fh)
            time.sleep(SLEEP)
            return payload
        except Exception as exc:                      # noqa: BLE001
            last = exc
            time.sleep(2.0 * (attempt + 1))
    print(f"    API FAILED after {RETRIES} tries: {last}", flush=True)
    return {}


def strip_html(s):
    out, depth = [], 0
    for ch in s or "":
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return " ".join("".join(out).split())


def imageinfo(titles):
    """Licence, authorship, size and direct URL for up to 50 titles at a time."""
    got = {}
    titles = list(titles)
    for i in range(0, len(titles), 50):
        chunk = titles[i:i + 50]
        d = api(titles="|".join(chunk), prop="imageinfo",
                iiprop="url|size|mime|extmetadata|timestamp")
        for p in d.get("query", {}).get("pages", []):
            ii = (p.get("imageinfo") or [{}])[0]
            if not ii:
                continue
            ex = ii.get("extmetadata", {})

            def meta(key):
                return strip_html((ex.get(key) or {}).get("value", ""))

            got[p["title"]] = {
                "commons_title": p["title"],
                "page_url": ii.get("descriptionurl", ""),
                "image_url": ii.get("url", ""),
                "mime": ii.get("mime", ""),
                "width": ii.get("width", 0),
                "height": ii.get("height", 0),
                "min_side": min(ii.get("width", 0) or 0,
                                ii.get("height", 0) or 0),
                "file_size_bytes": ii.get("size", 0),
                "licence_short": meta("LicenseShortName"),
                "licence_url": meta("LicenseUrl"),
                "artist": meta("Artist")[:200],
                "credit": meta("Credit")[:200],
                "upload_date": ii.get("timestamp", ""),
            }
        print(f"    imageinfo {min(i + 50, len(titles))}/{len(titles)}",
              flush=True)
    return got


def search_titles(term, limit=60):
    d = api(list="search", srsearch="filetype:bitmap " + term,
            srnamespace=6, srlimit=limit)
    return [r["title"] for r in d.get("query", {}).get("search", [])]


def category_titles(cat, depth, seen):
    if cat in seen or depth < 0:
        return []
    seen.add(cat)
    d = api(list="categorymembers", cmtitle=cat, cmtype="file|subcat",
            cmlimit=500)
    files, subcats = [], []
    for m in d.get("query", {}).get("categorymembers", []):
        (files if m["ns"] == 6 else subcats).append(m["title"])
    if depth > 0:
        for sc in subcats[:25]:    # bounded: Commons subcategory fan-out is wide
            files += category_titles(sc, depth - 1, seen)
    return files


def main():
    harvest_date = time.strftime("%Y-%m-%d")
    found = {}      # title -> (found_via, query_term)

    print(f"searching {len(PRODUCT_QUERIES)} product terms", flush=True)
    for term in PRODUCT_QUERIES:
        titles = search_titles(term)
        new = [t for t in titles if t not in found]
        for t in titles:
            found.setdefault(t, ("search", term))
        print(f"  {term:<45} {len(titles):>3} hits, {len(new):>3} new",
              flush=True)

    print(f"\nwalking {len(SEED_CATEGORIES)} category trees to depth "
          f"{CATEGORY_DEPTH}", flush=True)
    seen = set()
    for cat in SEED_CATEGORIES:
        titles = category_titles(cat, CATEGORY_DEPTH, seen)
        new = [t for t in titles if t not in found]
        for t in titles:
            found.setdefault(t, ("category", cat))
        print(f"  {cat:<45} {len(titles):>4} files, {len(new):>4} new",
              flush=True)

    print(f"\n{len(found)} distinct titles; fetching imageinfo", flush=True)
    info = imageinfo(found)
    print(f"  imageinfo returned {len(info)}", flush=True)

    rows = []
    for n, (title, rec) in enumerate(sorted(info.items()), start=1):
        if rec["mime"] not in WANTED_MIME:
            continue
        via, term = found[title]
        rec.update({"candidate_id": f"BA_{n:06d}", "found_via": via,
                    "query_term": term, "harvest_date": harvest_date})
        rows.append(rec)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    print(f"\nwrote {OUT.relative_to(ROOT)}: {len(rows)} bitmap candidates "
          f"({len(info) - len(rows)} non-bitmap dropped at the API level)")
    print("Nothing is selected yet. Step 31 screens these.")


if __name__ == "__main__":
    sys.exit(main())

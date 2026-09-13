"""
Step 27 — Harvest additional Split E candidates from the regulatory alert
archives, so the set is large enough to evaluate on.

Why this step exists
--------------------
The delivered manifest names 57 retrievable images, of which 28 survive the
step-25 eligibility screen. Its remaining 143 rows are `source_photo_queue`
placeholders, and they are not usable as delivered: all 143 carry the same
generic index URL (`.../regulation-prequalification/incidents`) rather than a
specific alert, and 22 of the 34 cases name a product with no alert page at all.
So the queue cannot be "downloaded"; the alert pages have to be located first.

That is what this script does. It reads WHO's own full-alert index and FDA's
counterfeit-medicine index, keeps the alerts whose titles asserts FALSIFICATION
(never "substandard" — the package's own current-source review corrected
CASE_0033 for exactly this reason, and a substandard product is not a
counterfeit), fetches each alert page, and extracts every image resource it points at.

Two resource kinds, because WHO changed how it publishes. Alerts up to roughly
2021 embed the product photographs inline as <img> on the news page. From about
2022 the news page carries only boilerplate and links a PDF, and the photographs
live inside that PDF. Harvesting only inline images therefore silently loses
most of the last five years of alerts -- the first pass of this script returned
42 distinct URLs across 48 alerts, nearly all of them page furniture, which is
what exposed the change. Both kinds are collected here and resolved in step 28.

What it does NOT do
-------------------
It does not decide what is usable. Every harvested image is a *candidate*; it
must still pass the step-25 independence check and the eligibility screen before
it can enter Split E, and the screen is a recorded human-readable judgement, not
something this script infers. Harvesting more candidates is not the same as
having more data, and the gap between the two is the whole point of steps 25-26.

Rights
------
Identical to step 24: WHO-hosted images are `metadata_only_permission_required`
and are not redistributable; FDA-hosted images are public domain under FDA's
website policy subject to a per-image exception check. Bytes land in
`data/raw/`, which is gitignored. The repository ships this script and the
resulting URL manifest, never the WHO bytes.

Output
------
  data/metadata/split_e_harvest_manifest.csv — every candidate image URL found,
    with the alert it came from, the alert's falsification language, and the
    rights status. This is the harvest's manifest; step 24b downloads it.
"""
import csv
import re
import time
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "metadata" / "split_e_harvest_manifest.csv"

WHO_INDEX = ("https://www.who.int/teams/regulation-prequalification/"
             "incidents-and-SF/full-list-of-who-medical-product-alerts")
FDA_INDEX = "https://www.fda.gov/drugs/buying-using-medicine-safely/counterfeit-medicine"

USER_AGENT = "pharmavision-research/1.0 (external-validation set construction)"
DELAY_S = 0.5

# A WHO alert titled "substandard" is not a falsification finding. The delivered
# package had already made this mistake once (CASE_0033, ACCUPAQUE/OMNIPAQUE/
# VISIPAQUE, labelled FALSIFIED when WHO classifies it substandard) and caught it
# in its own current-source review. Encode the rule rather than re-check by hand.
FALSIFIED_RE = re.compile(r"falsified|counterfeit", re.I)
SUBSTANDARD_RE = re.compile(r"substandard", re.I)

# WHO serves alert imagery from these hosts; everything else on the page is
# chrome (logos, social icons, the emblem) and is dropped by size at download.
IMG_SRC_RE = re.compile(r'<img[^>]+src="([^"]+)"', re.I)
IMG_HREF_RE = re.compile(r'href="(https?://(?:cdn\.)?who\.int/[^"]+\.(?:jpg|jpeg|png))"', re.I)
FDA_IMG_RE = re.compile(r'(?:src|href)="((?:https://www\.fda\.gov)?/files/[^"?]+\.(?:png|jpg|jpeg))', re.I)
# From ~2022 WHO publishes the alert, and its photographs, as a linked PDF.
PDF_RE = re.compile(r'(https://cdn\.who\.int/media/docs/[^"\s\')]+\.pdf(?:\?[^"\s\')]*)?)', re.I)

SKIP_URL_PARTS = ("/emblem", "logo", "icon", "sprite", "placeholder",
                  "social-media", "/assets/", "favicon")

FIELDNAMES = ["candidate_id", "source_organization", "alert_title", "alert_url",
              "resource_type", "image_url", "image_license",
              "redistribution_status", "harvest_date"]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "replace")


def absolutise(src, base):
    return urllib.parse.urljoin(base, unescape(src.strip()))


def who_alert_urls():
    """Every WHO medical-product-alert page that asserts falsification."""
    html = get(WHO_INDEX)
    # Titles sit in the anchor text; capture both so the falsified/substandard
    # test can look at the human-readable title, not just the slug.
    pairs = re.findall(r'href="((?:https://www\.who\.int)?/news/item/[^"]+)"[^>]*>([^<]{0,300})',
                       html)
    out = {}
    for href, text in pairs:
        url = absolutise(href, "https://www.who.int/")
        title = unescape(re.sub(r"\s+", " ", text)).strip()
        haystack = f"{url} {title}"
        if not FALSIFIED_RE.search(haystack):
            continue
        if SUBSTANDARD_RE.search(haystack) and not FALSIFIED_RE.search(title):
            continue
        out.setdefault(url, title or url.rsplit("/", 1)[-1])
    return out


def fda_alert_urls():
    """FDA counterfeit-medicine index -> the alert pages it links."""
    html = get(FDA_INDEX)
    hrefs = re.findall(r'href="([^"]+)"', html)
    out = {}
    for h in hrefs:
        if not re.search(r"counterfeit|falsified", h, re.I):
            continue
        url = absolutise(h, FDA_INDEX)
        if "fda.gov" not in url or url.rstrip("/") == FDA_INDEX.rstrip("/"):
            continue
        if any(url.lower().endswith(x) for x in (".pdf", ".zip")):
            continue
        out.setdefault(url, url.rsplit("/", 1)[-1].replace("-", " "))
    return out


def resources_on(url, org):
    """Return (resource_type, absolute_url) pairs: inline images and alert PDFs."""
    html = get(url)
    out = []
    for pdf in dict.fromkeys(PDF_RE.findall(html)):
        # The page embeds the same PDF link in a script string with a trailing
        # backslash as well as in the anchor; normalise before de-duplicating.
        out.append(("pdf", pdf.rstrip("\\")))
    return out + [("image", u) for u in _inline_images(html, url, org)]


def _inline_images(html, url, org):
    found = []
    if org == "WHO":
        for m in IMG_SRC_RE.findall(html):
            found.append(absolutise(m, url))
        found += IMG_HREF_RE.findall(html)
    else:
        for m in FDA_IMG_RE.findall(html):
            found.append(absolutise(m, url))
    seen, keep = set(), []
    for u in found:
        u = u.split("#")[0]
        low = u.lower()
        if any(p in low for p in SKIP_URL_PARTS):
            continue
        if not re.search(r"\.(png|jpe?g)($|\?)", low):
            continue
        if u not in seen:
            seen.add(u)
            keep.append(u)
    return keep


def main():
    today = time.strftime("%Y-%m-%d")
    sources = []
    print("Reading WHO full-alert index...")
    who = who_alert_urls()
    print(f"  {len(who)} WHO alerts asserting falsification")
    sources += [("WHO", u, t) for u, t in sorted(who.items())]

    print("Reading FDA counterfeit-medicine index...")
    try:
        fda = fda_alert_urls()
        print(f"  {len(fda)} FDA counterfeit alert pages")
        sources += [("FDA", u, t) for u, t in sorted(fda.items())]
    except Exception as exc:  # noqa: BLE001
        print(f"  FDA index unavailable ({exc}); continuing with WHO only")

    rows, n = [], 0
    for org, url, title in sources:
        try:
            res = resources_on(url, org)
        except Exception as exc:  # noqa: BLE001
            print(f"  [skip] {url} ({type(exc).__name__})")
            time.sleep(DELAY_S)
            continue
        for rtype, img in res:
            n += 1
            rows.append({
                "candidate_id": f"HV_{n:06d}",
                "source_organization": org,
                "alert_title": title[:200],
                "alert_url": url,
                "resource_type": rtype,
                "image_url": img,
                "image_license": ("public_domain" if org == "FDA"
                                  else "unknown_permission_required"),
                "redistribution_status": (
                    "permitted_pending_per_image_exception_check" if org == "FDA"
                    else "metadata_only_permission_required"),
                "harvest_date": today,
            })
        npdf = sum(1 for t, _ in res if t == "pdf")
        print(f"  {org} {len(res) - npdf:>2} img + {npdf} pdf  {title[:62]}")
        time.sleep(DELAY_S)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(rows)

    print(f"\n{len(rows)} candidate image URLs from {len(sources)} alerts")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()

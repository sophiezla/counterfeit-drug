"""
Step 24 — Fetch the Split E candidate bytes from the regulatory-alert manifest.

Split E is the first candidate external set in this project that carries a
COUNTERFEIT label. Splits C and D are authentic-only by construction (Section
III-E), so every external number the paper reports today is a specificity and
counterfeit recall under acquisition shift is listed in Table 8 as *not
measured*. This script is the first step toward measuring it.

What arrived, and what it is not
--------------------------------
The compiled package (`PharmaChecked_200_license_audited_2026-09-07.zip`) is a
**rights-audited candidate manifest, not an image dataset**: its own
`documentation/CURRENT_VERIFICATION.md` says so, and `images/`, `hashes/` and
`splits/` inside it are empty directories. Of its 188 manifest rows, 131 are
`source_photo_queue` records with no image URL at all. Only 57 rows are
`direct_image_reference`s that name a retrievable file. Those 57 are what this
script fetches.

Rights
------
FDA-hosted files are public domain under FDA's website policy; WHO-hosted files
are `metadata_only_permission_required` and are NOT redistributable. This script
therefore writes bytes only into `data/raw/`, which is gitignored, exactly as
the Mendeley Split C/D downloads are. The repository ships the manifest and this
script, never the WHO bytes; anyone can regenerate the set from the manifest.
The `redistributable` column in the log records which is which so that no later
step can package a WHO image by accident.

Output
------
  data/raw/split_e_regulatory/PC_XXXXXX.<ext>
  data/metadata/split_e_download_log.csv  — one row per attempted fetch, with
    sha256, byte count, decoded dimensions, HTTP content type, and the rights
    status carried through from the manifest.
"""
import csv
import hashlib
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "PharmaChecked_200_license_audited_manifest_2026-09-07.csv"
OUT_DIR = ROOT / "data" / "raw" / "split_e_regulatory"
LOG_OUT = ROOT / "data" / "metadata" / "split_e_download_log.csv"

USER_AGENT = "pharmavision-research/1.0 (external-validation dedup check)"
REQUEST_DELAY_S = 0.4  # be polite to fda.gov / who.int

EXT_BY_FORMAT = {"PNG": ".png", "JPEG": ".jpg", "GIF": ".gif", "WEBP": ".webp"}

REDISTRIBUTABLE = {"permitted_pending_per_image_exception_check"}

FIELDNAMES = [
    "image_id", "case_id", "manifest_label", "source_organization",
    "original_image_url", "http_status", "content_type", "bytes", "sha256",
    "format", "width", "height", "min_side", "stored_relpath",
    "image_license", "redistribution_status", "redistributable",
]


def direct_reference_rows():
    with open(MANIFEST, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r["record_type"] == "direct_image_reference"]


def fetch(url):
    # The manifest stores some URLs with literal spaces already percent-encoded
    # and some not; quote() with a generous safe set normalises both without
    # double-encoding an existing %XX.
    safe = urllib.parse.quote(url, safe=":/?=&%#")
    req = urllib.request.Request(safe, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.status, resp.headers.get("Content-Type", ""), resp.read()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = direct_reference_rows()
    print(f"{len(rows)} direct image references in the manifest")

    log = []
    for i, r in enumerate(rows, 1):
        iid = r["image_id"]
        org = "FDA" if "fda.gov" in r["original_image_url"] else "WHO"
        entry = {
            "image_id": iid,
            "case_id": r["case_id"],
            "manifest_label": r["label"],
            "source_organization": org,
            "original_image_url": r["original_image_url"],
            "image_license": r["image_license"],
            "redistribution_status": r["redistribution_status"],
            "redistributable": str(r["redistribution_status"] in REDISTRIBUTABLE),
        }

        existing = list(OUT_DIR.glob(f"{iid}.*"))
        if existing:
            path = existing[0]
            body = path.read_bytes()
            status, ctype = "cached", ""
        else:
            try:
                status, ctype, body = fetch(r["original_image_url"])
            except Exception as exc:  # noqa: BLE001 - logged, not raised
                entry.update({"http_status": f"FAIL: {type(exc).__name__}",
                              "content_type": "", "bytes": 0, "sha256": "",
                              "format": "", "width": "", "height": "",
                              "min_side": "", "stored_relpath": ""})
                log.append(entry)
                print(f"  [{i:>2}/{len(rows)}] {iid} FAILED: {exc}")
                continue
            path = None

        # Decode before deciding the extension: the manifest's URL suffix is not
        # reliable (several .png URLs serve JPEG bytes), and a wrong extension
        # would silently change how a later PIL open behaves.
        import io
        with Image.open(io.BytesIO(body)) as im:
            fmt, (w, h) = im.format, im.size
        if path is None:
            path = OUT_DIR / f"{iid}{EXT_BY_FORMAT.get(fmt, '.bin')}"
            path.write_bytes(body)

        entry.update({
            "http_status": status,
            "content_type": ctype,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "format": fmt, "width": w, "height": h, "min_side": min(w, h),
            "stored_relpath": f"split_e_regulatory/{path.name}",
        })
        log.append(entry)
        print(f"  [{i:>2}/{len(rows)}] {iid} {fmt} {w}x{h} {len(body)}B "
              f"{'redistributable' if entry['redistributable'] == 'True' else 'metadata-only'}")
        if status != "cached":
            time.sleep(REQUEST_DELAY_S)

    LOG_OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(log)

    ok = [e for e in log if e["sha256"]]
    n_redist = sum(1 for e in ok if e["redistributable"] == "True")
    print(f"\nfetched {len(ok)}/{len(rows)}; "
          f"{n_redist} redistributable (FDA), {len(ok) - n_redist} metadata-only (WHO)")
    print(f"Wrote {LOG_OUT}")
    print(f"Bytes in {OUT_DIR} (gitignored — not redistributed by this repo)")


if __name__ == "__main__":
    main()

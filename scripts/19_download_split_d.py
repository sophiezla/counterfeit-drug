"""
Download a SECOND external evaluation set (Split D): the Mendeley source's
"iphone 11 pro" subset, 150 images, one per distinct product.

Why this specific subset. The single-external-source objection to Split C is
real: all 150 of its images come from one camera against one dark backdrop, and
this paper itself argues that a model can score well on one external
distribution by matching a shortcut peculiar to it (Section 9.3, on M3). A
second external set answers that -- but only if it differs in the right way.

The Mendeley archive ships six device subsets, and its authors deliberately
varied lighting across them; Section 5.6 records the iphone 11 pro subset as
more than twice as bright in the mean as the huawei cn subset already used
(0.389 vs 0.162). Both subsets are single-instance-per-product, covering the
same 150 products.

That makes Split D a PAIRED CAPTURE-SHIFT test rather than a new content sample:
the products are held fixed and only the acquisition changes. For a paper whose
thesis is that acquisition is confounded with the label, this is the sharper of
the two experiments available -- it isolates the axis under study instead of
varying content and capture together. It is emphatically NOT an independent
second product sample, and Section 7 says so where the results are reported.

Output: data/raw/mendeley_split_d/*.jpg
"""
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "raw" / "mendeley_split_d"
OUT_DIR.mkdir(parents=True, exist_ok=True)
META_PATH = ROOT / "data" / "metadata" / "mendeley_bjy2svvmn8_metadata.json"
META_URL = "https://data.mendeley.com/public-api/datasets/bjy2svvmn8"
# data.mendeley.com rejects generic urllib requests with 403 unless a browser
# User-Agent is supplied; the public-api path is the one that returns file URLs.
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
SUBSET = "iphone 11 pro"


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS))


def main():
    if META_PATH.exists():
        meta = json.loads(META_PATH.read_text(encoding="utf-8"))
        print(f"Using cached metadata ({len(meta['files'])} files)")
    else:
        print("Fetching dataset metadata...")
        with fetch(META_URL) as resp:
            meta = json.loads(resp.read().decode("utf-8"))
        META_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    targets = [f for f in meta["files"]
               if f["filename"].lower().startswith(SUBSET)]
    print(f"Downloading {len(targets)} '{SUBSET}' files...")

    got = 0
    for i, f in enumerate(targets):
        out_path = OUT_DIR / f["filename"].replace(" ", "_")
        if out_path.exists() and out_path.stat().st_size == f["content_details"]["size"]:
            got += 1
            continue
        with fetch(f["content_details"]["download_url"]) as resp, \
                open(out_path, "wb") as out_f:
            out_f.write(resp.read())
        got += 1
        if got % 25 == 0:
            print(f"  {got}/{len(targets)}")
        time.sleep(0.1)

    files = sorted(OUT_DIR.glob("*"))
    total = sum(p.stat().st_size for p in files)
    print(f"Done. {len(files)} files, {total / 1e6:.1f} MB in {OUT_DIR}")


if __name__ == "__main__":
    main()

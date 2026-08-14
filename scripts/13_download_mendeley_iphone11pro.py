"""
Step 13 (data) — Download the "iPhone 11 Pro" subset of the same Mendeley
dataset already used for Split C's authentic class (06_download_mendeley_
split_c.py used the "Huawei CN" subset, 150 images, 1 per product).

This subset has the same structure (150 images, one per the same 150
distinct products) but is a completely different set of photos, never
used anywhere in this project. It serves as the base material for
synthetic counterfeit generation (see 14_generate_synthetic_counterfeit.py
and data/metadata/synthetic_counterfeit_findings.md): perturbing an
independent, never-before-used, genuinely-authentic photo into a
synthetic "counterfeit-style" version, rather than reusing the same
photos already serving as the authentic class.

Output: data/raw/mendeley_iphone11pro/*.jpg
"""
import json
import time
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "raw" / "mendeley_iphone11pro"
OUT_DIR.mkdir(parents=True, exist_ok=True)
META_PATH = ROOT / "data" / "metadata" / "mendeley_bjy2svvmn8_metadata.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return urllib.request.urlopen(req)


def main():
    print("Loading cached dataset metadata...")
    meta = json.loads(META_PATH.read_text(encoding="utf-8"))

    targets = [f for f in meta["files"] if f["filename"].lower().startswith("iphone 11 pro")]
    print(f"Downloading {len(targets)} files...")

    for i, f in enumerate(targets):
        out_path = OUT_DIR / f["filename"].replace(" ", "_")
        if out_path.exists() and out_path.stat().st_size == f["content_details"]["size"]:
            continue
        url = f["content_details"]["download_url"]
        with fetch(url) as resp, open(out_path, "wb") as out_f:
            out_f.write(resp.read())
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{len(targets)}")
        time.sleep(0.1)  # be polite to the server

    total_size = sum(p.stat().st_size for p in OUT_DIR.glob("*.jpg"))
    print(f"Done. {len(list(OUT_DIR.glob('*.jpg')))} images, "
          f"{total_size / 1e6:.1f} MB in {OUT_DIR}")


if __name__ == "__main__":
    main()

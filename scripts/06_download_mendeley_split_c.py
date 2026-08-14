"""
Step 6 (data) — Download a Split C candidate: "Mobile-Captured Pharmaceutical
Medication Packages" (Mendeley Data, DOI 10.17632/bjy2svvmn8.1, CC BY 4.0,
Abdelmaksoud/Gadallah/Asad, Cairo University).

This dataset has NO counterfeit label (it's a single-class collection of
150 distinct authentic pharmaceutical packages, built for label-OCR
research) -- so per the user's direction, it is used as an AUTHENTIC-ONLY
external generalization check, not a full two-class Split C. It is
genuinely independent of Roboflow/Kaggle: different authors, different
country/context (Cairo University vs. Philippines FDA-sourced images and an
unspecified-provenance Kaggle set), different capture methodology (6
specific smartphones under controlled lighting-variation protocol vs.
scraped/screenshot images). Independence is verified programmatically in
07_verify_split_c_independence.py via the same rotation-aware pHash
pipeline used in the main dedup step, not assumed from the description.

Downloads only the "huawei cn (N).jpg" subset: exactly one image per each
of the 150 distinct products (confirmed via metadata: 150 files, 1:1 with
the 150-row drug list), avoiding a 6.46 GB full-dataset pull when a single
representative photo per product is what a generalization check needs.

Output: data/raw/mendeley_split_c/*.jpg + data/raw/mendeley_split_c/drug_list.xlsx
"""
import json
import time
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "raw" / "mendeley_split_c"
OUT_DIR.mkdir(parents=True, exist_ok=True)
META_URL = "https://data.mendeley.com/public-api/datasets/bjy2svvmn8"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return urllib.request.urlopen(req)


def main():
    print("Fetching dataset metadata...")
    with fetch(META_URL) as resp:
        meta = json.loads(resp.read().decode("utf-8"))

    (ROOT / "data" / "metadata" / "mendeley_bjy2svvmn8_metadata.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    targets = [f for f in meta["files"] if f["filename"].lower().startswith("huawei cn")]
    targets += [f for f in meta["files"] if f["filename"] == "drug list.xlsx"]
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

    total_size = sum((OUT_DIR / f["filename"].replace(" ", "_")).stat().st_size
                      for f in targets if (OUT_DIR / f["filename"].replace(" ", "_")).exists())
    print(f"Done. {len(list(OUT_DIR.glob('*.jpg')))} images, "
          f"{total_size / 1e6:.1f} MB in {OUT_DIR}")


if __name__ == "__main__":
    main()

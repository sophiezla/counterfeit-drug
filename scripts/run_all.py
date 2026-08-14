"""
Run the entire data pipeline end-to-end, in order, from the extracted raw
data through to final splits. Idempotent: re-running overwrites prior
outputs with identical results (all randomness is fixed-seed).

Usage (from the pharmavision/ project root):
    pip install -r requirements.txt
    python scripts/run_all.py

Prerequisite (not automated — see data/README.md "Reproducing from scratch"):
    the two zips in data/raw_zips/ must already be extracted into
    data/raw/roboflow/ and data/raw/kaggle_fake_real/.
"""
import runpy
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
STEPS = [
    "01_inventory.py",
    "02_filter.py",
    "03_dedup.py",
    "04_provenance.py",
    "05_build_splits.py",
]


def main():
    for step in STEPS:
        print(f"\n{'=' * 70}\nRunning {step}\n{'=' * 70}")
        runpy.run_path(str(SCRIPTS_DIR / step), run_name="__main__")


if __name__ == "__main__":
    main()

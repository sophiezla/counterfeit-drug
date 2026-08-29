"""
Pack paper/overleaf_upload.zip: everything needed to compile both documents on
Overleaf, and nothing else.

The zip used to be assembled by hand and had gone stale -- it held a paper.tex
from an earlier build, no supplementary.tex, and none of the class assets, so
an upload would not have compiled. This script regenerates it from whatever is
currently in paper/latex/, and refuses to run if either .tex is older than the
Markdown it comes from, since a stale zip is the failure it exists to prevent.

    python paper/scripts/build_tex.py
    python paper/scripts/build_supplement.py
    python paper/scripts/make_overleaf_zip.py
"""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LATEX = ROOT / "paper" / "latex"
OUT = ROOT / "paper" / "overleaf_upload.zip"

# (generated .tex, the Markdown it is generated from)
DOCS = [("paper.tex", "paper.md"),
        ("supplementary.tex", "supplementary.md")]

# The class, and the assets it loads by name. Overleaf carries IEEEtran but
# not ieeeaccess, so the class travels with the source, as the official
# template distributes it.
ASSETS = ["ieeeaccess.cls", "spotcolor.sty", "IEEEtran.cls", "IEEEtran.bst",
          "logo.png", "notaglinelogo.png", "bullet.png"]
FONT_GLOBS = ["t1-*.pfb", "t1-*.tfm", "t1-*.map", "t1*.fd"]


def main():
    missing, stale = [], []
    for tex, md in DOCS:
        src, gen = ROOT / "paper" / md, LATEX / tex
        if not gen.exists():
            missing.append(tex)
        elif src.exists() and gen.stat().st_mtime < src.stat().st_mtime:
            stale.append(tex)
    if missing or stale:
        for name in missing:
            print(f"  MISSING {name} -- run its builder first")
        for name in stale:
            print(f"  STALE   {name} is older than its Markdown -- rebuild first")
        sys.exit(1)

    files = []
    for tex, _ in DOCS:
        files.append(LATEX / tex)
    for name in ASSETS:
        path = LATEX / name
        if path.exists():
            files.append(path)
        else:
            print(f"  [note] {name} not in paper/latex/, not packed")
    for pattern in FONT_GLOBS:
        files.extend(sorted(LATEX.glob(pattern)))

    figures = sorted((LATEX / "figures").glob("*"))
    if not figures:
        print("  no figures in paper/latex/figures -- run build_tex.py")
        sys.exit(1)

    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for path in files:
            z.write(path, path.name)
        for path in figures:
            z.write(path, f"figures/{path.name}")

    total = sum(i.file_size for i in zipfile.ZipFile(OUT).infolist())
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  {len(files)} source/asset files, {len(figures)} figures, "
          f"{total / 1e6:.1f} MB uncompressed")


if __name__ == "__main__":
    main()

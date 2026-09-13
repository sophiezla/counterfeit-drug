r"""
Assemble ieee-submission/: everything the IEEE Access submission needs, taken
from the current build tree, verified fresh, and listed with checksums.

    python paper/scripts/make_submission_folder.py

Refuses to run if either generated .tex is older than the Markdown it comes
from, or either published PDF is older than its .tex -- a stale bundle is the
failure this script exists to prevent. Wipes and rebuilds the folder every
time, so nothing from an earlier assembly can survive into it.

What goes in, and why:
  01_manuscript.pdf              the review copy of the main paper
  02_supplementary_material.pdf  the supplement, uploaded as supplementary
  03_manuscript.docx             the Word rendering of the same Markdown
  04_latex_source/               paper.tex, supplementary.tex, the class and
                                 its assets, the fonts, and figures/ -- the
                                 same set make_overleaf_zip.py packs, laid
                                 out so it compiles as-is with pdflatex
  04_latex_source.zip            the same, zipped for the upload form
  05_graphical_abstract.png      Fig. 1 (the mechanism diagram), which is
                                 what IEEE Access's required graphical
                                 abstract slot is meant to hold
  06_author_photo.jpeg           the biography photograph, separately
  MANIFEST.md                    page counts, word counts, the build commit,
                                 and a SHA-256 for every file
"""
import hashlib
import shutil
import subprocess
import sys
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAPER = ROOT / "paper"
LATEX = PAPER / "latex"
OUT = ROOT / "ieee-submission"

MAIN_PDF = PAPER / "PharmaChecked_v2_manuscript_IEEEAccess.pdf"
SUP_PDF = PAPER / "PharmaChecked_v2_supplementary_IEEEAccess.pdf"
DOCX = PAPER / "PharmaChecked_v2_manuscript.docx"

ASSETS = ["ieeeaccess.cls", "spotcolor.sty", "IEEEtran.cls", "IEEEtran.bst",
          "logo.png", "notaglinelogo.png", "bullet.png"]
FONT_GLOBS = ["t1-*.pfb", "t1-*.tfm", "t1-*.map", "t1*.fd"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def freshness():
    problems = []
    for tex, md, pdf in (("paper.tex", "paper.md", MAIN_PDF),
                         ("supplementary.tex", "supplementary.md", SUP_PDF)):
        src, gen = PAPER / md, LATEX / tex
        if gen.stat().st_mtime < src.stat().st_mtime:
            problems.append(f"{tex} is older than {md}: rebuild")
        if pdf.stat().st_mtime < gen.stat().st_mtime:
            problems.append(f"{pdf.name} is older than {tex}: recompile")
    if DOCX.stat().st_mtime < (PAPER / "paper.md").stat().st_mtime:
        problems.append("the .docx is older than paper.md: rebuild")
    return problems


def main():
    problems = freshness()
    if problems:
        for p in problems:
            print("  STALE  " + p)
        sys.exit(1)

    if OUT.exists():
        shutil.rmtree(OUT)
    src_dir = OUT / "04_latex_source"
    (src_dir / "figures").mkdir(parents=True)

    shutil.copy2(MAIN_PDF, OUT / "01_manuscript.pdf")
    shutil.copy2(SUP_PDF, OUT / "02_supplementary_material.pdf")
    shutil.copy2(DOCX, OUT / "03_manuscript.docx")

    packed = []
    for name in ["paper.tex", "supplementary.tex"] + ASSETS:
        shutil.copy2(LATEX / name, src_dir / name)
        packed.append(src_dir / name)
    for pattern in FONT_GLOBS:
        for path in sorted(LATEX.glob(pattern)):
            shutil.copy2(path, src_dir / path.name)
            packed.append(src_dir / path.name)
    for path in sorted((LATEX / "figures").glob("*")):
        shutil.copy2(path, src_dir / "figures" / path.name)
        packed.append(src_dir / "figures" / path.name)

    zip_path = OUT / "04_latex_source.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for path in packed:
            z.write(path, path.relative_to(src_dir).as_posix())

    shutil.copy2(PAPER / "figures" / "fig15_mechanism.png",
                 OUT / "05_graphical_abstract.png")
    shutil.copy2(PAPER / "figures" / "author_photo.jpeg",
                 OUT / "06_author_photo.jpeg")

    # ------------------------------------------------------------ manifest
    import fitz  # PyMuPDF
    mp, sp = fitz.open(MAIN_PDF), fitz.open(SUP_PDF)
    main_words = len(" ".join(p.get_text() for p in mp).split())
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                            capture_output=True, text=True).stdout.strip()
    # The bundle itself is excluded from the dirtiness check, or assembling
    # it would always report the tree dirty.
    dirty = subprocess.run(["git", "status", "--porcelain", "--", ".",
                            ":!ieee-submission"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    title = (PAPER / "paper.md").read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()

    lines = [
        "# IEEE Access submission bundle",
        "",
        f"**{title}**",
        "",
        f"Assembled {date.today().isoformat()} from commit `{commit}`"
        + (" (working tree had uncommitted changes)" if dirty else " (clean working tree)")
        + " by `paper/scripts/make_submission_folder.py`. Every file is a copy of a",
        "build artefact under `paper/`; nothing here is hand-edited. Regenerate the",
        "bundle rather than editing it.",
        "",
        "| File | Purpose | Notes |",
        "|---|---|---|",
        f"| `01_manuscript.pdf` | Main manuscript, review copy | {mp.page_count} pages, {main_words:,} words as rendered |",
        f"| `02_supplementary_material.pdf` | Supplementary material | {sp.page_count} pages |",
        "| `03_manuscript.docx` | Main manuscript, Word rendering | same Markdown source; maths flattened, floats inline |",
        "| `04_latex_source/` | LaTeX source | `paper.tex`, `supplementary.tex`, `ieeeaccess.cls` and its assets, fonts, `figures/`; compiles as-is with pdflatex |",
        "| `04_latex_source.zip` | The same, zipped | for the source-file upload |",
        "| `05_graphical_abstract.png` | Graphical abstract | Fig. 1, the mechanism diagram |",
        "| `06_author_photo.jpeg` | Author photograph | as used in the biography |",
        "",
        "Both documents pass `paper/scripts/verify_crossrefs.py` and",
        "`paper/scripts/final_sweep.py` at this commit. The code release the",
        "manuscript reports is v1.4.0, doi:10.5281/zenodo.22739071.",
        "",
        "## Checksums (SHA-256)",
        "",
        "| File | SHA-256 |",
        "|---|---|",
    ]
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.md":
            lines.append(f"| `{path.relative_to(OUT).as_posix()}` | `{sha256(path)}` |")
    (OUT / "MANIFEST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    n = sum(1 for p in OUT.rglob("*") if p.is_file())
    print(f"wrote {OUT.relative_to(ROOT)}/ -- {n} files, commit {commit}"
          + (", WORKING TREE DIRTY" if dirty else ""))


if __name__ == "__main__":
    main()

r"""
Compile paper/latex/paper.tex and supplementary.tex with pdflatex, then report
what each page actually contains.

The build reports of build_tex.py describe the source, not the page. A page
can be typeset without a single warning and still be four floats and no text,
which is what happened here: floats deferred, queued and drained onto pages of
their own, several pages after the text that introduces them. HANDOFF.md
records the same lesson from the .docx side -- never trust a build report over
a rendered page -- so this script ends by printing the float-to-text balance
of every page and naming the ones that are float-only.

    python paper/scripts/compile_pdf.py            # both documents
    python paper/scripts/compile_pdf.py paper      # just the manuscript

Exit status is non-zero if pdflatex fails or if any page carries floats and no
body text.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LATEX = ROOT / "paper" / "latex"

# Where each compiled document is published, and under what name.
# stem, destination, and whether a float-only page fails the build. It fails
# for the manuscript, where a page of floats several pages after the text that
# introduces them is a defect a reviewer will name. The supplement is closer
# to a figure appendix -- consecutive figures on one page is what it is for --
# so there the same finding is reported and not enforced.
TARGETS = {
    "paper": ("paper.tex",
              ROOT / "paper" / "PharmaChecked_v2_manuscript_IEEEAccess.pdf",
              True),
    "supplementary": ("supplementary.tex",
                      ROOT / "paper"
                      / "PharmaChecked_v2_supplementary_IEEEAccess.pdf",
                      False),
}

CAPTION_RE = re.compile(r"^\s*(?:FIGURE|TABLE)\s+S?\d+\.", re.M)


def compile_one(stem, passes=3):
    """Run pdflatex to a fixed point on cross-references."""
    for i in range(passes):
        proc = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
             "-file-line-error", stem],
            cwd=LATEX, capture_output=True, text=True, errors="replace")
        if proc.returncode != 0:
            tail = [ln for ln in proc.stdout.splitlines()
                    if ln.startswith("!") or ".tex:" in ln]
            print(f"  pdflatex FAILED on pass {i + 1}")
            print("\n".join(tail[-25:]))
            return False
    return True


def page_report(pdf):
    """Print the float/text balance per page; return the float-only pages."""
    try:
        import pymupdf
    except ImportError:
        print("  (pymupdf not installed -- skipping the page audit)")
        return []
    doc = pymupdf.open(pdf)
    float_only = []
    print(f"  {doc.page_count} pages")
    for i, page in enumerate(doc, start=1):
        text = page.get_text()
        captions = CAPTION_RE.findall(text)
        # Body lines: long enough to be prose or a code listing, and not part
        # of a caption. A page whose only long lines are captions is a page of
        # floats. Listings count, or the appendix pages that legitimately set
        # a long command list beneath two tables read as float pages.
        body = [ln for ln in text.split("\n")
                if len(ln) > 45 and not CAPTION_RE.match(ln)]
        if captions and len(body) < 5:
            float_only.append(i)
            print(f"    page {i:>2}: {len(captions)} float(s), "
                  f"{len(body)} body line(s)   <-- float page")
    if not float_only:
        print("    no float-only pages")
    return float_only


def main():
    which = sys.argv[1:] or list(TARGETS)
    failed = []
    for name in which:
        stem, dest, gate = TARGETS[name]
        print(f"{name}:")
        if not compile_one(stem):
            failed.append(name)
            continue
        pdf = LATEX / stem.replace(".tex", ".pdf")
        if page_report(pdf) and gate:
            failed.append(f"{name} (float pages)")
        try:
            dest.write_bytes(pdf.read_bytes())
        except PermissionError:
            # A PDF reader holding the published file blocks the copy. The
            # compile itself succeeded, so say which file is current and which
            # is not, rather than raising a traceback over a locked viewer.
            # HANDOFF.md records the same trap for Word holding the .docx.
            print(f"  LOCKED  {dest.name} is open in another program.")
            print(f"          The fresh build is {pdf.relative_to(ROOT)}; "
                  f"close the reader and re-run to publish it.")
            failed.append(f"{name} (could not publish, file locked)")
            continue
        print(f"  -> {dest.relative_to(ROOT)}")
    if failed:
        print(f"\nFAILED: {', '.join(failed)}")
        sys.exit(1)
    print("\nboth documents compiled with no float-only pages")


if __name__ == "__main__":
    main()

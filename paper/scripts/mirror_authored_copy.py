# -*- coding: utf-8 -*-
"""Regenerate ieee_access_rewrite_20260830/MANUSCRIPT_rewritten.md from paper/paper.md.

The authored copy differs from the build source only in heading case and in the
reference list, which it stubs rather than reprinting. Keeping the transform
mechanical is what stops the two from drifting apart, which they had.
"""
import io
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "paper" / "paper.md"
DST = ROOT / "ieee_access_rewrite_20260830" / "MANUSCRIPT_rewritten.md"

CAPS = re.compile(
    r"^## ([IVX]+\. .+"
    r"|Acknowledgment"
    r"|Ethics, Conflicts of Interest, and Data Provenance"
    r"|Data and Code Availability)$",
    re.M,
)


def main():
    src = io.open(SRC, encoding="utf-8").read()
    old = io.open(DST, encoding="utf-8").read()

    # The reference stub and the biography are carried over from the authored copy.
    tail = old[old.index("## REFERENCES"):]
    body = src[: src.index("## References")]

    # IEEE Access sets top-level headings in caps; the authored copy follows suit.
    body = CAPS.sub(lambda m: "## " + m.group(1).upper(), body)

    io.open(DST, "w", encoding="utf-8", newline="\n").write(body + tail)
    print("regenerated", DST.relative_to(ROOT))


if __name__ == "__main__":
    main()

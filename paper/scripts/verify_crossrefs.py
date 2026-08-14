"""
Check that every cross-reference in the manuscript resolves.

HANDOFF.md warns that table numerals are literal text in paper.md, so any
insertion shifts captions and in-text references independently and the two can
silently disagree. This script is that check, run over both the Markdown
source and the generated LaTeX.

    python paper/scripts/verify_crossrefs.py

Exit status is non-zero if anything dangles, so it can gate a build.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MD = ROOT / "paper" / "paper.md"
TEX = ROOT / "paper" / "latex" / "paper.tex"

problems = []


def report(ok, label, detail=""):
    print(f"  [{'ok' if ok else 'FAIL'}] {label}{(' -- ' + detail) if detail else ''}")
    if not ok:
        problems.append(label)


def strip_code(md):
    return re.sub(r"```.*?```", "", md, flags=re.S)


def check_markdown():
    print("paper.md")
    md = strip_code(MD.read_text(encoding="utf-8"))

    captions = [int(n) for n in re.findall(r"^\*\*TABLE (\d+)\.\*\*", md, re.M)]
    report(captions == list(range(1, len(captions) + 1)),
           f"table captions numbered 1..{len(captions)} with no gaps",
           f"got {captions}" if captions != list(range(1, len(captions) + 1)) else "")

    cited = {int(n) for n in re.findall(r"\bTables?\s+(\d+)", md)}
    cited |= {int(n) for m in re.findall(r"\bTables?\s+\d+((?:\s*(?:,|and)\s*\d+)+)", md)
              for n in re.findall(r"\d+", m)}
    dangling = sorted(cited - set(captions))
    report(not dangling, "every in-text table reference has a caption",
           f"dangling: {dangling}")
    uncited = sorted(set(captions) - cited)
    report(not uncited, "every table is referred to in the text",
           f"never cited: {uncited}")

    figs = [int(n) for n in re.findall(r"^>\s*\*\*FIGURE (\d+)\.\*\*", md, re.M)]
    report(sorted(figs) == list(range(1, len(figs) + 1)),
           f"figure captions cover 1..{len(figs)}", f"got {sorted(figs)}")
    fig_cited = {int(n) for n in re.findall(r"\b(?:Figs?\.|Figures?)\s+(\d+)", md)}
    report(not (fig_cited - set(figs)), "every figure reference has a caption",
           f"dangling: {sorted(fig_cited - set(figs))}")

    refs = [int(n) for n in re.findall(r"^\[(\d+)\]\s", md, re.M)]
    report(refs == list(range(1, len(refs) + 1)),
           f"reference list numbered 1..{len(refs)}")
    cites = {int(n) for n in re.findall(r"\[(\d+)\]", md)} - set(refs)
    report(not (cites - set(refs)), "every citation resolves",
           f"dangling: {sorted(cites - set(refs))}")

    sec_refs = set(re.findall(r"\bSections?\s+([IVXLC]+(?:-[A-Z])?)", md))
    heads = set(re.findall(r"^## ([IVXLC]+)\.", md, re.M))
    subs = {f"{a}-{chr(64 + i)}" for a in heads for i in range(1, 27)}
    report(not (sec_refs - heads - subs), "section references look well-formed",
           f"odd: {sorted(sec_refs - heads - subs)}")

    # Sections are Roman in IEEE Access; tables are Arabic. Only tables.
    roman_left = re.findall(r"\bTables?\s+[IVXLC]+\b", md)
    report(not roman_left, "no Roman table numerals left over",
           f"{roman_left[:5]}")

    # Every table must be referenced from text that PRECEDES or accompanies it,
    # never only from text after it. A renumbering that silently redirects a
    # reference to a different table passes the existence checks above, so
    # this locality check is the one that catches it: a table's first mention
    # should be within a few hundred characters of its own caption, because
    # this manuscript introduces every table in the sentence before it.
    # This is a NOTE, not a gate. Legitimate forward references from an
    # earlier section trip it, and it would not have caught the renumbering
    # bug it was written for (a mis-pointed reference can still sit next to
    # some other table's caption). It is here because the list is short enough
    # to eyeball after a renumbering, which is the only reliable check.
    far = []
    for n in captions:
        cap = md.find(f"**TABLE {n}.**")
        mentions = [m.start() for m in re.finditer(rf"\bTable {n}\b", md)]
        if mentions and not any(abs(m - cap) < 2000 for m in mentions):
            far.append(n)
    if far:
        print(f"  [note] tables mentioned only far from their own caption, "
              f"verify the reference still means this table: {far}")

    # Multi-table references ("Tables 19, 21 and 25") are a known renumbering
    # hazard: a shift script keyed on "Table <n>" only rewrites the first
    # element of such a list. Surface them all for eyeballing.
    lists = re.findall(r"Tables?\s+\d+(?:\s*(?:,|and|to|–|-)\s*\d+)+", md)
    if lists:
        print(f"  [note] {len(lists)} multi-table reference(s) — verify by hand "
              f"after any renumbering: {lists}")


def check_tex():
    print("\nlatex/paper.tex")
    if not TEX.exists():
        report(False, "paper.tex exists", "run build_tex.py first")
        return
    tex = TEX.read_text(encoding="utf-8")

    labels = set(re.findall(r"\\label\{([^}]+)\}", tex))
    used = set(re.findall(r"\\(?:eq)?ref\{([^}]+)\}", tex))
    report(not (used - labels), "every \\ref resolves to a \\label",
           f"dangling: {sorted(used - labels)[:8]}")

    dupes = [l for l in labels
             if len(re.findall(r"\\label\{" + re.escape(l) + r"\}", tex)) > 1]
    report(not dupes, "no duplicate labels", f"{dupes[:8]}")

    bib = set(re.findall(r"\\bibitem\{([^}]+)\}", tex))
    cited = {k.strip() for group in re.findall(r"\\cite\{([^}]+)\}", tex)
             for k in group.split(",")}
    report(not (cited - bib), "every \\cite has a \\bibitem",
           f"dangling: {sorted(cited - bib)[:8]}")
    report(not (bib - cited), "every \\bibitem is cited",
           f"uncited: {sorted(bib - cited)[:8]}")

    for env in ("table*", "figure*", "equation", "enumerate", "itemize",
                "verbatim", "thebibliography"):
        o = len(re.findall(r"\\begin\{" + re.escape(env) + r"\}", tex))
        c = len(re.findall(r"\\end\{" + re.escape(env) + r"\}", tex))
        report(o == c, f"{env} environments balanced", f"{o} open, {c} close")


def main():
    check_markdown()
    check_tex()
    print()
    if problems:
        print(f"{len(problems)} check(s) FAILED")
        sys.exit(1)
    print("all cross-reference checks passed")


if __name__ == "__main__":
    main()

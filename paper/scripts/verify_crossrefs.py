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
SUPP_MD = ROOT / "paper" / "supplementary.md"
TEX = ROOT / "paper" / "latex" / "paper.tex"
SUPP_TEX = ROOT / "paper" / "latex" / "supplementary.tex"

# Phrases that only ever appear in the project's internal reference-audit
# annotations. None belongs in a submitted bibliography, and six of them
# reached the compiled PDF once, because the stripper matched a whitelist of
# opening words rather than the shape of a note. This is the check that would
# have caught it.
NOTE_TELLS = (
    "before submission", "should be refreshed", "full text read",
    "full text re-read", "verified against", "not verified",
    "confirm spelling", "we could examine", "identity confirmed",
    "workspace identified", "author list corrected", "re-verified",
    "no peer-reviewed version", "cited here for", "confirmed against",
    "taken from the article", "added then", "2026-08-28",
)

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

    # A section reference pointing at the section it sits in is almost always
    # a renumbering casualty: the text still describes what the old letter
    # covered. Nothing else in this file can tell a stale section reference
    # from a live one, because both resolve. Four wrong ones survived every
    # other check here, and this is the one that catches the cheapest class of
    # them. It reports rather than gates, since a genuine self-reference
    # ("as this section argues") is legal, if rare.
    heads_seq = [(m.start(), m.group(1), m.group(2) or "")
                 for m in re.finditer(r"^(?:## ([IVXLC]+)\.|### ([A-Z])\.)",
                                      md, re.M)]
    section_at, roman = {}, None
    marks = []
    for pos, rom, letter in heads_seq:
        if rom:
            roman = rom
            marks.append((pos, rom))
        elif roman:
            marks.append((pos, f"{roman}-{letter}"))

    def enclosing(pos):
        here = None
        for start, name in marks:
            if start <= pos:
                here = name
            else:
                break
        return here

    selfrefs = []
    for m in re.finditer(r"\bSections?\s+([IVXLC]+(?:-[A-Z])?)", md):
        here = enclosing(m.start())
        if here and m.group(1) == here:
            selfrefs.append((here, " ".join(md[m.start():m.start() + 70].split())))
    if selfrefs:
        print(f"  [note] {len(selfrefs)} reference(s) point at their own "
              f"section — check each is deliberate:")
        for name, snippet in selfrefs:
            print(f"           in {name}: {snippet}")

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
    # Four entries are cited only from the supplement, which shares this
    # numbering; the References section says so. They are not orphans.
    supplement_only = {"ref17", "ref18", "ref22", "ref24"}
    report(not (bib - cited - supplement_only),
           "every \\bibitem is cited (here or in the supplement)",
           f"uncited: {sorted(bib - cited - supplement_only)[:8]}")

    for env in ("table*", "figure*", "equation", "enumerate", "itemize",
                "verbatim", "thebibliography"):
        o = len(re.findall(r"\\begin\{" + re.escape(env) + r"\}", tex))
        c = len(re.findall(r"\\end\{" + re.escape(env) + r"\}", tex))
        report(o == c, f"{env} environments balanced", f"{o} open, {c} close")

    # The bibliography that ships must carry no internal apparatus.
    entries = re.findall(r"\\bibitem\{(.*?)(?=\\bibitem|\\end\{thebib)",
                         tex, re.S)
    leaked = [e.split("}", 1)[0] for e in entries
              if any(t in e.lower() for t in NOTE_TELLS)]
    report(not leaked, "no internal reference note reached the bibliography",
           f"leaked in: {leaked[:8]}")


def check_supplement():
    """The supplement is a separate document sharing one numbering scheme.

    Neither file can resolve the other's S-references, so nothing in the
    LaTeX build checks them. This is the only place the two are held against
    each other.
    """
    print("\nsupplementary.md")
    if not SUPP_MD.exists():
        report(False, "supplementary.md exists")
        return
    supp = strip_code(SUPP_MD.read_text(encoding="utf-8"))
    main_md = strip_code(MD.read_text(encoding="utf-8"))

    sections, current = set(), None
    for level, text in re.findall(r"^(#{2,4})\s*(.*)$", supp, re.M):
        if len(level) == 2:
            m = re.match(r"(S-[IVXLC]+)\.", text)
            if m:
                current = m.group(1)
                sections.add(current)
        elif len(level) == 3 and current:
            m = re.match(r"([A-Z])\.", text)
            if m:
                sections.add(f"{current}-{m.group(1)}")

    tables = {int(n) for n in re.findall(r"\*\*TABLE S(\d+)\.\*\*", supp)}
    figures = {int(n) for n in re.findall(r"\*\*FIGURE S(\d+)\.\*\*", supp)}
    report(sorted(tables) == list(range(1, len(tables) + 1)),
           f"supplement tables numbered S1..S{len(tables)}",
           f"got {sorted(tables)}")
    report(sorted(figures) == list(range(1, len(figures) + 1)),
           f"supplement figures numbered S1..S{len(figures)}",
           f"got {sorted(figures)}")

    def s_refs(text):
        sec = set(re.findall(r"\bSections?\s+(S-[IVXLC]+(?:-[A-Z])?)", text))
        tab = {int(n) for n in re.findall(r"\bTables?\s+S(\d+)", text)}
        tab |= {int(n) for m in re.findall(
                    r"\bTables?\s+S\d+((?:\s*(?:,|and|to|–|-)\s*S\d+)+)", text)
                for n in re.findall(r"\d+", m)}
        fig = {int(n) for n in re.findall(r"\b(?:Figs?\.|Figures?)\s+S(\d+)", text)}
        return sec, tab, fig

    for where, text in (("paper.md", main_md), ("supplementary.md", supp)):
        sec, tab, fig = s_refs(text)
        report(not (sec - sections), f"{where}: every Section S-x resolves",
               f"dangling: {sorted(sec - sections)}")
        report(not (tab - tables), f"{where}: every Table Sn resolves",
               f"dangling: {sorted(tab - tables)}")
        report(not (fig - figures), f"{where}: every Fig. Sn resolves",
               f"dangling: {sorted(fig - figures)}")

    _, cited_t, cited_f = s_refs(main_md + supp)
    report(not (tables - cited_t), "every supplement table is cited somewhere",
           f"never cited: {sorted(tables - cited_t)}")
    report(not (figures - cited_f), "every supplement figure is cited somewhere",
           f"never cited: {sorted(figures - cited_f)}")

    if SUPP_TEX.exists():
        stex = SUPP_TEX.read_text(encoding="utf-8")
        for env in ("table*", "figure*", "equation", "enumerate", "itemize",
                    "verbatim"):
            o = len(re.findall(r"\\begin\{" + re.escape(env) + r"\}", stex))
            c = len(re.findall(r"\\end\{" + re.escape(env) + r"\}", stex))
            report(o == c, f"supplementary.tex: {env} balanced",
                   f"{o} open, {c} close")


def main():
    check_markdown()
    check_tex()
    check_supplement()
    print()
    if problems:
        print(f"{len(problems)} check(s) FAILED")
        sys.exit(1)
    print("all cross-reference checks passed")


if __name__ == "__main__":
    main()

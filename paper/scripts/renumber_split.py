r"""
Renumber the main paper and the supplement after the split, and repoint every
cross-reference between them.

The split moved whole sections out of paper.md, which left both documents with
gaps: sections VI and X vanished from the main paper, subsection letters
skipped, and roughly two thirds of the tables and figures now live in the
supplement while the surviving text still cites their old numbers.

This script assigns:

    main paper     Section I..N, subsections A.., Table 1.., Fig. 1.., Eq. (1)..
    supplement     Section S-I..,  subsections A.., Table S1.., Fig. S1..

and rewrites every reference in BOTH files, so a main-paper sentence that used
to say "Table 9" now says "Table S4" if that table moved, and "Table 6" if it
stayed and shifted. The old numbering is recovered from
paper/_pre_split_backup/paper.md; captions and figure paths are the identity
keys, so a renamed caption is reported rather than silently mismatched.

    python paper/scripts/renumber_split.py --check
    python paper/scripts/renumber_split.py
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAIN = ROOT / "paper" / "paper.md"
SUP = ROOT / "paper" / "supplementary.md"
OLD = ROOT / "paper" / "_pre_split_backup" / "paper.md"

ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
         "XI", "XII", "XIII", "XIV", "XV", "XVI"]

TABLE_CAP = re.compile(r"^\*\*TABLE\s+(\d+)\.\*\*\s*(.{0,50})", re.M)
FIG_CAP = re.compile(r"^>\s*\*\*FIGURE\s+(\d+)\.\*\*\s*`([^`]+)`", re.M)
EQ_TAG = re.compile(r"\\tag\{(\d+)\}")


def strip_code(text):
    return re.sub(r"```.*?```", "", text, flags=re.S)


def read(p):
    return p.read_text(encoding="utf-8")


def section_index(text):
    """[(level, title)] in document order, ignoring fenced code."""
    out, in_code = [], False
    for ln in text.split("\n"):
        if ln.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r"^(#{2,3})\s+(?:[IVXL]+\.|[A-Z]\.)?\s*(.*)$", ln)
        if m:
            out.append((len(m.group(1)), m.group(2).strip(), ln))
    return out


def old_numbering(text):
    """Maps from the pre-split document: caption-key -> old number."""
    t = strip_code(text)
    tables = {m.group(2).strip()[:40]: int(m.group(1))
              for m in TABLE_CAP.finditer(t)}
    figs = {Path(m.group(2)).name: int(m.group(1)) for m in FIG_CAP.finditer(t)}
    secs = {}
    major = 0
    minor = 0
    for ln in t.split("\n"):
        m = re.match(r"^##\s+([IVXL]+)\.\s+(.*)$", ln)
        if m:
            major, minor = m.group(1), 0
            secs[m.group(2).strip()] = major
            continue
        m = re.match(r"^###\s+([A-Z])\.\s+(.*)$", ln)
        if m and major:
            secs[m.group(2).strip()] = f"{major}-{m.group(1)}"
    return tables, figs, secs


def assign(text, prefix):
    """New numbers for one file. prefix '' for main, 'S' for the supplement."""
    t = strip_code(text)
    tables, figs = {}, {}
    for i, m in enumerate(TABLE_CAP.finditer(t), 1):
        tables[m.group(2).strip()[:40]] = f"{prefix}{i}"
    for i, m in enumerate(FIG_CAP.finditer(t), 1):
        figs[Path(m.group(2)).name] = f"{prefix}{i}"
    secs, major_i = {}, 0
    cur_major, minor_i = None, 0
    for ln in t.split("\n"):
        m = re.match(r"^##\s+(?:[IVXL]+\.\s+)?(.*)$", ln)
        if m and not ln.startswith("###"):
            title = m.group(1).strip()
            if title in ("Acknowledgment", "References", "Author Biographies",
                         "Data and Code Availability",
                         "Ethics, Conflicts of Interest, and Data Provenance"):
                cur_major = None
                continue
            major_i += 1
            cur_major = (f"S-{ROMAN[major_i]}" if prefix
                         else ROMAN[major_i])
            secs[title] = cur_major
            minor_i = 0
            continue
        m = re.match(r"^###\s+(?:[A-Z]\.\s+)?(.*)$", ln)
        if m and cur_major:
            minor_i += 1
            secs[m.group(1).strip()] = f"{cur_major}-{chr(64 + minor_i)}"
    return tables, figs, secs


def rewrite_headings(text, prefix):
    out, major_i, minor_i, in_code = [], 0, 0, False
    cur_major = None
    for ln in text.split("\n"):
        if ln.strip().startswith("```"):
            in_code = not in_code
            out.append(ln)
            continue
        if in_code:
            out.append(ln)
            continue
        m = re.match(r"^##\s+(?:[IVXL]+\.\s+)?(.*)$", ln)
        if m and not ln.startswith("###"):
            title = m.group(1).strip()
            if title in ("Acknowledgment", "References", "Author Biographies",
                         "Data and Code Availability",
                         "Ethics, Conflicts of Interest, and Data Provenance"):
                cur_major = None
                out.append(f"## {title}")
                continue
            major_i += 1
            minor_i = 0
            cur_major = (f"S-{ROMAN[major_i]}" if prefix else ROMAN[major_i])
            out.append(f"## {cur_major}. {title}")
            continue
        m = re.match(r"^###\s+(?:[A-Z]\.\s+)?(.*)$", ln)
        if m and cur_major:
            minor_i += 1
            out.append(f"### {chr(64 + minor_i)}. {m.group(1).strip()}")
            continue
        out.append(ln)
    return "\n".join(out)


def renumber_captions(text, tables, figs):
    def tab(m):
        key = m.group(2).strip()[:40]
        return f"**TABLE {tables.get(key, m.group(1))}.**"
    text = re.sub(r"\*\*TABLE\s+(\d+)\.\*\*\s*(.{0,50})",
                  lambda m: tab(m) + m.group(2), text)

    def fig(m):
        key = Path(m.group(2)).name
        return (f"> **FIGURE {figs.get(key, m.group(1))}.** `{m.group(2)}`")
    return FIG_CAP.sub(fig, text)


def rewrite_refs(text, tmap, fmap, smap):
    """tmap/fmap/smap: old number (str) -> new label (str)."""
    parts, in_code, buf = [], False, []
    for ln in text.split("\n"):
        if ln.strip().startswith("```"):
            parts.append(("code" if not in_code else "code", "\n".join(buf)))
            buf = [ln]
            in_code = not in_code
            continue
        buf.append(ln)
    parts.append(("x", "\n".join(buf)))

    def sub_all(seg):
        def tab(m):
            nums = re.findall(r"\d+", m.group(0))
            new = [tmap.get(n, n) for n in nums]
            word = "Tables" if len(new) > 1 else "Table"
            if len(new) == 1:
                return f"{word} {new[0]}"
            return f"{word} {', '.join(new[:-1])} and {new[-1]}"
        seg = re.sub(r"\bTables?\s+\d+(?:\s*(?:,|and)\s*\d+)*", tab, seg)

        def fig(m):
            nums = re.findall(r"\d+", m.group(0))
            new = [fmap.get(n, n) for n in nums]
            word = "Figs." if len(new) > 1 else "Fig."
            if len(new) == 1:
                return f"{word} {new[0]}"
            return f"{word} {', '.join(new[:-1])} and {new[-1]}"
        seg = re.sub(r"\b(?:Figs?\.|Figures?)\s+\d+(?:\s*(?:,|and)\s*\d+)*",
                     fig, seg)

        def sec(m):
            return "Section " + smap.get(m.group(1), m.group(1))
        seg = re.sub(r"\bSection\s+([IVXL]+(?:-[A-Z])?)", sec, seg)
        return seg

    return "".join(seg if kind == "code" and seg.lstrip().startswith("```")
                   else sub_all(seg) for kind, seg in parts)


def main():
    check = "--check" in sys.argv
    old_t, old_f, old_s = old_numbering(read(OLD))
    main_txt, sup_txt = read(MAIN), read(SUP)

    new_t_main, new_f_main, new_s_main = assign(main_txt, "")
    new_t_sup, new_f_sup, new_s_sup = assign(sup_txt, "S")

    # old number -> new label, across both documents
    tmap, fmap, smap = {}, {}, {}
    for key, old in old_t.items():
        if key in new_t_main:
            tmap[str(old)] = new_t_main[key]
        elif key in new_t_sup:
            tmap[str(old)] = new_t_sup[key]
    for key, old in old_f.items():
        if key in new_f_main:
            fmap[str(old)] = new_f_main[key]
        elif key in new_f_sup:
            fmap[str(old)] = new_f_sup[key]
    for title, old in old_s.items():
        if title in new_s_main:
            smap[str(old)] = new_s_main[title]
        elif title in new_s_sup:
            smap[str(old)] = new_s_sup[title]

    print(f"tables mapped: {len(tmap)}/{len(old_t)}   "
          f"figures: {len(fmap)}/{len(old_f)}   sections: {len(smap)}/{len(old_s)}")
    unmapped_t = sorted(set(map(str, old_t.values())) - set(tmap))
    if unmapped_t:
        print(f"  !! tables with no destination: {unmapped_t}")
    print("  table map:", {k: tmap[k] for k in sorted(tmap, key=int)})
    print("  figure map:", {k: fmap[k] for k in sorted(fmap, key=int)})

    if check:
        print("\n--check: nothing written")
        return

    for path, txt, tt, ff, prefix in ((MAIN, main_txt, new_t_main, new_f_main, ""),
                                      (SUP, sup_txt, new_t_sup, new_f_sup, "S")):
        out = rewrite_headings(txt, prefix)
        out = renumber_captions(out, tt, ff)
        out = rewrite_refs(out, tmap, fmap, smap)
        path.write_text(out, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

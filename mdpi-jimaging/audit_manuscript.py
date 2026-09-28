"""Consistency audit of the J Imaging manuscript against the Diagnostics record.

1. every numeric token in manuscript.md occurs in the Diagnostics manuscript or
   supplement (new numbers are listed for a human check);
2. every table row of the Diagnostics manuscript still appears byte-identical;
3. every Table/Figure/Equation cited exists, and tables/figures are first cited in order;
4. every Table S / Figure S cited exists in supplementary.md;
5. abstract and body word counts; banned-phrase counts.
Usage: python audit_manuscript.py
"""
import io, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
rd = lambda f: io.open(os.path.join(HERE, f), encoding="utf-8").read()
new, old, supp = rd("manuscript.md"), rd("_diagnostics_manuscript.md"), rd("supplementary.md")
body = new[new.index("## 1. Introduction"):new.index("## Supplementary Materials")]
ok = True

# 1. numbers
tok = lambda t: set(re.findall(r"(?<![\w.])\d+(?:[.,]\d+)*(?![\w])", t))
known = tok(old) | tok(rd("_diagnostics_supplementary.md"))
novel = sorted(tok(new[:new.index("## References")]) - known)
print("1. numeric tokens absent from the Diagnostics record:", novel)

# 2. table rows
rows = [l for l in old.split("\n") if l.startswith("| M") or l.startswith("| Kaggle") or l.startswith("| Condition")
        or l.startswith("| Header") or l.startswith("| Determ") or l.startswith("| Pixel") or l.startswith("| Outer")
        or l.startswith("| Inner") or l.startswith("| Border") or l.startswith("| Center") or l.startswith("| —")]
missing = [r for r in rows if r not in new]
print(f"2. Diagnostics table rows: {len(rows)}, missing from new: {len(missing)}")
for r in missing:
    print("   ", r[:110]); ok = False

# 3. main cross-references
for kind, pat in (("TABLE", r"\*\*TABLE (\d+)\.\*\*"), ("FIGURE", r"\*\*FIGURE (\d+)\.\*\*")):
    defined = [int(x) for x in re.findall(pat, new)]
    word = "Table" if kind == "TABLE" else "Figure"
    cited = [int(n) for m in re.finditer(rf"\b{word}s? ((?:\d+(?:, | and |–| to )?)+)", body)
             for n in re.findall(r"\d+", m.group(1))]
    first = list(dict.fromkeys(cited))
    print(f"3. {word}s defined {defined}; first-citation order {first}")
    if sorted(set(cited)) != defined or first != sorted(first):
        print("   ORDER/EXISTENCE PROBLEM"); ok = False
eqs = re.findall(r"\\tag\{(\d+)\}", new)
eqc = set(re.findall(r"Equation \((\d+)\)", new))
print("   equations defined", eqs, "cited", sorted(eqc), "OK" if eqc <= set(eqs) else "PROBLEM")

# 4. supplementary items
for word in ("Table", "Figure"):
    defined = set(re.findall(rf"\*\*{word.upper()} S(\d+)\.\*\*", supp))
    cited = set(n for m in re.finditer(rf"{word}s? S(\d+)(?:(?: to |–| and |, )S?(\d+))?", new) for n in m.groups() if n)
    print(f"4. {word} S cited not defined:", sorted(cited - defined, key=int))
sec_def = set(re.findall(r"^### ([A-Z])\. ", supp, flags=re.M))
sec_cited = set(re.findall(r"S-I-([A-Z])", new))
print("   S-I subsections cited not defined:", sorted(sec_cited - sec_def))

# 5. counts and style
abstract = re.search(r"\*\*Abstract:\*\* (.*)", new).group(1)
print("5. abstract words:", len(abstract.split()))
prose = re.sub(r"^\|.*$", "", body, flags=re.M)
print("   body words (text, tables excluded):", len(prose.split()), "| with tables:", len(body.split()))
for p in ["It is worth noting", "Importantly", "Furthermore", "Taken together", "In recent years", "novel",
          "leverag", "cutting-edge", "transformative", "groundbreaking", "Moreover", "—", ";", "However"]:
    print(f"   {p!r}: {body.count(p)}")
print("ALL STRUCTURAL CHECKS PASS" if ok else "CHECK FAILURES ABOVE")

"""Convert manuscript.md into the official MDPI LaTeX template (journal: jimaging).

Usage: python build_mdpi_tex.py <outdir> <template_Definitions_dir>
Writes <outdir>/manuscript.tex, copies Definitions/ and figures/, and runs
pdflatex twice. manuscript.md is read only.

The markdown is the source of truth; this script only re-expresses it:
  - '## n. Title' headings -> \\section etc. (MDPI numbers them itself, and the
    manual numbers were sequential, so in-text "Section 2.4" still matches);
  - '[1,2]' / '[3-6]' citations -> \\cite{refN,...}, reference list -> \\bibitem;
  - '**TABLE n.** caption' + pipe table -> table/tabularx with \\label{tabn};
  - Unicode symbols -> pdflatex-safe commands.
"""
import io, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(sys.argv[1])
DEFS = sys.argv[2]


def pandoc(md):
    r = subprocess.run(["pandoc", "-f", "markdown-auto_identifiers+raw_tex+tex_math_dollars",
                        "-t", "latex", "--wrap=none"], input=md, capture_output=True,
                       text=True, encoding="utf-8")
    if r.returncode:
        sys.exit(r.stderr)
    return r.stdout.strip()


TEXT_MAP = {"−": "{\\textminus}", "×": "{$\\times$}", "°": "{\\textdegree}", "→": "{$\\rightarrow$}",
            "±": "{$\\pm$}", "σ": "{$\\sigma$}", "β": "{$\\beta$}", "∈": "{$\\in$}", "≤": "{$\\leq$}", "Δ": "{$\\Delta$}"}
MATH_MAP = {"−": "-", "×": "\\times ", "°": "^{\\circ}", "→": "\\rightarrow ", "±": "\\pm ",
            "σ": "\\sigma ", "β": "\\beta ", "∈": "\\in ", "≤": "\\leq ", "Δ": "\\Delta "}
SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")


def fix_unicode(tex):
    parts = re.split(r"(\\\(.*?\\\)|\\\[.*?\\\]|\\begin\{equation\}.*?\\end\{equation\})", tex, flags=re.S)
    out = []
    for i, p in enumerate(parts):
        if i % 2:  # math
            for k, v in MATH_MAP.items():
                p = p.replace(k, v)
        else:
            p = re.sub(r"[₀-₉]+", lambda m: "\\textsubscript{" + m.group().translate(SUB) + "}", p)
            p = re.sub(r"[⁰¹²³⁴-⁹⁻]+", lambda m: "\\textsuperscript{" +
                       m.group().translate(SUP).replace("-", "{\\textminus}") + "}", p)
            for k, v in TEXT_MAP.items():
                p = p.replace(k, v)
        out.append(p)
    return "".join(out)


CITE = re.compile(r"\[([1-9]\d*(?:[–-]\d+)?(?:,\s?[1-9]\d*(?:[–-]\d+)?)*)\]")


def cites(md):
    md = re.sub(r"`(https?://[^`]+)`", r"<\1>", md)
    md = re.sub(r"(?<![<(`])(https?://[^\s<>]*[^\s<>.,;)])", r"<\1>", md)

    def f(m):
        keys = []
        for p in m.group(1).split(","):
            p = p.strip()
            if re.match(r"^\d+[–-]\d+$", p):
                a, b = map(int, re.split("[–-]", p)); keys += range(a, b + 1)
            else:
                keys.append(int(p))
        return "\\cite{" + ",".join(f"ref{k}" for k in keys) + "}"
    return CITE.sub(f, md)


def cell(s):
    return fix_unicode(pandoc(s.strip())) if s.strip() else ""


def table(caption_md, rows, n):
    hdr = [c for c in rows[0].strip().strip("|").split("|")]
    body = [[c for c in r.strip().strip("|").split("|")] for r in rows[2:]]
    ncol = len(hdr)
    wide = ncol >= 5
    size = "\\footnotesize" if wide else "\\small"
    # Column widths in proportion to content (square-root damped), so that a
    # prose column does not wrap into a narrow slot while a number column sits
    # half empty. tabularx needs the \hsize factors to sum to ncol.
    lens = [max(len(re.sub(r"[`*\\$]", "", r[i]).strip()) for r in [hdr] + body) for i in range(ncol)]
    w = [max(6, L) ** 0.5 for L in lens]
    f = [ncol * x / sum(w) for x in w]
    spec = "".join(f">{{\\hsize={x:.3f}\\hsize}}L" for x in f)
    lines = ["\\begin{table}[H]", f"\\caption{{{fix_unicode(pandoc(cites(caption_md)))}\\label{{tab{n}}}}}",
             "\\renewcommand{\\arraystretch}{1.25}"]
    if wide:
        lines += ["\\begin{adjustwidth}{-\\extralength}{0cm}", f"{size}", f"\\begin{{tabularx}}{{\\fulllength}}{{{spec}}}"]
    else:
        lines += [f"{size}", f"\\begin{{tabularx}}{{\\textwidth}}{{{spec}}}"]
    lines += ["\\toprule", " & ".join("\\textbf{" + cell(h) + "}" if h.strip() else "" for h in hdr) + " \\\\", "\\midrule"]
    for r in body:
        lines.append(" & ".join(cell(c) for c in r) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabularx}"]
    if wide:
        lines.append("\\end{adjustwidth}")
    lines.append("\\end{table}")
    return "\n".join(lines)


src = io.open(os.path.join(HERE, "manuscript.md"), encoding="utf-8").read()
lines = src.split("\n")
title = next(l[2:].strip() for l in lines if l.startswith("# "))
abstract_md = next(l for l in lines if l.startswith("**Abstract:**"))[len("**Abstract:** "):]
keywords = next(l for l in lines if l.startswith("**Keywords:**"))[len("**Keywords:** "):]
body_md = src[src.index("## 1. Introduction"):src.index("## Supplementary Materials")]
back_md = src[src.index("## Supplementary Materials"):src.index("## References")]
refs_md = src[src.index("## References"):]

# ---- body: tables and figure become raw LaTeX blocks, then pandoc
blines = body_md.split("\n")
out, i, tabn = [], 0, 0
while i < len(blines):
    l = blines[i]
    m = re.match(r"\*\*TABLE (\d+)\.\*\* (.*)", l)
    if m:
        n, cap = m.groups()
        j = i + 1
        while not blines[j].startswith("|"):
            j += 1
        k = j
        while k < len(blines) and blines[k].startswith("|"):
            k += 1
        out += ["", "```{=latex}", table(cap, blines[j:k], n), "```", ""]
        i = k
        continue
    m = re.match(r"> \*\*FIGURE (\d+)\.\*\* `([^`]+)` — (.*)", l)
    if m:
        n, path, cap = m.groups()
        capt = fix_unicode(pandoc(cites(cap)))
        out += ["", "```{=latex}", "\\begin{figure}[H]", "\\begin{adjustwidth}{-\\extralength}{0cm}", "\\centering",
                f"\\includegraphics[width=\\linewidth]{{{path}}}", "\\end{adjustwidth}",
                f"\\caption{{{capt}\\label{{fig{n}}}}}", "\\end{figure}", "```", ""]
        i += 1
        continue
    m = re.match(r"^(#{2,4}) \d+(?:\.\d+)*\.\s+(.*)", l)
    if m:
        level = {2: "#", 3: "##", 4: "###"}[len(m.group(1))]
        out.append(f"{level} {m.group(2)}")
        i += 1
        continue
    out.append(l)
    i += 1
body_tex = pandoc(cites("\n".join(out)))
body_tex = body_tex.replace("\\tightlist\n", "")
body_tex = re.sub(r"\\\[(.*?)\\tag\{(\d+)\}\s*\\\]", lambda m: "\\begin{equation}" + m.group(1).strip() +
                  "\\label{eq" + m.group(2) + "}\\end{equation}", body_tex, flags=re.S)
body_tex = fix_unicode(body_tex)

# ---- back matter
sections = re.split(r"^## ", back_md, flags=re.M)[1:]
macro = {"Supplementary Materials": "supplementary", "Author Contributions": "authorcontributions",
         "Funding": "funding", "Institutional Review Board Statement": "institutionalreview",
         "Informed Consent Statement": "informedconsent", "Data Availability Statement": "dataavailability",
         "Acknowledgments": "acknowledgments", "Conflicts of Interest": "conflictsofinterest"}
back_tex = []
for s in sections:
    name, txt = s.split("\n", 1)
    tex = fix_unicode(pandoc(cites(txt.strip())))
    back_tex.append(f"\\{macro[name.strip()]}{{{tex}}}\n")

# ---- references
bib = []
for l in refs_md.split("\n"):
    m = re.match(r"^(\d+)\. (.*)", l)
    if m:
        tex = fix_unicode(pandoc(cites(m.group(2))))
        bib.append(f"\\bibitem[{m.group(1)}]{{ref{m.group(1)}}}\n{tex}")

abstract_tex = fix_unicode(pandoc(cites(abstract_md)))
title_tex = fix_unicode(pandoc(title))

doc = r"""\documentclass[jimaging,article,submit,pdftex,oneauthor]{Definitions/mdpi}
\firstpage{1}
\makeatletter
\setcounter{page}{\@firstpage}
\makeatother
\pubvolume{1}
\issuenum{1}
\articlenumber{0}
\pubyear{2026}
\copyrightyear{2026}
\datereceived{ }
\daterevised{ }
\dateaccepted{ }
\datepublished{ }
\hreflink{https://doi.org/}
\usepackage{textcomp}
\usepackage{xurl}
\Title{@TITLE@}
\TitleCitation{@TITLE@}
\newcommand{\orcidauthorA}{0009-0004-2403-910X}
\Author{Sophie Zhu \orcidA{}}
\AuthorNames{Sophie Zhu}
\isAPAStyle{\AuthorCitation{Zhu, S.}}{\isChicagoStyle{\AuthorCitation{Zhu, Sophie.}}{\AuthorCitation{Zhu, S.}}}
\address{Mira Costa High School, Manhattan Beach, CA 90266, USA}
\corres{Correspondence: sophiezhu2028@gmail.com}
\abstract{@ABSTRACT@}
\keyword{@KEYWORDS@}
\begin{document}

@BODY@

\vspace{6pt}

@BACK@
\abbreviations{Abbreviations}{
The following abbreviations are used in this manuscript:
\\
\noindent
\begin{tabular}{@{}ll}
AI & artificial intelligence\\
CNN & convolutional neural network\\
FDA & U.S. Food and Drug Administration\\
JPEG & Joint Photographic Experts Group (image format)\\
LR & logistic regression\\
PNG & Portable Network Graphics (image format)\\
RGB & red-green-blue\\
WHO & World Health Organization
\end{tabular}
}

\begin{adjustwidth}{-\extralength}{0cm}
\reftitle{References}
\begin{thebibliography}{999}
@BIB@
\end{thebibliography}
\PublishersNote{}
\end{adjustwidth}
\end{document}
"""
doc = (doc.replace("@TITLE@", title_tex).replace("@ABSTRACT@", abstract_tex)
       .replace("@KEYWORDS@", keywords).replace("@BODY@", body_tex)
       .replace("@BACK@", "\n".join(back_tex)).replace("@BIB@", "\n".join(bib)))

os.makedirs(OUT, exist_ok=True)
if os.path.isdir(os.path.join(OUT, "Definitions")):
    shutil.rmtree(os.path.join(OUT, "Definitions"))
shutil.copytree(DEFS, os.path.join(OUT, "Definitions"))
os.makedirs(os.path.join(OUT, "figures"), exist_ok=True)
# Figures come from mdpi-jimaging/figures (make_figures_diagnostics.py, make_figure4.py).
for f in re.findall(r"`figures/([^`]+)`", src):
    shutil.copy(os.path.join(HERE, "figures", f), os.path.join(OUT, "figures"))
io.open(os.path.join(OUT, "manuscript.tex"), "w", encoding="utf-8", newline="\n").write(doc)
for _ in range(2):
    r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "manuscript.tex"],
                       cwd=OUT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        print(r.stdout[-4000:]); sys.exit("pdflatex failed")
log = io.open(os.path.join(OUT, "manuscript.log"), encoding="utf-8", errors="replace").read()
print("undefined refs:", len(re.findall(r"undefined", log)), "| overfull boxes:", len(re.findall(r"Overfull \\hbox", log)),
      "| missing chars:", len(re.findall(r"Missing character", log)))
print("wrote", os.path.join(OUT, "manuscript.pdf"))

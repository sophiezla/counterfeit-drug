r"""
Render paper/paper.md into an Overleaf-ready IEEE Access LaTeX source tree.

Same contract as build_docx.py: paper.md is the single source of truth and
this script converts it, so the outputs cannot drift from the manuscript.

Output (paper/latex/):
    paper.tex          \documentclass{ieeeaccess} main file
    figures/*.pdf      the vector figures, copied so the tree is standalone
    README.md          how to compile, and the class-file caveat

What this build gives that the .docx cannot:

  * real mathematics.  build_docx.py flattens LaTeX to Unicode, which turns
    \frac{1}{HW}\sum into "(1)/(HW)Σ".  Here the source maths is passed
    through untouched and set by TeX.
  * real floats.  Tables and figures become table*/figure*, so they float to
    the top of a page instead of splitting the columns where they happen to
    occur.
  * real cross-references.  "Table 7", "Fig. 3" and "Eq. (5)" in paper.md are
    emitted as \ref/\eqref against \label{tab:7} etc., and the bracketed
    citations become \cite, so LaTeX renumbers everything if a float moves.

Conversions applied to the Markdown:

  ## I. Introduction      -> \section{Introduction}      (numeral dropped:
  ### A. Something           the class numbers sections itself)
  **bold** *it* `code`   -> \textbf \textit \texttt
  <sup>1</sup>           -> \textsuperscript
  pipe table             -> table* + tabular, caption above
  > **FIGURE n.** `path` -> figure* + \includegraphics
  $$ ... \tag{n}$$       -> equation environment, \label{eq:n}
  [12]                   -> \cite{ref12}
  [n] entry              -> \bibitem{refn} in thebibliography

Non-ASCII prose characters are mapped to LaTeX in UNICODE_MAP; anything left
over is reported at the end of the run rather than silently emitted, because
pdflatex will fail on it.

The internal apparatus (the reference verification note and the trailing
italic annotation on each reference) is excluded, as in build_docx.py.
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "paper" / "paper.md"
OUTDIR = ROOT / "paper" / "latex"
OUT = OUTDIR / "paper.tex"

KEEP_INTERNAL_NOTES = False

# --------------------------------------------------------------------- escaping
UNICODE_MAP = {
    "—": "---", "–": "--", "‐": "-", "−": "$-$",
    "“": "``", "”": "''", "‘": "`", "’": "'", "…": r"\ldots{}",
    "×": r"$\times$", "·": r"$\cdot$", "±": r"$\pm$", "≈": r"$\approx$",
    "≤": r"$\le$", "≥": r"$\ge$", "≠": r"$\neq$", "→": r"$\rightarrow$",
    "⊂": r"$\subset$", "⊆": r"$\subseteq$", "⊃": r"$\supset$",
    "⊇": r"$\supseteq$", "∈": r"$\in$", "∞": r"$\infty$", "√": r"$\sqrt{}$",
    "Δ": r"$\Delta$", "Σ": r"$\Sigma$", "Φ": r"$\Phi$", "Ω": r"$\Omega$",
    "α": r"$\alpha$", "β": r"$\beta$", "γ": r"$\gamma$", "δ": r"$\delta$",
    "ε": r"$\varepsilon$", "θ": r"$\theta$", "λ": r"$\lambda$",
    "μ": r"$\mu$", "π": r"$\pi$", "ρ": r"$\rho$", "σ": r"$\sigma$",
    "τ": r"$\tau$", "φ": r"$\varphi$", "χ": r"$\chi$", "ψ": r"$\psi$",
    "ω": r"$\omega$", "η": r"$\eta$",
    "°": r"$^\circ$", "′": r"$'$", "″": r"$''$",
    "¹": r"$^1$", "²": r"$^2$", "³": r"$^3$", "⁻": r"$^-$",
    "≫": r"$\gg$", "≪": r"$\ll$", "∼": r"$\sim$", "~": r"$\sim$",
    "Ö": r'\"{O}', "Ü": r'\"{U}', "∩": r"$\cap$", "∪": r"$\cup$",
    "✓": r"$\checkmark$", "⁴": r"$^4$", "⁵": r"$^5$", "⁶": r"$^6$",
    "₀": r"$_0$", "₁": r"$_1$", "₂": r"$_2$",
    "\u00a0": "~", "\u2009": r"\,", "\u200b": "",
}

SPECIALS = {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
            "_": r"\_", "{": r"\{", "}": r"\}", "^": r"\^{}"}

_unmapped = set()


def esc(text):
    """Escape plain prose for LaTeX. Never call this on maths or verbatim."""
    out = []
    for ch in text:
        if ch in SPECIALS:
            out.append(SPECIALS[ch])
        elif ch in UNICODE_MAP:
            out.append(UNICODE_MAP[ch])
        elif ord(ch) > 127:
            _unmapped.add(ch)
            out.append(ch)
        else:
            out.append(ch)
    return "".join(out)


# ------------------------------------------------------------------- inline
INLINE = re.compile(
    r"(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`|\$[^$]+?\$|<sup>.*?</sup>)")

CITE_RE = re.compile(r"\[(\d+)\](?:\s*[–-]\s*\[(\d+)\])?")
TAB_REF_RE = re.compile(r"\bTables?\s+(\d+)((?:\s*(?:,|and|to|–|-)\s*\d+)*)")
FIG_REF_RE = re.compile(r"\b(?:Figs?\.|Figures?)\s+(\d+)"
                        r"((?:\s*(?:,|and|to|–|-)\s*\d+)*)")
EQ_REF_RE = re.compile(r"\bEq(?:uation)?\.?\s*\((\d+)\)")


def _cite(m):
    lo, hi = m.group(1), m.group(2)
    if hi:
        keys = ",".join(f"ref{n}" for n in range(int(lo), int(hi) + 1))
    else:
        keys = f"ref{lo}"
    return r"\cite{" + keys + "}"


def _numbered_ref(prefix, word_single, word_plural):
    def repl(m):
        first, rest = m.group(1), m.group(2) or ""
        nums = [first] + re.findall(r"\d+", rest)
        word = word_plural if len(nums) > 1 else word_single
        if len(nums) == 1:
            return rf"{word}~\ref{{{prefix}:{nums[0]}}}"
        joined = re.sub(r"\d+", lambda mm: rf"\ref{{{prefix}:{mm.group(0)}}}",
                        first + rest)
        return f"{word}~{joined}"
    return repl


def crossrefs(s):
    """Turn the manuscript's literal cross-references into real LaTeX ones."""
    s = TAB_REF_RE.sub(_numbered_ref("tab", "Table", "Tables"), s)
    s = FIG_REF_RE.sub(_numbered_ref("fig", "Fig.", "Figs."), s)
    s = EQ_REF_RE.sub(lambda m: rf"\eqref{{eq:{m.group(1)}}}", s)
    s = CITE_RE.sub(_cite, s)
    return s


def inline(text, do_crossrefs=True):
    """Markdown inline -> LaTeX. Maths and code pass through unescaped."""
    out = []
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            out.append(r"\textbf{" + inline(part[2:-2], do_crossrefs) + "}")
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append(r"\textit{" + inline(part[1:-1], do_crossrefs) + "}")
        elif part.startswith("<sup>"):
            out.append(r"\textsuperscript{"
                       + esc(re.sub(r"</?sup>", "", part)) + "}")
        elif part.startswith("`") and part.endswith("`"):
            out.append(r"\texttt{" + esc(part[1:-1]) + "}")
        elif part.startswith("$") and part.endswith("$"):
            out.append(part)                      # already LaTeX maths
        else:
            out.append(crossrefs(esc(part)) if do_crossrefs else esc(part))
    return "".join(out)


# --------------------------------------------------------------- block parsing
from importlib import util as _importutil                       # noqa: E402
_spec = _importutil.spec_from_file_location(
    "build_docx", Path(__file__).with_name("build_docx.py"))
_bd = _importutil.module_from_spec(_spec)
_spec.loader.exec_module(_bd)
parse_blocks = _bd.parse_blocks                 # one parser, two renderers

FIG_RE = re.compile(r"^\*\*FIGURE\s+(\d+)\.\*\*\s*`([^`]+)`\s*[—-]\s*(.*)$", re.S)
TABLE_CAP_RE = re.compile(r"^\*\*TABLE\s+(\d+)\.\*\*\s*(.*)$", re.S)
REF_RE = re.compile(r"^\[(\d+)\]\s+(.*)$", re.S)
REF_NOTE_RE = re.compile(
    r"\s*\*(?:Verified|Not verified|Author|Publisher|Primary)[^*]*\*\s*$")
EQ_TAG_RE = re.compile(r"\\tag\{(\d+)\}")


def render_table(lines, number, caption):
    rows = [r for r in ([c.strip() for c in ln.strip().strip("|").split("|")]
                        for ln in lines)
            if not re.match(r"^[\s:\-]+$", "".join(r))]
    if not rows:
        return ""
    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    spec = "l" + "c" * (ncols - 1)
    size = r"\scriptsize" if ncols > 7 else r"\footnotesize"

    body = []
    for ri, row in enumerate(rows):
        cells = [inline(c) for c in row]
        if ri == 0:
            cells = [r"\textbf{" + c + "}" if c else c for c in cells]
        body.append(" & ".join(cells) + r" \\")
        if ri == 0:
            body.append(r"\midrule")

    core = [
        size,
        r"\setlength{\tabcolsep}{4pt}",
        rf"\begin{{tabular}}{{{spec}}}",
        r"\toprule",
        *body,
        r"\bottomrule",
        r"\end{tabular}",
    ]
    if number is None:
        # An uncaptioned table in the source. It must NOT become a float:
        # \caption would advance the table counter and shift every later
        # number away from the "Table n" the manuscript and the .docx use.
        return "\n".join([r"\begin{center}", *core, r"\end{center}", ""])

    return "\n".join([
        r"\begin{table*}[!t]",
        rf"\caption{{{inline(caption, do_crossrefs=True)}}}",
        rf"\label{{tab:{number}}}",
        r"\centering",
        *core,
        r"\end{table*}",
        "",
    ])


def render_figure(m):
    number, relpath, caption = m.groups()
    name = Path(relpath).name
    return "\n".join([
        r"\begin{figure*}[!t]",
        r"\centerline{\includegraphics[width=\textwidth]{figures/"
        + name + "}}",
        rf"\caption{{{inline(caption)}}}",
        rf"\label{{fig:{number}}}",
        r"\end{figure*}",
        "",
    ])


def render_math(raw):
    inner = raw.strip().strip("$").strip()
    tag = EQ_TAG_RE.search(inner)
    inner = EQ_TAG_RE.sub("", inner).strip()
    if tag:
        return ("\\begin{equation}\n"
                f"\\label{{eq:{tag.group(1)}}}\n{inner}\n\\end{{equation}}\n")
    return f"\\begin{{equation*}}\n{inner}\n\\end{{equation*}}\n"


HEAD_NUM_RE = re.compile(r"^(?:[IVXLC]+|[A-Z]|\d+)\.\s+")
UNNUMBERED = ("Acknowledgment", "Data and Code Availability",
              "Author Biographies")


def merge_lists(blocks):
    """The manuscript separates list items with blank lines, so the parser
    emits one 'list' block per item. Left alone, each becomes its own
    enumerate and LaTeX restarts the numbering at 1 for every contribution."""
    merged = []
    for kind, payload in blocks:
        if (kind == "list" and merged and merged[-1][0] == "list"
                and merged[-1][1][0] == payload[0]):
            merged[-1] = ("list", (payload[0], merged[-1][1][1] + payload[1]))
        else:
            merged.append((kind, payload))
    return merged


def render_body(blocks):
    blocks = merge_lists(blocks)
    out, in_refs, bibitems = [], False, []
    pending_caption = None

    skipping = False
    for idx, (kind, payload) in enumerate(blocks):
        # The biography is emitted by the BIOGRAPHY constant below, using the
        # class's own IEEEbiography environment (which places the photograph).
        # Rendering the Markdown section as well would duplicate it.
        if kind == "h2" and str(payload).startswith("Author Biographies"):
            skipping = True
        if skipping:
            continue
        if kind == "h2":
            text = str(payload)
            in_refs = text.startswith("References")
            if in_refs:
                continue
            if text.startswith("Appendix"):
                title = text.replace("—", "---")
                out.append(r"\section*{" + esc(title).upper() + "}")
            elif text.startswith(UNNUMBERED):
                out.append(r"\section*{" + esc(text).upper() + "}")
            else:
                out.append(r"\section{" + inline(HEAD_NUM_RE.sub("", text)) + "}")
        elif kind == "h3":
            out.append(r"\subsection{"
                       + inline(HEAD_NUM_RE.sub("", str(payload))) + "}")
        elif kind == "h4":
            out.append(r"\subsubsection{" + inline(str(payload)) + "}")
        elif kind == "para":
            text = str(payload)
            m = TABLE_CAP_RE.match(text)
            if m:
                pending_caption = m.groups()
                continue
            if in_refs:
                r = REF_RE.match(text)
                if r:
                    entry = r.group(2)
                    if not KEEP_INTERNAL_NOTES:
                        entry = REF_NOTE_RE.sub("", entry)
                    bibitems.append((r.group(1), inline(entry,
                                                        do_crossrefs=False)))
                    continue
            out.append(inline(text))
        elif kind == "table":
            if pending_caption:
                out.append(render_table(payload, *pending_caption))
                pending_caption = None
            else:                       # an uncaptioned table in the source
                out.append(render_table(payload, None, ""))
        elif kind == "quote":
            if (not KEEP_INTERNAL_NOTES and payload
                    and payload[0].startswith("**Reference verification")):
                continue
            figs = [FIG_RE.match(l) for l in payload]
            if any(figs):
                out.extend(render_figure(f) for f in figs if f)
                rest = [l for l, f in zip(payload, figs) if not f]
                if rest:
                    out.append(inline(" ".join(rest)))
            else:
                out.append(r"\noindent\textit{" + inline(" ".join(payload)) + "}")
        elif kind == "math":
            out.append(render_math(payload))
        elif kind == "list":
            ordered, items = payload
            env = "enumerate" if ordered else "itemize"
            out.append(rf"\begin{{{env}}}")
            out.extend(r"\item " + inline(it) for it in items)
            out.append(rf"\end{{{env}}}")
        elif kind == "code":
            out.append(r"\begin{verbatim}")
            out.extend(payload)
            out.append(r"\end{verbatim}")
        elif kind == "rule":
            continue
        out.append("")
    return out, bibitems


# ------------------------------------------------------------------- preamble
PREAMBLE = r"""%% IEEE Access manuscript -- GENERATED FILE, DO NOT EDIT.
%% Produced from paper/paper.md by paper/scripts/build_tex.py.
%% Edit the Markdown and rebuild; hand edits here are lost on the next build.
\documentclass{ieeeaccess}
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{algorithmic}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{url}
\usepackage[colorlinks=true,linkcolor=blue,citecolor=blue,
            urlcolor=blue]{hyperref}
\def\BibTeX{{\rm B\kern-.05em{\sc i\kern-.025em b}\kern-.08em
    T\kern-.1667em\lower.7ex\hbox{E}\kern-.125emX}}

\begin{document}

\history{Date of publication xxxx 00, 0000, date of current version
         xxxx 00, 0000.}
\doi{10.1109/ACCESS.2026.DOI}

\title{%(title)s}

\author{%(authors)s}

\address[1]{Mira Costa High School, Manhattan Beach, CA 90266 USA
            (e-mail: sophiezhu2028@gmail.com)}

\tfootnote{This work received no specific grant from any funding agency in the
public, commercial, or not-for-profit sectors. The manuscript and the
accompanying code were prepared with the assistance of Claude, an AI assistant
developed by Anthropic; see the generative-AI disclosure in the Ethics
section.}

\corresp{Corresponding author: Sophie Zhu (e-mail: sophiezhu2028@gmail.com).}

\begin{abstract}
%(abstract)s
\end{abstract}

\begin{keywords}
%(keywords)s
\end{keywords}

\titlepgskip=-15pt

\maketitle
"""

BIOGRAPHY = r"""
\begin{IEEEbiography}[{\includegraphics[width=1in,height=1.25in,clip,
    keepaspectratio]{figures/author_photo.jpeg}}]{SOPHIE ZHU}
is a student at Mira Costa High School, in Manhattan Beach, CA, USA. Her
research interests include artificial intelligence, healthcare technology,
computer vision, and machine learning applications in public health. Her work
focuses on the development of accessible and scalable artificial intelligence
systems for healthcare challenges, with an emphasis on low-cost technologies
for resource-constrained environments. Her current research examines how
dataset construction shapes what image classifiers actually learn, and what
evaluation protocols are needed before such systems can be trusted in
public-health settings.
\end{IEEEbiography}
"""

README = """# IEEE Access LaTeX build

Generated by `paper/scripts/build_tex.py` from `paper/paper.md`, which is the
single source of truth. **Do not hand-edit `paper.tex`** -- edit the Markdown
and rebuild, or the next build silently discards the change.

    python paper/scripts/build_tex.py

## Compiling

There is no TeX distribution on the machine this was built on, so `paper.tex`
has never been compiled here. Compile it on Overleaf:

1. Open the official *IEEE Access LaTeX template* on Overleaf.
2. Upload `paper.tex` and the `figures/` directory into it.
3. Compile with pdfLaTeX.

`ieeeaccess.cls` is **not** included in this directory. Take it from the
official template rather than from a mirror, so that the class file matches
whatever IEEE currently requires.

## What differs from the .docx

Both outputs come from the same Markdown, but this one has real mathematics,
real floats, and real cross-references (`\\ref`, `\\eqref`, `\\cite`). The
.docx flattens maths to Unicode and places floats inline. Numbers, wording and
tables are identical.
"""


def main():
    md = SRC.read_text(encoding="utf-8")
    head, _, _ = md.partition("## I. Introduction")

    title = re.search(r"^# (.+)$", head, re.M).group(1)
    abstract = re.search(r"^\*\*ABSTRACT\*\*\s*(.+)$", head, re.M).group(1)
    keywords = re.search(r"^\*\*INDEX TERMS\*\*\s*(.+)$", head, re.M).group(1)

    authors = r"\uppercase{Sophie Zhu}\authorrefmark{1}"

    blocks = parse_blocks(md)
    start = next(i for i, (k, v) in enumerate(blocks)
                 if k == "h2" and str(v).startswith("I. Introduction"))
    body, bibitems = render_body(blocks[start:])

    bib = ["", r"\begin{thebibliography}{00}"]
    bib += [rf"\bibitem{{ref{n}}} {entry}" for n, entry in bibitems]
    bib += [r"\end{thebibliography}", ""]

    tex = (PREAMBLE % {
        "title": inline(title, do_crossrefs=False),
        "authors": authors,
        "abstract": inline(abstract, do_crossrefs=False),
        "keywords": inline(keywords, do_crossrefs=False),
    } + "\n" + "\n".join(body) + "\n".join(bib) + BIOGRAPHY
        + "\n\\end{document}\n")

    OUTDIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(tex, encoding="utf-8")
    (OUTDIR / "README.md").write_text(README, encoding="utf-8")

    figdir = OUTDIR / "figures"
    figdir.mkdir(exist_ok=True)
    n_fig = 0
    for pdf in (ROOT / "paper" / "figures").glob("*.pdf"):
        shutil.copy2(pdf, figdir / pdf.name)
        n_fig += 1

    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  {len(tex.splitlines())} lines, {len(bibitems)} bibitems, "
          f"{n_fig} figures copied")
    if _unmapped:
        print("  UNMAPPED non-ASCII characters (pdflatex will fail on these): "
              + " ".join(sorted(_unmapped)))
    else:
        print("  no unmapped non-ASCII characters")


if __name__ == "__main__":
    main()

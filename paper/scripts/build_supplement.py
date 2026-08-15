r"""
Render paper/supplementary.md into paper/latex/supplementary.tex.

Reuses build_tex.py wholesale -- same Markdown parser, same escaping, same
table and float logic -- and changes only what a supplement must change:

  * floats are numbered S1, S2, ... via \thetable / \thefigure / \theequation,
    and the "S1." already written into each Markdown caption is stripped so it
    is not printed twice;
  * sections are unnumbered, because the Markdown headings already carry the
    "S-I." labels the main paper cites;
  * citations become literal bracketed numbers. The reference list lives in
    the main paper and is not duplicated here, so \cite would dangle.

    python paper/scripts/build_supplement.py
"""
import re
import sys
from importlib import util as _importutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "paper" / "supplementary.md"
OUT = ROOT / "paper" / "latex" / "supplementary.tex"

_spec = _importutil.spec_from_file_location(
    "build_tex", Path(__file__).with_name("build_tex.py"))
bt = _importutil.module_from_spec(_spec)
_spec.loader.exec_module(bt)

# S-aware caption patterns, replacing build_tex's digit-only ones.
bt.TABLE_CAP_RE = re.compile(r"^\*\*TABLE\s+S?(\d+)\.\*\*\s*(.*)$", re.S)
bt.FIG_RE = re.compile(
    r"^\*\*FIGURE\s+S?(\d+)\.\*\*\s*`([^`]+)`\s*[—-]\s*(.*)$", re.S)

PREAMBLE = r"""%% Supplementary material -- GENERATED FILE, DO NOT EDIT.
%% Produced from paper/supplementary.md by paper/scripts/build_supplement.py.
\documentclass{ieeeaccess}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{textcomp}
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{tabularx}
\usepackage{listings}
\usepackage{microtype}
\usepackage{url}

\IfFileExists{inconsolata.sty}{\usepackage[scaled=0.95,varqu]{inconsolata}}{%
  \IfFileExists{beramono.sty}{\usepackage[scaled=0.82]{beramono}}{}}

\lstset{
  basicstyle=\ttfamily\scriptsize,
  breaklines=true,
  breakatwhitespace=false,
  postbreak=\mbox{$\hookrightarrow$\space},
  columns=fullflexible,
  keepspaces=true,
  showstringspaces=false,
  frame=none,
  aboveskip=6pt,
  belowskip=6pt,
}
\Urlmuskip=0mu plus 1mu
\def\UrlBreaks{\do\/\do-\do.\do_\do:}

%% Supplementary numbering.
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thefigure}{S\arabic{figure}}
\renewcommand{\theequation}{S\arabic{equation}}

\begin{document}

\history{Supplementary material.}
\doi{10.1109/ACCESS.2026.DOI}

\title{Supplementary Material: Asymmetric Class Sourcing Creates Provenance
Confounds in Authenticity-Classification Image Datasets}

\author{\uppercase{Sophie Zhu}\authorrefmark{1}}
\address[1]{Mira Costa High School, Manhattan Beach, CA 90266 USA
            (e-mail: sophiezhu2028@gmail.com)}
\corresp{Corresponding author: Sophie Zhu (e-mail: sophiezhu2028@gmail.com).}

\begin{abstract}
@@INTRO@@
\end{abstract}

\begin{keywords}
Supplementary material.
\end{keywords}

\titlepgskip=-15pt
\maketitle
"""


def render_body(blocks):
    """As build_tex.render_body, but sections are unnumbered and keep the
    S-labels already written into the Markdown headings."""
    blocks = bt.merge_lists(blocks)
    out, pending_caption = [], None
    for kind, payload in blocks:
        if kind in ("h2", "h3", "h4"):
            level = {"h2": "section", "h3": "subsection", "h4": "subsubsection"}
            out.append("\\" + level[kind] + "*{"
                       + bt.inline(str(payload)) + "}")
        elif kind == "para":
            text = str(payload)
            m = bt.TABLE_CAP_RE.match(text)
            if m:
                pending_caption = (m.group(1), m.group(2))
                continue
            out.append(bt.inline(text))
        elif kind == "table":
            if pending_caption:
                out.append(bt.render_table(payload, *pending_caption))
                pending_caption = None
            else:
                out.append(bt.render_table(payload, None, ""))
        elif kind == "quote":
            figs = [bt.FIG_RE.match(l) for l in payload]
            if any(figs):
                out.extend(bt.render_figure(f) for f in figs if f)
                rest = [l for l, f in zip(payload, figs) if not f]
                if rest:
                    out.append(bt.inline(" ".join(rest)))
            else:
                out.append(r"\noindent\textit{"
                           + bt.inline(" ".join(payload)) + "}")
        elif kind == "math":
            out.append(bt.render_math(payload))
        elif kind == "list":
            ordered, items = payload
            env = "enumerate" if ordered else "itemize"
            out.append(rf"\begin{{{env}}}")
            out.extend(r"\item " + bt.inline(it) for it in items)
            out.append(rf"\end{{{env}}}")
        elif kind == "code":
            out.append(r"\begin{lstlisting}")
            out.extend(ln.translate(bt.CODE_ASCII) for ln in payload)
            out.append(r"\end{lstlisting}")
        elif kind == "rule":
            continue
        out.append("")
    return out


def main():
    md = SRC.read_text(encoding="utf-8")
    head, _, rest = md.partition("---")
    intro = " ".join(l for l in head.split("\n")
                     if l.strip() and not l.startswith("#")
                     and not l.startswith("**"))

    blocks = bt.parse_blocks(rest)
    body = render_body(blocks)

    tex = (PREAMBLE.replace("@@INTRO@@", bt.inline(intro.strip()))
           + "\n" + "\n".join(body) + "\n\\EOD\n\n\\end{document}\n")

    # No reference list here: cite keys would dangle, so print the numbers.
    tex = re.sub(r"\\cite\{([^}]+)\}",
                 lambda m: "[" + ", ".join(k.strip().replace("ref", "")
                                           for k in m.group(1).split(",")) + "]",
                 tex)
    # Equations cited across the boundary live in the main paper.
    tex = bt.resolve_dangling_eqrefs(tex)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(tex, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  {len(tex.splitlines())} lines, "
          f"{tex.count(chr(92) + 'begin{table')} tables, "
          f"{tex.count(chr(92) + 'begin{figure')} figures")
    if bt._unmapped:
        print("  UNMAPPED non-ASCII: " + " ".join(sorted(bt._unmapped)))


if __name__ == "__main__":
    main()

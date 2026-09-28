"""Render manuscript.md (and optionally supplementary.md) to PDF via pandoc + xelatex.

Usage: python build_pdf.py [manuscript|supplementary|all]
Output: <name>.pdf beside the source. The .md files are not modified.
"""
import io, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(HERE, "..", "paper", "figures").replace("\\", "/")

HEADER = r"""
\usepackage{booktabs}
\usepackage{etoolbox}
\usepackage{amsmath}
\AtBeginEnvironment{longtable}{\footnotesize\setlength{\tabcolsep}{3pt}}
\usepackage{caption}
\captionsetup{font=small,labelformat=empty}
\usepackage{fancyhdr}
\pagestyle{fancy}\fancyhf{}\fancyfoot[C]{\thepage}
\renewcommand{\headrulewidth}{0pt}
\usepackage{xurl}
\usepackage{fontspec}
\newfontfamily\checkfont{Segoe UI Symbol}
\sloppy
"""


def preprocess(md):
    lines = md.split("\n")
    # title: first "# " line becomes metadata
    title = next(l[2:].strip() for l in lines if l.startswith("# "))
    i = lines.index("# " + title)
    body = lines[i + 1:]
    out = []
    for l in body:
        m = re.match(r"> \*\*FIGURE (S?\d+)\.\*\* `([^`]+)` — (.*)", l)
        if m:
            n, f, cap = m.groups()
            base = os.path.join(HERE, "..") if f.startswith("paper/") else HERE
            path = os.path.normpath(os.path.join(base, f)).replace("\\", "/")
            out.append(f"![**Figure {n}.** {cap}]({path}){{width=95%}}")
            continue
        l = l.replace("✓", "`{\\checkfont ✓}`{=latex}")
        out.append(l)
    text = "\n".join(out)
    text = re.sub(r"<sup>(.*?)</sup>", lambda m: "^" + m.group(1).replace(" ", "\\ ") + "^", text)
    # display equations: pandoc passes \tag through to LaTeX display math
    return title, text


def build(name):
    src = os.path.join(HERE, name + ".md")
    title, text = preprocess(io.open(src, encoding="utf-8").read())
    tmp_md = os.path.join(HERE, "_build_" + name + ".md")
    tmp_hdr = os.path.join(HERE, "_build_header.tex")
    io.open(tmp_md, "w", encoding="utf-8").write(text)
    io.open(tmp_hdr, "w", encoding="utf-8").write(HEADER)
    out = os.path.join(HERE, name + ".pdf")
    cmd = [
        "pandoc", tmp_md, "-o", out,
        "--from", "markdown+pipe_tables+tex_math_dollars+raw_tex-implicit_figures+implicit_figures",
        "--pdf-engine=xelatex",
        "--shift-heading-level-by=-1",
        "-H", tmp_hdr,
        "-M", "title=" + title,
        "-V", "mainfont=Cambria", "-V", "mathfont=Cambria Math",
        "-V", "monofont=Consolas",
        "-V", "fontsize=11pt", "-V", "geometry:margin=2.2cm",
        "-V", "linestretch=1.15", "-V", "colorlinks=true",
        "-V", "linkcolor=black", "-V", "urlcolor=blue",
    ]
    print(" ".join(cmd))
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    sys.stdout.write(r.stdout[-3000:]); sys.stderr.write(r.stderr[-6000:])
    for f in (tmp_md, tmp_hdr):
        try:
            os.remove(f)
        except OSError:
            pass
    if r.returncode:
        sys.exit(r.returncode)
    print("wrote", out)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "manuscript"
    for n in (["manuscript", "supplementary"] if which == "all" else [which]):
        build(n)

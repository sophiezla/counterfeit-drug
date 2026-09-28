"""Word version of the manuscript (MDPI accepts Word or LaTeX).

Reuses build_pdf.preprocess (figures inlined from the FIGURE lines) and lets
pandoc write .docx; display equations become editable Word equations (OMML)
and tables stay editable Word tables. Core properties are set explicitly so
the file carries the author's name and nothing else.
Usage: python make_docx.py <out.docx>
"""
import io, os, subprocess, sys, zipfile, re

import build_pdf

HERE = os.path.dirname(os.path.abspath(__file__))
out = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "manuscript.docx"))
title, text = build_pdf.preprocess(io.open(os.path.join(HERE, "manuscript.md"), encoding="utf-8").read())
tmp = os.path.join(HERE, "_docx_build.md")
io.open(tmp, "w", encoding="utf-8").write(text)
r = subprocess.run(["pandoc", tmp, "-o", out, "--from",
                    "markdown+pipe_tables+tex_math_dollars+raw_tex-implicit_figures+implicit_figures",
                    "--shift-heading-level-by=-1", "-M", "title=" + title, "-M", "author=Sophie Zhu"],
                   cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace")
os.remove(tmp)
if r.returncode:
    sys.exit(r.stderr)
# inspect core properties
with zipfile.ZipFile(out) as z:
    core = z.read("docProps/core.xml").decode("utf-8")
print("core.xml creator:", re.findall(r"<dc:creator>(.*?)</dc:creator>", core), "| mentions claude:", "claude" in core.lower())
print("wrote", out)

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
    # Superscripts and subscripts must NOT be mapped into their own math
    # groups. Two adjacent ones (10<super minus><super four>) would emit
    # "$^-$$^4$", and "$$" is LaTeX's display-math delimiter, so the second
    # group opens display math and every brace after it is misparsed. The
    # text-mode commands compose safely instead.
    "¹": r"\textsuperscript{1}", "²": r"\textsuperscript{2}",
    "³": r"\textsuperscript{3}", "⁻": r"\textsuperscript{-}",
    "≫": r"$\gg$", "≪": r"$\ll$", "∼": r"$\sim$", "~": r"$\sim$",
    "Ö": r'\"{O}', "Ü": r'\"{U}', "∩": r"$\cap$", "∪": r"$\cup$",
    "✓": r"$\checkmark$",
    "⁴": r"\textsuperscript{4}", "⁵": r"\textsuperscript{5}",
    "⁶": r"\textsuperscript{6}", "⁹": r"\textsuperscript{9}",
    "₀": r"\textsubscript{0}", "₁": r"\textsubscript{1}",
    "₂": r"\textsubscript{2}",
    "\u00a0": "~", "\u2009": r"\,", "\u200b": "",
}

SPECIALS = {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
            "_": r"\_", "{": r"\{", "}": r"\}", "^": r"\^{}"}

# Code blocks are set verbatim, which cannot represent multi-byte UTF-8.
CODE_ASCII = str.maketrans({
    "→": "->", "←": "<-", "—": "--", "–": "-", "·": ".", "×": "x",
    "≤": "<=", "≥": ">=", "✓": "yes", "≈": "~", "…": "...",
    "“": '"', "”": '"', "‘": "'", "’": "'",
})

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
    text = "".join(out)
    # Safety net for the same hazard in general: two adjacent mapped symbols
    # emit "...$$...", which LaTeX reads as display math. Merging the two
    # groups into one is equivalent for the single symbols mapped here.
    while "$$" in text:
        text = text.replace("$$", "")
    return text


def plain(text):
    """Strip markup for the PDF info dictionary, which takes no markup."""
    import re as _re
    t = _re.sub(r"\*\*|\*|`", "", text)
    t = _re.sub(r"<[^>]+>", "", t)
    return " ".join(t.split()).replace("{", "").replace("}", "")


def author_name(md):
    """The author line is the first bold run after the title."""
    import re as _re
    m = _re.search(r"^\*\*([A-Z][A-Za-z .'-]+)\*\*", md, _re.M)
    return m.group(1).title() if m else ""


def index_terms(md):
    import re as _re
    m = _re.search(r"\*\*INDEX TERMS\*\*\s*(.+)", md)
    return m.group(1).rstrip(".") if m else ""


# ------------------------------------------------------------------- inline
INLINE = re.compile(
    r"(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`|\$[^$]+?\$|<sup>.*?</sup>)")

# The range separator is matched as an en-dash OR as the "--" it has already
# been converted to by the time this runs: escaping happens first, so the
# single-character class silently failed on every range in the manuscript and
# each one was emitted as two \cite commands joined by a dash. That renders
# "[26]-[28]" with a stretchable space in the middle of the range instead of
# letting the cite package compress it.
CITE_RE = re.compile(r"\[(\d+)\](?:\s*(?:–|-{1,2})\s*\[(\d+)\])?")
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
    # A reference that opens a sentence needs the word, or the line starts
    # "(8) composes ...". Mid-sentence, IEEEtran style is the bare number.
    def _eq(m):
        before = s[:m.start()].rstrip()
        opens = (not before) or before.endswith((".", "!", "?", ":", "*"))
        word = "Equation~" if opens else ""
        return rf"{word}\eqref{{eq:{m.group(1)}}}"

    s = EQ_REF_RE.sub(_eq, s)
    s = CITE_RE.sub(_cite, s)
    return s


def inline(text, do_crossrefs=True):
    """Markdown inline -> LaTeX. Maths and code pass through unescaped."""
    # Backslash-escaped markdown must not be read as a delimiter. The manuscript
    # uses "\*" as a literal asterisk for table footnote markers; left alone,
    # the emphasis regex pairs that asterisk with the next one and emits an
    # unbalanced group ("Too many }'s").
    text = text.replace(r"\*", "\x01STAR\x01").replace(r"\_", "\x01US\x01")
    out = []
    for part in INLINE.split(text):
        if not part:
            continue
        # Font switches, NOT \textbf/\textit. ieeeaccess.cls redefines both as
        # \def\textbf#1{{\bf #1}} over a \bf that itself takes an argument
        # (\long\def\bf#1{...}). So \textbf{$-$1.4} expands to {\bf $-$1.4},
        # \bf grabs the bare "$" as its argument, math mode is left open, and
        # the error surfaces as "Extra }, or forgotten $" -- anywhere bold or
        # italic text begins with maths. The switch forms are untouched by the
        # class and take no argument, so they compose safely.
        if part.startswith("**") and part.endswith("**"):
            out.append(r"{\bfseries " + inline(part[2:-2], do_crossrefs) + "}")
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append(r"{\itshape " + inline(part[1:-1], do_crossrefs) + "}")
        elif part.startswith("<sup>"):
            out.append(r"\textsuperscript{"
                       + esc(re.sub(r"</?sup>", "", part)) + "}")
        elif part.startswith("`") and part.endswith("`"):
            code = part[1:-1]
            # \texttt cannot break a long token, so URLs and the long file
            # paths this manuscript cites run off the column. \url breaks at
            # the characters listed in \UrlBreaks in the preamble.
            breakable = ("://" in code
                         or re.match(r"https?://|www\.", code)
                         or (len(code) > 16 and ("/" in code or "_" in code)))
            if breakable and "%" not in code and "#" not in code:
                out.append(r"\url{" + code + "}")
            else:
                out.append(r"\texttt{" + esc(code) + "}")
        elif part.startswith("$") and part.endswith("$"):
            out.append(part)                      # already LaTeX maths
        else:
            out.append(crossrefs(esc(part)) if do_crossrefs else esc(part))
    return ("".join(out)
            .replace("\x01STAR\x01", "*").replace("\x01US\x01", r"\_"))


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
# A reference entry may carry a trailing italic verification annotation: the
# project's audit trail, never part of the citation. It is stripped from both
# built artefacts unless KEEP_INTERNAL_NOTES is set. The rule is structural
# rather than a whitelist of opening words -- an earlier whitelist silently
# passed six notes through into the compiled PDF.
REF_NOTE_RE = re.compile(r"\s*\*([^*]+)\*\s*$")
EQ_TAG_RE = re.compile(r"\\tag\{(\d+)\}")


def strip_ref_note(entry):
    """Drop a reference entry's trailing internal annotation, if it has one.

    A note is a trailing italic span of at least four words that ends in a
    full stop. A bibliographic italic at the end of an entry -- a journal or
    book title -- is shorter than that and carries no terminal period inside
    the italics, so the two are distinguishable without a word list. The test
    is written in Python rather than folded into the pattern because the
    obvious regex for it nests quantifiers and backtracks catastrophically on
    a long note.
    """
    m = REF_NOTE_RE.search(entry)
    if not m:
        return entry
    # A note may close with a quotation or a parenthesis after its full stop.
    # Requiring a bare "." missed one that ended on a quoted phrase, and it
    # printed.
    note = m.group(1).rstrip("\"')]}”’")
    if note.endswith(".") and len(m.group(1).split()) >= 4:
        return entry[:m.start()]
    return entry


def greek_free(text):
    r"""Spell out Greek letters in captions.

    Captions are set with the class's \tablecapfont / \figcapfont, which
    select its "medium" math version. That version binds the operators symbol
    font to T1 Formata, and T1 slot 1 is an acute accent -- so an uppercase
    Greek letter in a caption silently prints as a stray accent mark. It
    affected three captions here. Forcing another math version does not
    recover it, because every math version this class declares uses the same
    text font, so the caption says the letter's name instead.
    """
    for greek, word in (("Δ", "Delta"), ("Σ", "Sigma"),
                        ("μ", "mu"), ("σ", "sigma"),
                        ("λ", "lambda"), ("φ", "phi"),
                        ("α", "alpha"), ("β", "beta"),
                        ("θ", "theta"), ("τ", "tau"),
                        ("η", "eta")):
        text = text.replace(greek, word)
    return text


def render_table(lines, number, caption, note=None):
    rows = [r for r in ([c.strip() for c in ln.strip().strip("|").split("|")]
                        for ln in lines)
            if not re.match(r"^[\s:\-]+$", "".join(r))]
    if not rows:
        return ""
    ncols = max(len(r) for r in rows)
    rows = [r + [""] * (ncols - len(r)) for r in rows]
    size = r"\scriptsize" if ncols > 7 else r"\footnotesize"
    caption = greek_free(caption)

    # Column types are chosen from the content, because a fixed "lccc..."
    # overflows the text block whenever a cell holds prose. Any column whose
    # widest cell exceeds WRAP_CHARS becomes a tabularx X column, which wraps;
    # the rest stay centred at their natural width. Without this, Tables 1, 2
    # and 19 ran up to 525pt past the margin.
    WRAP_CHARS = 26

    def visible(cell):
        """Rough rendered length: drop markup that does not print."""
        s = re.sub(r"\*\*|\*|`", "", cell)
        s = re.sub(r"\\[a-zA-Z]+", "x", s)
        return len(s)

    widest = [max(visible(r[c]) for r in rows) for c in range(ncols)]
    wrap = [w > WRAP_CHARS for w in widest]

    if any(wrap):
        # Share the wrappable width in proportion to how wide each such column
        # actually wants to be, so a long "Notes" column is not squeezed to the
        # same width as a short one.
        n_wrap = sum(wrap)
        total = sum(widest[c] for c in range(ncols) if wrap[c])
        parts = []
        for c in range(ncols):
            if wrap[c]:
                # \hsize multipliers must average 1 across the X columns
                factor = n_wrap * widest[c] / total
                # No hyphenation inside a cell: a ragged-right column is
                # already loose, and a word broken across lines in a narrow
                # cell reads as a typo ("re-derive" split mid-word).
                parts.append(r">{\hsize=" + f"{factor:.3f}"
                             + r"\hsize\raggedright\arraybackslash"
                             + r"\hyphenpenalty=10000\exhyphenpenalty=10000}X")
            else:
                parts.append("c")
        spec = "".join(parts)
        # A captioned table becomes a full-width table* float; an uncaptioned
        # one stays in the two-column text, where the available width is a
        # single column. Using \textwidth for the latter overflowed by exactly
        # \textwidth - \columnwidth = 262.4pt.
        env = "tabularx"
        width = r"{\textwidth}" if number is not None else r"{\columnwidth}"
    else:
        spec = "l" + "c" * (ncols - 1)
        env, width = "tabular", ""

    body = []
    for ri, row in enumerate(rows):
        # A long identifier is one unbreakable token, and these columns
        # disable hyphenation on purpose, so "Counterfeit_med_detection"
        # overflowed its column by 21pt. An underscore is a legal place
        # to break an identifier and needs no hyphen to show for it.
        cells = [inline(c).replace(r"\_", r"\_\allowbreak{}")
                 for c in row]
        if ri == 0:                      # switch form, see inline() above
            cells = [r"{\bfseries " + c + "}" if c else c for c in cells]
        body.append(" & ".join(cells) + r" \\")
        if ri == 0:
            body.append(r"\midrule")

    grid = [
        rf"\begin{{{env}}}{width}{{{spec}}}",
        r"\toprule",
        *body,
        r"\bottomrule",
        rf"\end{{{env}}}",
    ]
    if env == "tabular":
        # A many-column numeric table has no wrappable column, so it keeps its
        # natural width and can exceed the text block -- which LaTeX reports
        # only as "Overfull \hbox ... while \output is active", from the float
        # rather than from any source line. Shrink to fit, but only when it
        # actually overflows, so tables that already fit are left alone.
        # \linewidth, not \textwidth: an uncaptioned table is set in the
        # running text of ONE column, where \textwidth is the width of
        # both of them. Guarding against the wrong one let a table
        # overflow its column by 39.6pt while the build reported it fit.
        # \linewidth is right in both places -- the column inside running
        # text, the full block inside a table* float.
        grid = ([r"\resizebox{\ifdim\width>\linewidth\linewidth"
                 r"\else\width\fi}{!}{%"] + grid + ["}"])
    core = [
        size,
        # Wrapping tables give the saved padding back to the text, which is
        # what lets them fit without hyphenating inside a cell.
        r"\setlength{\tabcolsep}{" + ("3pt" if any(wrap) else "4pt") + "}",
        r"\renewcommand{\arraystretch}{1.15}",
        *grid,
    ]
    if note:
        # A tabular note belongs inside the float. Left in the running text it
        # is a paragraph that explains a symbol the reader is looking at on
        # another page, because a table* can only land at the top of a page.
        # \parbox rather than a bare line so a note longer than the text block
        # wraps and stays left-aligned under the rule.
        core += [
            r"\vspace{2pt}",
            r"\parbox{\textwidth}{\footnotesize\raggedright " + inline(note)
            + "}",
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


# Note for anyone adding a figure: every figure is generated with
# "savefig.bbox: tight", which crops the empty width away, so a plot drawn
# 6.6 in wide can be saved 5.25 in wide at an unchanged height -- and
# width=\textwidth then scales that taller aspect UP rather than down. A 2.7
# in plot reached 3.9 in on the page that way. The fix belongs in
# make_figures.py, in the figsize and in whatever puts the white space there
# (a suptitle, or a legend anchored outside the axes); a height cap here
# would also shrink the three tall diagrams, which need their width.
def render_figure(m):
    number, relpath, caption = m.groups()
    name = Path(relpath).name
    return "\n".join([
        r"\begin{figure*}[!t]",
        r"\centerline{\includegraphics[width=\textwidth]{figures/"
        + name + "}}",
        rf"\caption{{{inline(greek_free(caption))}}}",
        rf"\label{{fig:{number}}}",
        r"\end{figure*}",
        "",
    ])


MATH_FITS = 95          # characters of source that fit one column comfortably


def _fit_math(inner):
    """Make a wide display equation fit a 85.29mm column.

    Several equations here state two things joined by \\qquad, which is wider
    than a column and overflows silently. Splitting at that join is the
    typographically correct fix. Equations built on a cases environment cannot
    be split that way -- the separators are structural -- so those are scaled
    instead, which is the lesser evil and still legible at 7pt.
    """
    if len(inner) <= MATH_FITS:
        return inner

    if r"\begin{cases}" in inner or r"\begin{aligned}" in inner:
        return r"\resizebox{\columnwidth}{!}{$\displaystyle " + inner + "$}"

    for sep in (r"\qquad", r"\quad"):
        if sep in inner:
            parts = [p.strip() for p in inner.split(sep) if p.strip()]
            if len(parts) > 1:
                body = " \\\\[2pt]\n".join(parts)
                return "\\begin{aligned}\n" + body + "\n\\end{aligned}"
    return inner


def render_math(raw):
    inner = raw.strip().strip("$").strip()
    tag = EQ_TAG_RE.search(inner)
    inner = _fit_math(EQ_TAG_RE.sub("", inner).strip())
    if tag:
        return ("\\begin{equation}\n"
                f"\\label{{eq:{tag.group(1)}}}\n{inner}\n\\end{{equation}}\n")
    return f"\\begin{{equation*}}\n{inner}\n\\end{{equation*}}\n"


HEAD_NUM_RE = re.compile(r"^(?:[IVXLC]+|[A-Z]|\d+)\.\s+")
UNNUMBERED = ("Acknowledgment", "Data and Code Availability",
              "Author Biographies",
              "Ethics, Conflicts of Interest, and Data Provenance")


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


# A paragraph opening with an escaped asterisk, immediately after a table, is
# that table's tabular note: it defines a mark used in the cells. It has to
# travel with the float. Left as running text it explains a symbol the reader
# is looking at on a different page, since a table* only lands at a page top.
TABLE_NOTE_RE = re.compile(r"^\\\*\s+")


def table_note_after(blocks, idx):
    """Return the tabular note following the table at blocks[idx], or None."""
    if idx + 1 >= len(blocks):
        return None
    kind, payload = blocks[idx + 1]
    if kind != "para":
        return None
    text = str(payload)
    return text if TABLE_NOTE_RE.match(text) else None


def render_body(blocks):
    blocks = merge_lists(blocks)
    out, in_refs, bibitems = [], False, []
    pending_caption = None
    consumed_note = False

    skipping = False
    for idx, (kind, payload) in enumerate(blocks):
        # The biography is emitted by build_biography() below, which reads
        # this same section and wraps it in the class's own IEEEbiography
        # environment (which places the photograph). Rendering the Markdown
        # section here as well would duplicate it.
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
            if consumed_note:
                # Already emitted inside the preceding float.
                consumed_note = False
                continue
            m = TABLE_CAP_RE.match(text)
            if m:
                pending_caption = m.groups()
                continue
            if in_refs:
                r = REF_RE.match(text)
                if r:
                    entry = r.group(2)
                    if not KEEP_INTERNAL_NOTES:
                        entry = strip_ref_note(entry)
                    bibitems.append((r.group(1), inline(entry,
                                                        do_crossrefs=False)))
                    continue
            out.append(inline(text))
        elif kind == "table":
            note = table_note_after(blocks, idx)
            consumed_note = note is not None
            if pending_caption:
                out.append(render_table(payload, *pending_caption, note=note))
                pending_caption = None
            else:                       # an uncaptioned table in the source
                out.append(render_table(payload, None, "", note=note))
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
            # lstlisting, not verbatim: verbatim cannot break a long line, and
            # Appendix C's command lines are wider than a column, which alone
            # produced eleven of the overfull boxes.
            out.append(r"\begin{lstlisting}")
            # lstlisting is verbatim-like and rejects multi-byte UTF-8, so the
            # arrows in Appendix C's pipeline comments become ASCII.
            out.extend(ln.translate(CODE_ASCII) for ln in payload)
            out.append(r"\end{lstlisting}")
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
\usepackage{tabularx}
\usepackage{listings}
\usepackage{microtype}
\usepackage{url}

%% Typewriter face. The class's default is Courier, which is wide, light and
%% sits badly beside Times and Formata. Inconsolata is narrower and darker,
%% which also shortens the long file paths this manuscript quotes inline.
\IfFileExists{inconsolata.sty}{\usepackage[scaled=0.95,varqu]{inconsolata}}{%
  \IfFileExists{beramono.sty}{\usepackage[scaled=0.82]{beramono}}{}}

%% Wide content control. The text block is 177.53mm and a column 85.29mm, so
%% long tokens and wide tables overflow silently unless told how to break.
\lstset{
  basicstyle=\ttfamily\scriptsize,
  breaklines=true,
  breakatwhitespace=false,
  postbreak=\mbox{$\hookrightarrow$\space},   % no colour: the class does not
                                              % define xcolor's named colours
  columns=fullflexible,
  keepspaces=true,
  showstringspaces=false,
  frame=none,
  aboveskip=6pt,
  belowskip=6pt,
}
%% Float placement. Every table and figure here is full-width, and a
%% double-column float can only be set at the top of a page. With LaTeX's
%% defaults -- at most two per page top, filling at most 0.7 of it, and a
%% float page declared as soon as the queue fills 0.5 of one -- the queue
%% drains into pages that are nothing but floats: one page of this manuscript
%% carried four floats and no text at all, several pages after the text that
%% introduces them. Raising the per-page allowance and the fraction a float
%% page must reach lets the queue drain onto the tops of text pages instead.
\setcounter{topnumber}{3}
\setcounter{dbltopnumber}{3}
\setcounter{totalnumber}{4}
\renewcommand{\topfraction}{0.92}
\renewcommand{\dbltopfraction}{0.92}
\renewcommand{\textfraction}{0.08}
\renewcommand{\floatpagefraction}{0.90}
\renewcommand{\dblfloatpagefraction}{0.95}

\Urlmuskip=0mu plus 0.15mu       % enough give to break a long URL, not
                                 % enough to gap it visibly: at plus 1mu
                                 % an 85 mm column rendered the repo URL
                                 % as https : / / github . com / ...
\def\UrlBreaks{\do\/\do-\do.\do_\do:}
\usepackage[colorlinks=true,linkcolor=blue,citecolor=blue,
            urlcolor=blue]{hyperref}
\hypersetup{pdftitle={@@PDFTITLE@@},pdfauthor={@@PDFAUTHOR@@},
            pdfsubject={IEEE Access submission},
            pdfkeywords={@@PDFKEYWORDS@@}}
\def\BibTeX{{\rm B\kern-.05em{\sc i\kern-.025em b}\kern-.08em
    T\kern-.1667em\lower.7ex\hbox{E}\kern-.125emX}}

\begin{document}

%% The ieeeaccess class defaults its page footer to VOLUME 11, 2023. Set the
%% submission volume and year so the footer is not stale; IEEE production
%% replaces these along with \history and \doi below.
\vol{14}
\year{2026}

\history{Date of publication xxxx 00, 0000, date of current version
         xxxx 00, 0000.}
\doi{10.1109/ACCESS.2026.DOI}

\title{@@TITLE@@}

\author{@@AUTHORS@@}

\address[1]{Mira Costa High School, Manhattan Beach, CA 90266 USA
            (e-mail: sophiezhu2028@gmail.com; ORCID: 0009-0004-2403-910X)}

\tfootnote{This work received no specific grant from any funding agency in the
public, commercial, or not-for-profit sectors. The manuscript and the
accompanying code were prepared with the assistance of Claude, an AI assistant
developed by Anthropic; see the generative-AI disclosure in the Ethics
section.}

\corresp{Corresponding author: Sophie Zhu (e-mail: sophiezhu2028@gmail.com).}

\begin{abstract}
@@ABSTRACT@@
\end{abstract}

\begin{keywords}
@@KEYWORDS@@
\end{keywords}

\titlepgskip=-15pt

\maketitle
"""

# The biography is taken from paper.md's "Author Biographies" section, not
# stored here. It was stored here until 2026-08-29, which meant two copies of
# it existed and an edit to the Markdown silently did not reach the PDF --
# exactly the drift the "paper.md is the single source of truth" rule exists
# to prevent, and exactly how it was found.
BIOGRAPHY_TEMPLATE = r"""
\begin{IEEEbiography}[{\includegraphics[width=1in,height=1.25in,clip,
    keepaspectratio]{figures/author_photo.jpeg}}]{@@NAME@@}
@@BODY@@
\end{IEEEbiography}
"""


def build_biography(md):
    """Render the manuscript's own biography paragraph into IEEEbiography.

    The environment takes the author's name as its argument and the biography
    text as its body, beginning mid-sentence ("is a student at..."), which is
    how the class typesets the run-in name.
    """
    m = re.search(r"^\*\*([A-Z][A-Z .'-]+)\*\*\s+(is\b.*?)(?=\n\n|\Z)",
                  md, re.M | re.S)
    if not m:
        raise SystemExit(
            "no author biography found in paper.md: expected a paragraph "
            "starting '**NAME** is ...' under Author Biographies")
    name, body = m.group(1).strip(), " ".join(m.group(2).split())
    return (BIOGRAPHY_TEMPLATE
            .replace("@@NAME@@", name)
            .replace("@@BODY@@", inline(esc(body))))

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


def resolve_dangling_eqrefs(tex):
    r"""Turn \eqref at a label this document does not define into literal text.

    The manuscript and its supplement cite each other's equations. Within a
    document \eqref is right; across the boundary it cannot resolve, so the
    reference is printed as a plain number instead of a dangling "??".
    """
    labels = set(re.findall(r"\\label\{(eq:\d+)\}", tex))

    def fix(m):
        key = m.group(1)
        if key in labels:
            return m.group(0)
        return "(" + key.split(":")[1] + ")"
    return re.sub(r"\\eqref\{(eq:\d+)\}", fix, tex)


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

    # \EOD is required by ieeeaccess.cls: it typesets the end-of-document
    # marker and the class raises "You have not used the command \EOD at the
    # end of your document" without it.
    # Placeholder substitution rather than %-formatting: the preamble is LaTeX
    # and contains literal % comments, which %-formatting would try to read as
    # conversion specifiers.
    preamble = PREAMBLE
    for token, value in (
        ("@@TITLE@@", inline(title, do_crossrefs=False)),
        # Info-dictionary strings: plain text only.
        ("@@PDFTITLE@@", plain(title)),
        ("@@PDFAUTHOR@@", plain(author_name(md))),
        ("@@PDFKEYWORDS@@", plain(index_terms(md))),
        ("@@AUTHORS@@", authors),
        ("@@ABSTRACT@@", inline(abstract, do_crossrefs=False)),
        ("@@KEYWORDS@@", inline(keywords, do_crossrefs=False)),
    ):
        assert token in preamble, f"preamble lost its {token} placeholder"
        preamble = preamble.replace(token, value)

    tex = (preamble + "\n" + "\n".join(body) + "\n".join(bib)
           + build_biography(md)
           + "\n\\EOD\n\n\\end{document}\n")
    tex = resolve_dangling_eqrefs(tex)

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

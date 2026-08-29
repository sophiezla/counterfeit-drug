"""
Build a local HTML tool for drawing one product bounding box per external image.

Why this exists. The attention audit's strongest claim -- that on external
images the models take their evidence for "authentic" from the background --
is currently supported by a four-way human categorisation of 40 heatmaps and
by a border-mass statistic that is purely radial: it asks how far attention
sits from the centre of the frame, not whether it sits on the product. Those
two are only the same thing when the product is centred. Section X names the
fix: Grad-CAM mass inside an annotated product box. That needs one box per
image, and nothing else.

So this tool asks for exactly that and nothing else, in the fastest form the
task allows: one drag per image, which saves and advances on release. There is
no confirm button, no next button and no per-image form. At roughly two
seconds an image the 150-image Split C set is about five minutes of work, and
Split D another five.

    python scripts/23_build_product_box_tool.py            # Split C (default)
    python scripts/23_build_product_box_tool.py --split d  # Split D

Then open data/metadata/product_box_tool_split_c.html in a browser -- no server
needed, images load over relative file:// paths. Progress auto-saves to
localStorage keyed to the file, so closing and reopening resumes. Export CSV
when done (or partway) and save it next to the tool as
data/metadata/product_boxes_split_c.csv, then run
modeling/attention_in_box.py to turn the boxes into the measurement.

Keys, all one-handed and all optional -- the drag alone is the normal path:
    drag        draw the box; releasing saves it and advances
    R           redraw the current image (also: just drag again)
    <-          go back one image
    W           the product fills the frame (box = whole image)
    S           skip: no product identifiable, or unsure
    Enter       advance without changing anything

Coordinates are exported as fractions of the image's own width and height, so
they stay valid at any resolution the measurement script decodes at.

Output: data/metadata/product_box_tool_split_<c|d>.html
"""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "data" / "metadata"
CANDIDATE_PROV = META / "split_c_candidate_provenance.csv"
SPLIT_D_DIR = ROOT / "data" / "raw" / "mendeley_split_d"


def split_c_items():
    with open(CANDIDATE_PROV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [{"id": r["image_id"],
             "path": "../raw/" + r["orig_relpath"].replace("\\", "/")}
            for r in rows]


def split_d_items():
    paths = sorted(p for p in SPLIT_D_DIR.iterdir()
                   if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    return [{"id": f"split_d_{p.stem}",
             "path": f"../raw/mendeley_split_d/{p.name}"} for p in paths]


TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Product box annotation &mdash; __TITLE__</title>
<style>
  body { font-family: -apple-system, Segoe UI, sans-serif; margin: 0;
         background: #1e1e1e; color: #eee; overflow: hidden; }
  #bar { display: flex; justify-content: space-between; align-items: center;
         padding: 8px 16px; background: #111; font-size: 14px; }
  #bar b { color: #6fb2ff; }
  #wrap { display: flex; align-items: center; justify-content: center;
          height: calc(100vh - 84px); }
  #stage { position: relative; line-height: 0; cursor: crosshair; }
  #img { max-height: calc(100vh - 100px); max-width: 96vw; user-select: none;
         -webkit-user-drag: none; }
  #box { position: absolute; border: 2px solid #6fb2ff;
         background: rgba(111,178,255,0.16); display: none;
         pointer-events: none; }
  #prog { height: 4px; background: #333; }
  #fill { height: 4px; background: #6fb2ff; width: 0; }
  #hint { padding: 4px 16px; background: #111; font-size: 12px; color: #999; }
  #err { color: #ff9a76; font-size: 15px; padding: 20px; display: none; }
  #done-banner { display: none; padding: 8px 16px; background: #14532d;
                 color: #d7ffe6; font-size: 14px; text-align: center; }
  button { background: #2a78d6; color: #fff; border: 0; padding: 6px 12px;
           border-radius: 4px; cursor: pointer; font-size: 13px; }
</style>
</head>
<body>
<div id="bar">
  <div><b id="n">0</b> / <span id="total">0</span> &nbsp; boxed:
       <b id="done">0</b> &nbsp; skipped: <b id="skipped">0</b></div>
  <div id="name"></div>
  <div><button onclick="exportCsv()">Export CSV</button></div>
</div>
<div id="prog"><div id="fill"></div></div>
<div id="wrap"><div id="stage"><img id="img" draggable="false"><div id="box">
  </div></div><div id="err"></div></div>
<div id="done-banner"></div>
<div id="hint">drag a box round the product &mdash; releasing saves and advances
  &nbsp;|&nbsp; W whole frame &nbsp; S skip &nbsp; R redraw &nbsp;
  &larr; back &nbsp; Enter next</div>

<script>
const ITEMS = __ITEMS__;
const KEY = "product_boxes_" + location.pathname;
let i = 0, boxes = JSON.parse(localStorage.getItem(KEY) || "{}");

const img = document.getElementById("img"), box = document.getElementById("box");
const stage = document.getElementById("stage");

function show() {
  i = Math.max(0, Math.min(ITEMS.length - 1, i));
  const it = ITEMS[i];
  img.src = it.path;
  document.getElementById("n").textContent = i + 1;
  document.getElementById("total").textContent = ITEMS.length;
  document.getElementById("name").textContent = it.id;
  const vals = Object.values(boxes);
  document.getElementById("done").textContent =
      vals.filter(v => v.status === "box").length;
  document.getElementById("skipped").textContent =
      vals.filter(v => v.status === "skip").length;
  document.getElementById("fill").style.width =
      (100 * vals.length / ITEMS.length) + "%";
  const banner = document.getElementById("done-banner");
  if (vals.length >= ITEMS.length) {
    banner.textContent = "all " + ITEMS.length + " images recorded — "
        + "click Export CSV, and save it as __CSVNAME__";
    banner.style.display = "block";
  } else { banner.style.display = "none"; }
  draw(boxes[it.id]);
}

function draw(rec) {
  if (!rec || rec.status !== "box") { box.style.display = "none"; return; }
  const w = img.clientWidth, h = img.clientHeight;
  box.style.left = (rec.x0 * w) + "px";
  box.style.top = (rec.y0 * h) + "px";
  box.style.width = ((rec.x1 - rec.x0) * w) + "px";
  box.style.height = ((rec.y1 - rec.y0) * h) + "px";
  box.style.display = "block";
}

function save(rec) {
  boxes[ITEMS[i].id] = rec;
  localStorage.setItem(KEY, JSON.stringify(boxes));
}

let dragging = false, sx = 0, sy = 0;
stage.addEventListener("mousedown", e => {
  dragging = true;
  [sx, sy] = at(e);
  box.style.left = sx + "px"; box.style.top = sy + "px";
  box.style.width = "0px"; box.style.height = "0px";
  box.style.display = "block";
  e.preventDefault();
});
function at(e) {
  // Clamp to the image: a drag may legitimately end past its edge, and the
  // box should stop at the frame rather than record a negative coordinate.
  const r = img.getBoundingClientRect();
  return [Math.max(0, Math.min(img.clientWidth, e.clientX - r.left)),
          Math.max(0, Math.min(img.clientHeight, e.clientY - r.top))];
}
window.addEventListener("mousemove", e => {
  if (!dragging) return;
  const [x, y] = at(e);
  box.style.left = Math.min(sx, x) + "px";
  box.style.top = Math.min(sy, y) + "px";
  box.style.width = Math.abs(x - sx) + "px";
  box.style.height = Math.abs(y - sy) + "px";
});
window.addEventListener("mouseup", e => {
  if (!dragging) return;
  dragging = false;
  const [x, y] = at(e);
  const w = img.clientWidth, h = img.clientHeight;
  // A hidden or unloaded image has zero size, and dividing by it would
  // record NaN coordinates that look like a real annotation.
  if (!w || !h) { box.style.display = "none"; return; }
  const x0 = Math.max(0, Math.min(sx, x) / w), x1 = Math.min(1, Math.max(sx, x) / w);
  const y0 = Math.max(0, Math.min(sy, y) / h), y1 = Math.min(1, Math.max(sy, y) / h);
  // A stray click is not a box. Anything under 2% of the frame is ignored, so
  // a mis-click does not silently record a degenerate annotation.
  if ((x1 - x0) * (y1 - y0) < 0.02) { draw(boxes[ITEMS[i].id]); return; }
  save({status: "box", x0: +x0.toFixed(4), y0: +y0.toFixed(4),
         x1: +x1.toFixed(4), y1: +y1.toFixed(4)});
  i++; show();
});

document.addEventListener("keydown", e => {
  const k = e.key.toLowerCase();
  if (k === "arrowleft") { i--; show(); }
  else if (k === "arrowright" || e.key === "Enter") { i++; show(); }
  else if (k === "w") {
    save({status: "box", x0: 0, y0: 0, x1: 1, y1: 1}); i++; show();
  }
  else if (k === "s") { save({status: "skip"}); i++; show(); }
  else if (k === "r") { delete boxes[ITEMS[i].id];
                        localStorage.setItem(KEY, JSON.stringify(boxes));
                        show(); }
  else return;
  e.preventDefault();
});

function exportCsv() {
  const lines = ["image_id,status,x0,y0,x1,y1"];
  for (const it of ITEMS) {
    const r = boxes[it.id];
    if (!r) continue;
    lines.push(r.status === "box"
      ? [it.id, "box", r.x0, r.y0, r.x1, r.y1].join(",")
      : [it.id, "skip", "", "", "", ""].join(","));
  }
  const blob = new Blob([lines.join("\\n") + "\\n"], {type: "text/csv"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "__CSVNAME__";
  a.click();
}

img.addEventListener("load", () => {
  document.getElementById("err").style.display = "none";
  img.style.display = "";
  draw(boxes[ITEMS[i].id]);
});
img.addEventListener("error", () => {
  img.style.display = "none";
  const el = document.getElementById("err");
  el.textContent = "cannot load " + ITEMS[i].path + " — open this file "
      + "from inside data/metadata/ so the relative path resolves";
  el.style.display = "block";
});
show();
</script>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", choices=("c", "d"), default="c")
    args = ap.parse_args()

    items = split_c_items() if args.split == "c" else split_d_items()
    out = META / f"product_box_tool_split_{args.split}.html"
    csvname = f"product_boxes_split_{args.split}.csv"
    title = f"Split {args.split.upper()}"

    # Marker substitution rather than % or .format: the template is HTML, CSS
    # and JavaScript at once, all three of which use braces and percent signs
    # for their own purposes, and escaping every one of them is how a "2%" in
    # a code comment silently breaks the build.
    html = (TEMPLATE
            .replace("__ITEMS__", json.dumps(items))
            .replace("__TITLE__", title)
            .replace("__CSVNAME__", csvname))
    out.write_text(html, encoding="utf-8")

    print(f"wrote {out.relative_to(ROOT)} ({len(items)} images)")
    print(f"open it in a browser, drag one box per image, then Export CSV and "
          f"save as data/metadata/{csvname}")
    print("then: python modeling/attention_in_box.py")


if __name__ == "__main__":
    main()

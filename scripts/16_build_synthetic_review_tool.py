"""
Step 16 — Build a self-contained local HTML tool for manually reviewing
the 150 synthetic counterfeit candidates (15_generate_synthetic_
counterfeit.py) side-by-side with their real-authentic source photo.

Same fast, keyboard-driven, auto-saving pattern as
manual_review_tool.html / modality_tagging_tool.html. The reviewer judges
each synthetic image on plausibility -- does it look like a believable
degraded/counterfeit-style photo, or does it read as an obvious digital
artifact? -- not on whether the underlying product is real (it always is;
only the perturbation is synthetic).

Output: data/metadata/synthetic_review_tool.html
  Open directly in a browser, no server needed. Progress auto-saves to
  localStorage. Export CSV any time; consumed by
  17_apply_synthetic_review.py.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATE_CSV = ROOT / "data" / "metadata" / "synthetic_counterfeit_candidate_provenance.csv"
OUT_HTML = ROOT / "data" / "metadata" / "synthetic_review_tool.html"


def main():
    with open(CANDIDATE_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    images = [{
        "id": r["image_id"],
        "synthPath": f"../raw/{r['orig_relpath']}",
        "origPath": f"../raw/{r['base_source_relpath']}",
    } for r in rows]

    images_json = json.dumps(images)

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>PharmaChecked v2 -- synthetic counterfeit review</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, sans-serif; margin: 0; background: #1e1e1e; color: #eee; }}
  #bar {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; background: #111; position: sticky; top: 0; }}
  #progress {{ font-size: 14px; color: #aaa; }}
  #main {{ display: flex; flex-direction: column; align-items: center; padding: 20px; }}
  #compare {{ display: flex; gap: 16px; }}
  .panel {{ background: #333; padding: 10px; border-radius: 8px; text-align: center; }}
  .panel img {{ max-width: 420px; max-height: 560px; display: block; }}
  .panel .caption {{ margin-top: 6px; font-size: 13px; color: #aaa; }}
  #meta {{ margin-top: 10px; font-size: 14px; color: #ccc; text-align: center; }}
  #buttons {{ margin-top: 18px; display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }}
  button {{ font-size: 15px; padding: 10px 16px; border-radius: 6px; border: none; cursor: pointer; color: white; }}
  .approve {{ background: #2d6a2d; }}
  .reject {{ background: #a83232; }}
  .unsure {{ background: #6b6b1f; }}
  .nav {{ background: #444; }}
  button:hover {{ filter: brightness(1.2); }}
  #notes {{ margin-top: 10px; width: 400px; max-width: 90vw; padding: 6px; border-radius: 4px; border: 1px solid #555; background: #222; color: #eee; }}
  #tagged-badge {{ position: absolute; top: -10px; right: -10px; font-size: 12px; padding: 3px 8px; border-radius: 10px; }}
  #keys {{ margin-top: 14px; font-size: 12px; color: #888; text-align: center; max-width: 700px; }}
  #export {{ background: #1a5fb4; }}
</style>
</head>
<body>

<div id="bar">
  <div>PharmaChecked v2 -- synthetic counterfeit review (is this a believable degraded/counterfeit-style photo?)</div>
  <div id="progress"></div>
  <button id="export">Export CSV</button>
</div>

<div id="main">
  <div style="position: relative;">
    <div id="compare">
      <div class="panel"><img id="orig" src=""><div class="caption">original (real authentic photo)</div></div>
      <div class="panel"><img id="synth" src=""><div class="caption">synthetic counterfeit candidate</div></div>
    </div>
    <div id="tagged-badge"></div>
  </div>
  <div id="meta"></div>
  <div id="buttons">
    <button class="nav" id="prev">&larr; Prev</button>
    <button class="approve" id="btn-approve">Approve -- plausible (Space/&rarr;)</button>
    <button class="reject" id="btn-reject">Reject -- looks like an artifact (R)</button>
    <button class="unsure" id="btn-unsure">Unsure (U)</button>
  </div>
  <input id="notes" type="text" placeholder="optional note (press Enter to save note without changing tag)">
  <div id="keys">
    Keyboard: <b>Space</b> or <b>&rarr;</b> = approve &amp; next &middot; <b>R</b> = reject &amp; next &middot;
    <b>U</b> = unsure &amp; next &middot; <b>&larr;</b> = back.
    Approve only if the synthetic image looks like a believable degraded/counterfeit-style photo, not an obvious digital glitch.
    Progress auto-saves to this browser. Click "Export CSV" any time.
  </div>
</div>

<script>
const IMAGES = {images_json};
const STORAGE_KEY = "pharmavision_synthetic_review_v3";

let state = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{{}}");
let idx = state._idx || 0;

function save() {{
  state._idx = idx;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}}

function render() {{
  const im = IMAGES[idx];
  document.getElementById("orig").src = im.origPath;
  document.getElementById("synth").src = im.synthPath;
  document.getElementById("meta").innerHTML =
    `#${{idx+1}} / ${{IMAGES.length}} &mdash; ${{im.id}}`;
  const tag = state[im.id];
  const badge = document.getElementById("tagged-badge");
  if (tag) {{
    badge.textContent = tag.flag;
    badge.style.background = {{approve:"#2d6a2d", reject:"#a83232", unsure:"#6b6b1f"}}[tag.flag];
    badge.style.display = "inline-block";
  }} else {{
    badge.style.display = "none";
  }}
  document.getElementById("notes").value = (tag && tag.notes) || "";
  const done = IMAGES.filter(x => state[x.id]).length;
  document.getElementById("progress").textContent = `${{done}} / ${{IMAGES.length}} reviewed`;
  save();
}}

function tag(flag) {{
  const im = IMAGES[idx];
  const notes = document.getElementById("notes").value;
  state[im.id] = {{flag: flag, notes: notes}};
  if (idx < IMAGES.length - 1) idx++;
  render();
}}

function saveNoteOnly() {{
  const im = IMAGES[idx];
  const notes = document.getElementById("notes").value;
  const existing = state[im.id];
  state[im.id] = {{flag: existing ? existing.flag : "approve", notes: notes}};
  render();
}}

document.getElementById("btn-approve").onclick = () => tag("approve");
document.getElementById("btn-reject").onclick = () => tag("reject");
document.getElementById("btn-unsure").onclick = () => tag("unsure");
document.getElementById("prev").onclick = () => {{ if (idx > 0) idx--; render(); }};

document.addEventListener("keydown", (e) => {{
  if (document.activeElement.id === "notes") {{
    if (e.key === "Enter") {{ saveNoteOnly(); document.activeElement.blur(); }}
    return;
  }}
  if (e.key === " " || e.key === "ArrowRight") {{ e.preventDefault(); tag("approve"); }}
  else if (e.key.toLowerCase() === "r") tag("reject");
  else if (e.key.toLowerCase() === "u") tag("unsure");
  else if (e.key === "ArrowLeft") {{ if (idx > 0) idx--; render(); }}
}});

document.getElementById("export").onclick = () => {{
  let csv = "image_id,flag,notes\\n";
  for (const im of IMAGES) {{
    const t = state[im.id];
    const flag = t ? t.flag : "";
    const notes = t ? (t.notes || "").replace(/"/g, '""') : "";
    csv += `${{im.id}},${{flag}},"${{notes}}"\\n`;
  }}
  const blob = new Blob([csv], {{type: "text/csv"}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "synthetic_counterfeit_review.csv";
  a.click();
}};

render();
</script>
</body>
</html>
"""
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_HTML}")
    print(f"{len(images)} images loaded for review.")


if __name__ == "__main__":
    main()

"""
Step 11 — Build a local HTML tool for manually tagging modality (blister
pack / outer packaging / other) across the current cleaned 524-image
Kaggle pool. Same interface pattern as scripts/09_build_manual_review_tool.py
(keyboard-driven, auto-advance, auto-save to localStorage, CSV export) so
it feels identical to use.

This is the plan's Part 2.2 modality classification, run over the pool as
it stands AFTER the watermark/screenshot cleanup (scripts/10), so results
aren't invalidated by a subsequent data change.

Output: data/metadata/modality_tagging_tool.html
  Open directly in a browser, no server needed. Export CSV when done
  (or partway through) -> data/metadata/manual_modality_tags.csv, then
  run scripts/12_apply_modality_tags.py to write it into provenance.csv's
  `modality` column (no exclusions happen here -- this is a label, not a
  filter; deciding whether to filter to outer-packaging-only is a separate
  step, since it would remove a large fraction of the pool).
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROVENANCE = ROOT / "data" / "metadata" / "provenance.csv"
OUT_HTML = ROOT / "data" / "metadata" / "modality_tagging_tool.html"


def main():
    with open(PROVENANCE, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["source_dataset"] == "Kaggle - Fake vs Real Medicine"]
    rows.sort(key=lambda r: r["image_id"])

    images = [{"id": r["image_id"], "path": f"../raw/{r['orig_relpath'].replace(chr(92), '/')}",
               "label": r["class_label"]} for r in rows]
    images_json = json.dumps(images)

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>PharmaChecked v2 -- modality tagging</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, sans-serif; margin: 0; background: #1e1e1e; color: #eee; }}
  #bar {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; background: #111; position: sticky; top: 0; }}
  #progress {{ font-size: 14px; color: #aaa; }}
  #main {{ display: flex; flex-direction: column; align-items: center; padding: 20px; }}
  #imgwrap {{ background: #333; padding: 10px; border-radius: 8px; }}
  #img {{ max-width: 560px; max-height: 560px; display: block; }}
  #meta {{ margin-top: 10px; font-size: 14px; color: #ccc; text-align: center; }}
  #meta .label {{ font-weight: bold; }}
  #buttons {{ margin-top: 18px; display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }}
  button {{ font-size: 15px; padding: 10px 16px; border-radius: 6px; border: none; cursor: pointer; color: white; }}
  .blister {{ background: #1a6fa8; }}
  .packaging {{ background: #2d6a2d; }}
  .other {{ background: #8a4a1f; }}
  .nav {{ background: #444; }}
  button:hover {{ filter: brightness(1.2); }}
  #notes {{ margin-top: 10px; width: 400px; max-width: 90vw; padding: 6px; border-radius: 4px; border: 1px solid #555; background: #222; color: #eee; }}
  #tagged-badge {{ position: absolute; top: -10px; right: -10px; font-size: 12px; padding: 3px 8px; border-radius: 10px; }}
  #keys {{ margin-top: 14px; font-size: 12px; color: #888; text-align: center; max-width: 560px; }}
  #export {{ background: #1a5fb4; }}
</style>
</head>
<body>

<div id="bar">
  <div>PharmaChecked v2 -- modality tagging (Kaggle pool, post-cleanup)</div>
  <div id="progress"></div>
  <button id="export">Export CSV</button>
</div>

<div id="main">
  <div style="position: relative;">
    <div id="imgwrap"><img id="img" src=""></div>
    <div id="tagged-badge"></div>
  </div>
  <div id="meta"></div>
  <div id="buttons">
    <button class="nav" id="prev">&larr; Prev</button>
    <button class="blister" id="btn-blister">Blister pack (B)</button>
    <button class="packaging" id="btn-packaging">Outer packaging (P)</button>
    <button class="other" id="btn-other">Other (O)</button>
  </div>
  <input id="notes" type="text" placeholder="optional note, e.g. 'loose pills', 'syrup bottle', 'sachet', 'box+blister both visible' -- press Enter to save without changing tag">
  <div id="keys">
    Keyboard: <b>B</b> = blister pack &amp; next &middot; <b>P</b> = outer packaging &amp; next &middot;
    <b>O</b> = other &amp; next (use the note field for what kind: loose pills / syrup / sachet / box+blister combo / unclear)
    &middot; <b>&larr;</b> = back.
    Progress auto-saves to this browser. Click "Export CSV" any time.
  </div>
</div>

<script>
const IMAGES = {images_json};
const STORAGE_KEY = "pharmavision_modality_tags_v1";

let state = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{{}}");
let idx = state._idx || 0;

function save() {{
  state._idx = idx;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}}

function render() {{
  const im = IMAGES[idx];
  document.getElementById("img").src = im.path;
  document.getElementById("meta").innerHTML =
    `#${{idx+1}} / ${{IMAGES.length}} &mdash; <span class="label">${{im.id}}</span> &mdash; class: ${{im.label}}`;
  const tag = state[im.id];
  const badge = document.getElementById("tagged-badge");
  if (tag) {{
    badge.textContent = tag.modality;
    badge.style.background = {{blister:"#1a6fa8", packaging:"#2d6a2d", other:"#8a4a1f"}}[tag.modality];
    badge.style.display = "inline-block";
  }} else {{
    badge.style.display = "none";
  }}
  document.getElementById("notes").value = (tag && tag.notes) || "";
  const done = IMAGES.filter(x => state[x.id]).length;
  document.getElementById("progress").textContent = `${{done}} / ${{IMAGES.length}} tagged`;
  save();
}}

function tag(modality) {{
  const im = IMAGES[idx];
  const notes = document.getElementById("notes").value;
  state[im.id] = {{modality: modality, notes: notes}};
  if (idx < IMAGES.length - 1) idx++;
  render();
}}

function saveNoteOnly() {{
  const im = IMAGES[idx];
  const notes = document.getElementById("notes").value;
  const existing = state[im.id];
  if (existing) {{ state[im.id] = {{modality: existing.modality, notes: notes}}; render(); }}
}}

document.getElementById("btn-blister").onclick = () => tag("blister");
document.getElementById("btn-packaging").onclick = () => tag("packaging");
document.getElementById("btn-other").onclick = () => tag("other");
document.getElementById("prev").onclick = () => {{ if (idx > 0) idx--; render(); }};

document.addEventListener("keydown", (e) => {{
  if (document.activeElement.id === "notes") {{
    if (e.key === "Enter") {{ saveNoteOnly(); document.activeElement.blur(); }}
    return;
  }}
  if (e.key.toLowerCase() === "b") tag("blister");
  else if (e.key.toLowerCase() === "p") tag("packaging");
  else if (e.key.toLowerCase() === "o") tag("other");
  else if (e.key === "ArrowLeft") {{ if (idx > 0) idx--; render(); }}
}});

document.getElementById("export").onclick = () => {{
  let csv = "image_id,orig_relpath,class_label,modality,notes\\n";
  for (const im of IMAGES) {{
    const t = state[im.id];
    const modality = t ? t.modality : "";
    const notes = t ? (t.notes || "").replace(/"/g, '""') : "";
    csv += `${{im.id}},"${{im.path}}",${{im.label}},${{modality}},"${{notes}}"\\n`;
  }}
  const blob = new Blob([csv], {{type: "text/csv"}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "manual_modality_tags.csv";
  a.click();
}};

render();
</script>
</body>
</html>
"""
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_HTML}")
    print(f"{len(images)} images loaded (current cleaned Kaggle pool).")
    print("Open it directly in a browser to start tagging.")


if __name__ == "__main__":
    main()

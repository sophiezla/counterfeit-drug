"""
Step 9 — Build a self-contained local HTML tool for manually tagging the
564-image Kaggle modeling pool: watermark/stock-photo overlay, screenshot/
non-medicine image, or unsure. Designed to be fast (keyboard-driven,
auto-advance, auto-save) and to integrate directly with the existing
pipeline — its CSV export is consumed by
scripts/10_apply_manual_watermark_review.py, which adds new exclusions to
02_filter.py's pattern and re-runs the pipeline.

Pre-seeds the 11 watermark cases and other anomalies already found during
the earlier AI-assisted contact-sheet pass (data/metadata/
modality_review_findings.md) as *suggestions* -- shown with a distinct
badge so they can be confirmed or overridden, not re-discovered from
scratch, but the reviewer should not feel bound by them.

Output: data/metadata/manual_review_tool.html
  Open it directly in a browser (double-click, or `start` the file) --
  no server needed. Images load via relative file:// paths from
  data/raw/. Progress auto-saves to the browser's localStorage keyed by
  page URL, so closing and reopening the file resumes where you left off.
  Click "Export CSV" any time (including partway through) to download
  data/metadata/manual_watermark_review.csv with progress so far.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROVENANCE = ROOT / "data" / "metadata" / "provenance.csv"
OUT_HTML = ROOT / "data" / "metadata" / "manual_review_tool.html"

# From data/metadata/modality_review_findings.md -- shown as suggestions only.
AI_SUGGESTIONS = {
    "kaggle_fake_real_medicine_00291": ("watermark", 'AI pass: "alamy stock photo" watermark'),
    "kaggle_fake_real_medicine_00332": ("watermark", 'AI pass: "Generic India" watermark'),
    "kaggle_fake_real_medicine_00356": ("watermark", 'AI pass: "Generic India" watermark'),
    "kaggle_fake_real_medicine_00442": ("watermark", "AI pass: faint site-url-style overlay"),
    "kaggle_fake_real_medicine_00444": ("watermark", "AI pass: faint overlay, partially legible"),
    "kaggle_fake_real_medicine_00476": ("watermark", "AI pass: large diagonal stock-photo watermark"),
    "kaggle_fake_real_medicine_00493": ("watermark", 'AI pass: "medicaldawa.in" watermark'),
    "kaggle_fake_real_medicine_00517": ("watermark", 'AI pass: "medicaldawa.in" watermark'),
    "kaggle_fake_real_medicine_00538": ("unsure", "AI pass: no text watermark, but patterned-cloth photo backdrop (Grad-CAM attended to it, see modeling/README.md)"),
    "kaggle_fake_real_medicine_00547": ("watermark", "AI pass: partial overlay, likely stock-photo mark"),
    "kaggle_fake_real_medicine_00558": ("watermark", '"Wellness Forever" logo/watermark'),
    "kaggle_fake_real_medicine_00164": ("unsure", "AI pass: loose pills, no packaging visible (modality, not watermark, issue)"),
    "kaggle_fake_real_medicine_00378": ("unsure", "AI pass: loose pills, no packaging visible (modality, not watermark, issue)"),
}


def main():
    with open(PROVENANCE, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["source_dataset"] == "Kaggle - Fake vs Real Medicine"]
    rows.sort(key=lambda r: r["image_id"])

    images = []
    for r in rows:
        rel = r["orig_relpath"].replace("\\", "/")
        suggestion = AI_SUGGESTIONS.get(r["image_id"])
        images.append({
            "id": r["image_id"],
            "path": f"../raw/{rel}",
            "label": r["class_label"],
            "aiFlag": suggestion[0] if suggestion else "",
            "aiNote": suggestion[1] if suggestion else "",
        })

    images_json = json.dumps(images)

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>PharmaChecked v2 -- manual image review</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, sans-serif; margin: 0; background: #1e1e1e; color: #eee; }}
  #bar {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 20px; background: #111; position: sticky; top: 0; }}
  #progress {{ font-size: 14px; color: #aaa; }}
  #main {{ display: flex; flex-direction: column; align-items: center; padding: 20px; }}
  #imgwrap {{ background: #333; padding: 10px; border-radius: 8px; }}
  #img {{ max-width: 560px; max-height: 560px; display: block; }}
  #meta {{ margin-top: 10px; font-size: 14px; color: #ccc; text-align: center; }}
  #meta .label {{ font-weight: bold; }}
  #ai {{ margin-top: 6px; font-size: 13px; padding: 6px 10px; border-radius: 4px; }}
  #ai.watermark {{ background: #5a3d00; color: #ffd479; }}
  #ai.unsure {{ background: #3d3d00; color: #ffff9e; }}
  #ai.none {{ display: none; }}
  #buttons {{ margin-top: 18px; display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }}
  button {{ font-size: 15px; padding: 10px 16px; border-radius: 6px; border: none; cursor: pointer; color: white; }}
  .clean {{ background: #2d6a2d; }}
  .watermark {{ background: #a8710a; }}
  .screenshot {{ background: #a83232; }}
  .unsure {{ background: #6b6b1f; }}
  .nav {{ background: #444; }}
  button:hover {{ filter: brightness(1.2); }}
  #notes {{ margin-top: 10px; width: 400px; max-width: 90vw; padding: 6px; border-radius: 4px; border: 1px solid #555; background: #222; color: #eee; }}
  #tagged-badge {{ position: absolute; top: -10px; right: -10px; font-size: 12px; padding: 3px 8px; border-radius: 10px; }}
  #keys {{ margin-top: 14px; font-size: 12px; color: #888; text-align: center; max-width: 560px; }}
  #export {{ background: #1a5fb4; }}
  #jumplist {{ margin-top: 20px; font-size: 12px; color: #888; }}
</style>
</head>
<body>

<div id="bar">
  <div>PharmaChecked v2 -- manual image review (Kaggle pool)</div>
  <div id="progress"></div>
  <button id="export">Export CSV</button>
</div>

<div id="main">
  <div style="position: relative;">
    <div id="imgwrap"><img id="img" src=""></div>
    <div id="tagged-badge"></div>
  </div>
  <div id="meta"></div>
  <div id="ai"></div>
  <div id="buttons">
    <button class="nav" id="prev">&larr; Prev</button>
    <button class="clean" id="btn-clean">Clean (Space/&rarr;)</button>
    <button class="watermark" id="btn-watermark">Watermark (W)</button>
    <button class="screenshot" id="btn-screenshot">Screenshot / not medicine (S)</button>
    <button class="unsure" id="btn-unsure">Unsure (U)</button>
  </div>
  <input id="notes" type="text" placeholder="optional note (press Enter to save note without changing tag)">
  <div id="keys">
    Keyboard: <b>Space</b> or <b>&rarr;</b> = clean &amp; next &middot; <b>W</b> = watermark &amp; next &middot;
    <b>S</b> = screenshot/not-medicine &amp; next &middot; <b>U</b> = unsure &amp; next &middot; <b>&larr;</b> = back.
    Progress auto-saves to this browser. Click "Export CSV" any time.
  </div>
  <div id="jumplist"></div>
</div>

<script>
const IMAGES = {images_json};
const STORAGE_KEY = "pharmavision_manual_review_v1";

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
  const aiDiv = document.getElementById("ai");
  if (im.aiFlag) {{
    aiDiv.className = im.aiFlag;
    aiDiv.textContent = "Suggested: " + im.aiFlag.toUpperCase() + " -- " + im.aiNote;
  }} else {{
    aiDiv.className = "none";
    aiDiv.textContent = "";
  }}
  const tag = state[im.id];
  const badge = document.getElementById("tagged-badge");
  if (tag) {{
    badge.textContent = tag.flag;
    badge.style.background = {{clean:"#2d6a2d", watermark:"#a8710a", screenshot:"#a83232", unsure:"#6b6b1f"}}[tag.flag];
    badge.style.display = "inline-block";
  }} else {{
    badge.style.display = "none";
  }}
  document.getElementById("notes").value = (tag && tag.notes) || "";
  const done = IMAGES.filter(x => state[x.id]).length;
  document.getElementById("progress").textContent = `${{done}} / ${{IMAGES.length}} tagged`;
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
  state[im.id] = {{flag: existing ? existing.flag : "clean", notes: notes}};
  render();
}}

document.getElementById("btn-clean").onclick = () => tag("clean");
document.getElementById("btn-watermark").onclick = () => tag("watermark");
document.getElementById("btn-screenshot").onclick = () => tag("screenshot");
document.getElementById("btn-unsure").onclick = () => tag("unsure");
document.getElementById("prev").onclick = () => {{ if (idx > 0) idx--; render(); }};

document.addEventListener("keydown", (e) => {{
  if (document.activeElement.id === "notes") {{
    if (e.key === "Enter") {{ saveNoteOnly(); document.activeElement.blur(); }}
    return;
  }}
  if (e.key === " " || e.key === "ArrowRight") {{ e.preventDefault(); tag("clean"); }}
  else if (e.key.toLowerCase() === "w") tag("watermark");
  else if (e.key.toLowerCase() === "s") tag("screenshot");
  else if (e.key.toLowerCase() === "u") tag("unsure");
  else if (e.key === "ArrowLeft") {{ if (idx > 0) idx--; render(); }}
}});

document.getElementById("export").onclick = () => {{
  let csv = "image_id,orig_relpath,class_label,flag,notes,ai_suggested_flag\\n";
  for (const im of IMAGES) {{
    const t = state[im.id];
    const flag = t ? t.flag : "";
    const notes = t ? (t.notes || "").replace(/"/g, '""') : "";
    csv += `${{im.id}},"${{im.path}}",${{im.label}},${{flag}},"${{notes}}",${{im.aiFlag}}\\n`;
  }}
  const blob = new Blob([csv], {{type: "text/csv"}});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "manual_watermark_review.csv";
  a.click();
}};

render();
</script>
</body>
</html>
"""
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT_HTML}")
    print(f"{len(images)} images loaded, {len(AI_SUGGESTIONS)} pre-seeded with AI suggestions.")
    print(f"Open it directly in a browser to start reviewing.")


if __name__ == "__main__":
    main()

"""
Build a local HTML viewer for the Split E eligibility screen.

Why this exists. The screen that turns 202 regulatory-alert candidates into a
150-image Split E is a single pass by a single reviewer (see
data/metadata/split_e_findings.md, section 6, item 1), and that is the one
outstanding gate before Split E can be reported. This project's standard for
such a screen is a full human pass through a purpose-built local tool -- the
modality review used two of them (steps 09 and 11) -- so Split E gets the same
treatment rather than a weaker one.

The tool is a viewer first: every candidate at a readable size, the recorded
decision and reason beside it, filterable by decision, exclusion code, source
and flag. Adjudication is a second layer that costs one keystroke per image and
can be ignored entirely if all you want is to look. Agreeing with the recorded
call is the default for every image, so an untouched review exports as
"reviewer 2 agrees throughout" and a disagreement has to be entered
deliberately.

    python scripts/29_build_split_e_review_tool.py

Then open data/metadata/split_e_review_tool.html in a browser. No server is
needed; images load over relative file:// paths from data/raw. Progress
auto-saves to localStorage keyed to the file, so closing and reopening resumes.

Nothing about this tool sends an image anywhere. That is deliberate and not
incidental: 140 of the 150 Split E images are WHO-hosted and carry
`metadata_only_permission_required`, so they must not be uploaded to a hosted
page or published as an artifact. A local file:// viewer is the only form this
review can take without a rights problem.

Keys, one-handed:
    A / Enter   agree with the recorded decision, advance
    D           disagree -- flips include<->exclude for this image, advance
    N           add a note to the current image
    <- / ->     move without changing anything
    F           cycle the filter (all / included / excluded / disagreements)

Export writes data/metadata/split_e_review_adjudication.csv with one row per
image: the recorded decision, the second reviewer's verdict, and any note.
Re-run scripts/25 after applying any change to rebuild the provenance CSV.

Output: data/metadata/split_e_review_tool.html
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "data" / "metadata"
OUT = META / "split_e_review_tool.html"

REVIEWS = [META / "split_e_eligibility_review.csv",
           META / "split_e_harvest_eligibility_review.csv"]
LOGS = [(META / "split_e_download_log.csv", "image_id"),
        (META / "split_e_harvest_download_log.csv", "candidate_id")]
PROVENANCE = META / "split_e_candidate_provenance.csv"


def load_csv(path, key=None):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    return {r[key]: r for r in rows} if key else rows


def main():
    review = {}
    for p in REVIEWS:
        review.update(load_csv(p, key="image_id"))

    log = {}
    for path, key in LOGS:
        for iid, r in load_csv(path, key=key).items():
            if r.get("stored_relpath") and r.get("status", "kept") != "dropped":
                log[iid] = r

    prov = {r["image_id"].removeprefix("split_e_"): r for r in load_csv(PROVENANCE)}

    items = []
    for iid in sorted(review):
        if iid not in log:
            continue  # candidate whose bytes were dropped before the screen
        r, lg = review[iid], log[iid]
        p = prov.get(iid, {})
        items.append({
            "id": iid,
            # relative to data/metadata/, where this file is written
            "src": "../raw/" + lg["stored_relpath"],
            "decision": r["decision"],
            "code": r["exclusion_code"],
            "reason": r["reason"],
            "panel": r["panel_composite"] == "yes",
            "crop": r.get("label_crop") == "yes",
            "org": lg["source_organization"],
            "case": p.get("product_identity", ""),
            "alert": lg.get("alert_title", "") or lg.get("case_id", ""),
            "redist": (p.get("redistributable") or lg.get("redistributable")) == "True",
            "w": lg.get("width", ""), "h": lg.get("height", ""),
        })

    n_inc = sum(1 for i in items if i["decision"] == "include")
    html = TEMPLATE.replace("__DATA__", json.dumps(items))
    html = html.replace("__NINC__", str(n_inc))
    html = html.replace("__NEXC__", str(len(items) - n_inc))
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"  {len(items)} candidates: {n_inc} included, {len(items) - n_inc} excluded")
    print(f"  open it directly in a browser -- no server needed")


TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Split E eligibility review</title>
<style>
 :root{--bg:#12131a;--fg:#e8e8ee;--dim:#9a9ab0;--in:#2f9e5e;--ex:#c0392b;--edge:#2a2c38;}
 *{box-sizing:border-box}
 body{margin:0;background:var(--bg);color:var(--fg);
      font:14px/1.5 ui-sans-serif,system-ui,"Segoe UI",sans-serif}
 header{position:sticky;top:0;z-index:5;background:#0d0e14;border-bottom:1px solid var(--edge);
        padding:10px 16px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
 h1{font-size:15px;margin:0;font-weight:600;letter-spacing:.02em}
 .pill{padding:2px 9px;border-radius:99px;font-size:12px;border:1px solid var(--edge)}
 .in{color:var(--in);border-color:#1d5c39}.ex{color:var(--ex);border-color:#6d241c}
 button,select{background:#1c1e28;color:var(--fg);border:1px solid var(--edge);
        border-radius:6px;padding:5px 11px;font:inherit;font-size:13px;cursor:pointer}
 button:hover{background:#262936}
 #grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));
       gap:14px;padding:16px}
 .card{border:1px solid var(--edge);border-radius:9px;overflow:hidden;background:#171922;
       display:flex;flex-direction:column}
 .card.sel{outline:2px solid #4a7fd4;outline-offset:1px}
 .card.dis{border-color:#b8860b}
 .thumb{aspect-ratio:1;background:#0b0c11;display:flex;align-items:center;justify-content:center;
        cursor:zoom-in;overflow:hidden}
 .thumb img{max-width:100%;max-height:100%;object-fit:contain}
 .meta{padding:8px 10px;font-size:12px;border-top:1px solid var(--edge)}
 .idline{display:flex;justify-content:space-between;gap:8px;align-items:baseline}
 .id{font-family:ui-monospace,Consolas,monospace;font-size:11.5px}
 .code{color:var(--ex);font-size:11px;font-family:ui-monospace,monospace}
 .reason{color:var(--dim);font-size:11.5px;margin-top:4px;
         display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
 .flags{margin-top:5px;display:flex;gap:5px;flex-wrap:wrap}
 .flag{font-size:10px;padding:1px 6px;border-radius:99px;background:#232634;color:var(--dim)}
 .verdict{font-size:11px;margin-top:6px;color:#b8860b;font-weight:600}
 #lb{position:fixed;inset:0;background:rgba(6,7,10,.96);display:none;z-index:20;
     flex-direction:column;align-items:center;justify-content:center;padding:24px;gap:12px}
 #lb img{max-width:94vw;max-height:76vh;object-fit:contain}
 #lbmeta{max-width:900px;text-align:center;font-size:13px}
 #lbmeta .reason{-webkit-line-clamp:99;font-size:13px;margin-top:6px}
 kbd{background:#232634;border:1px solid var(--edge);border-radius:4px;padding:0 5px;font-size:11px}
 .hint{color:var(--dim);font-size:12px}
</style></head><body>
<header>
  <h1>Split E eligibility review</h1>
  <span class="pill in">__NINC__ included</span>
  <span class="pill ex">__NEXC__ excluded</span>
  <select id="filt">
    <option value="all">all candidates</option>
    <option value="include">included only</option>
    <option value="exclude">excluded only</option>
    <option value="dis">disagreements only</option>
    <option value="panel">panel composites</option>
    <option value="crop">label crops</option>
  </select>
  <select id="codefilt"><option value="">any exclusion code</option></select>
  <span class="pill" id="prog">0 adjudicated</span>
  <button id="exp">Export CSV</button>
  <button id="clr">Reset marks</button>
  <span class="hint"><kbd>click</kbd> zoom &middot; <kbd>A</kbd> agree &middot;
    <kbd>D</kbd> disagree &middot; <kbd>N</kbd> note &middot; <kbd>&larr;&rarr;</kbd> move</span>
</header>
<div id="grid"></div>
<div id="lb"><img id="lbimg" alt=""><div id="lbmeta"></div>
  <div class="hint"><kbd>A</kbd> agree &middot; <kbd>D</kbd> disagree &middot;
   <kbd>Esc</kbd> close &middot; <kbd>&larr;&rarr;</kbd> move</div></div>
<script>
const DATA = __DATA__;
const KEY = "split_e_review_v1";
let marks = {};
try { marks = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch(e) { marks = {}; }
let cur = 0, view = DATA.slice();

const $ = s => document.querySelector(s);
const grid = $("#grid"), lb = $("#lb");

const codes = [...new Set(DATA.filter(d=>d.code).map(d=>d.code))].sort();
codes.forEach(c => { const o=document.createElement("option"); o.value=o.textContent=c;
                     $("#codefilt").appendChild(o); });

function save(){ try{ localStorage.setItem(KEY, JSON.stringify(marks)); }catch(e){} render(); }
function verdictOf(d){ const m=marks[d.id]; return m ? m.verdict : ""; }
function effective(d){
  const v = verdictOf(d);
  if (v === "disagree") return d.decision === "include" ? "exclude" : "include";
  return d.decision;
}

function applyFilter(){
  const f=$("#filt").value, c=$("#codefilt").value;
  view = DATA.filter(d=>{
    if (c && d.code !== c) return false;
    if (f==="include") return d.decision==="include";
    if (f==="exclude") return d.decision==="exclude";
    if (f==="dis") return verdictOf(d)==="disagree";
    if (f==="panel") return d.panel;
    if (f==="crop") return d.crop;
    return true;
  });
  if (cur >= view.length) cur = Math.max(0, view.length-1);
  render();
}

function render(){
  grid.innerHTML = "";
  view.forEach((d,i)=>{
    const m = marks[d.id];
    const el = document.createElement("div");
    el.className = "card" + (i===cur?" sel":"") + (verdictOf(d)==="disagree"?" dis":"");
    const flags = [];
    if (d.panel) flags.push("panel");
    if (d.crop) flags.push("label crop");
    if (d.redist) flags.push("FDA public domain");
    flags.push(d.org);
    if (d.w) flags.push(d.w+"×"+d.h);
    el.innerHTML =
      '<div class="thumb"><img loading="lazy" src="'+d.src+'" alt=""></div>'+
      '<div class="meta"><div class="idline"><span class="id">'+d.id+'</span>'+
      '<span class="'+(d.decision==="include"?"in":"ex")+'" style="font-size:11px">'+
        d.decision+'</span></div>'+
      (d.code?'<div class="code">'+d.code+'</div>':'')+
      '<div class="reason">'+d.reason.replace(/</g,"&lt;")+'</div>'+
      '<div class="flags">'+flags.map(f=>'<span class="flag">'+f+'</span>').join("")+'</div>'+
      (m && m.verdict ? '<div class="verdict">reviewer 2: '+m.verdict+
         (m.note?" — "+m.note.replace(/</g,"&lt;"):"")+
         (m.verdict==="disagree"?" → "+effective(d):"")+'</div>' : '')+
      '</div>';
    el.querySelector(".thumb").onclick = e => { e.stopPropagation(); cur=i; openLb(); };
    el.onclick = () => { cur=i; render(); };
    grid.appendChild(el);
  });
  const n = Object.values(marks).filter(m=>m.verdict).length;
  const dis = Object.values(marks).filter(m=>m.verdict==="disagree").length;
  $("#prog").textContent = n+" of "+DATA.length+" adjudicated · "+dis+" disagreements";
  const sel = grid.children[cur];
  if (sel) sel.scrollIntoView({block:"nearest"});
}

function openLb(){
  const d = view[cur]; if(!d) return;
  $("#lbimg").src = d.src;
  $("#lbmeta").innerHTML =
    '<div class="id">'+d.id+' · '+d.org+' · '+d.case+'</div>'+
    '<div class="'+(d.decision==="include"?"in":"ex")+'">'+d.decision+
      (d.code?" · "+d.code:"")+'</div>'+
    '<div class="reason">'+d.reason.replace(/</g,"&lt;")+'</div>'+
    (d.alert?'<div class="hint" style="margin-top:6px">'+
       d.alert.replace(/</g,"&lt;")+'</div>':'');
  lb.style.display = "flex";
}
function closeLb(){ lb.style.display="none"; }
lb.onclick = e => { if(e.target===lb) closeLb(); };

function mark(verdict){
  const d = view[cur]; if(!d) return;
  marks[d.id] = Object.assign({}, marks[d.id], {verdict});
  if (cur < view.length-1) cur++;
  save();
  if (lb.style.display==="flex") openLb();
}

document.onkeydown = e => {
  if (e.target.tagName === "SELECT") return;
  const k = e.key.toLowerCase();
  if (k === "escape") return closeLb();
  if (k === "a" || e.key === "Enter") { e.preventDefault(); mark("agree"); }
  else if (k === "d") { e.preventDefault(); mark("disagree"); }
  else if (k === "n") { e.preventDefault();
    const d = view[cur]; if(!d) return;
    const note = prompt("Note for "+d.id+":", (marks[d.id]||{}).note || "");
    if (note !== null) { marks[d.id] = Object.assign({verdict:"agree"}, marks[d.id], {note}); save(); } }
  else if (e.key === "ArrowRight") { e.preventDefault();
    if(cur<view.length-1){cur++; render(); if(lb.style.display==="flex") openLb();} }
  else if (e.key === "ArrowLeft") { e.preventDefault();
    if(cur>0){cur--; render(); if(lb.style.display==="flex") openLb();} }
  else if (k === "f") { const s=$("#filt");
    s.selectedIndex=(s.selectedIndex+1)%s.options.length; applyFilter(); }
};

$("#filt").onchange = applyFilter;
$("#codefilt").onchange = applyFilter;
$("#clr").onclick = () => { if(confirm("Clear all reviewer-2 marks?")){ marks={}; save(); } };
$("#exp").onclick = () => {
  const rows = [["image_id","recorded_decision","exclusion_code","reviewer2_verdict",
                 "effective_decision","note"]];
  DATA.forEach(d => { const m = marks[d.id] || {};
    rows.push([d.id, d.decision, d.code, m.verdict || "",
               m.verdict ? effective(d) : d.decision, (m.note||"").replace(/"/g,'""')]); });
  const csv = rows.map(r => r.map(c => '"'+String(c)+'"').join(",")).join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], {type:"text/csv"}));
  a.download = "split_e_review_adjudication.csv"; a.click();
};

applyFilter();
</script></body></html>
"""


if __name__ == "__main__":
    main()

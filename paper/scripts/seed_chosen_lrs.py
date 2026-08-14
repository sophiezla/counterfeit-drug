"""
Seed modeling/results/chosen_lrs.json from the existing training logs.

The training scripts now record the selected learning rate themselves
(result_io.save_chosen_lr), but the models of record were trained before that
change, so the record has to be back-filled once from the logs those runs
produced. Parsed rather than typed by hand, so the value is traceable to the
run that actually used it.

Run once; afterwards the training scripts keep the file current.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "modeling" / "results"
OUT = RES / "chosen_lrs.json"

# The normalised retrain is the run of record for Models 2-4 (see
# modeling/README.md "Update 5/6"); its logs carry the "_normalized" suffix.
LOGS = {
    "model2_smallcnn_gap": "model2_train_log_normalized.txt",
    "model3_mobilenetv3small_frozen": "model3_train_log_normalized.txt",
    "model4_efficientnetb0_frozen": "model4_train_log_normalized.txt",
}

data = {}
for model, log in LOGS.items():
    text = (RES / log).read_text(encoding="utf-8", errors="replace")
    hits = re.findall(r"selected lr=([0-9.eE+-]+)", text)
    if not hits:
        hits = re.findall(r"using cached lr=([0-9.eE+-]+)", text)
    if not hits:
        sys.exit(f"no learning rate found in {log}")
    if len(set(hits)) != 1:
        sys.exit(f"{log} reports more than one selected lr: {sorted(set(hits))}")
    data[model] = float(hits[0])
    print(f"{model}: lr={data[model]}  (from {log})")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, sort_keys=True)
    f.write("\n")
print(f"wrote {OUT.relative_to(ROOT)}")

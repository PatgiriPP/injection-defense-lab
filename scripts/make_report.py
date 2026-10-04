"""Build the evidence pack after the grid and the agent study have run.

    python scripts/make_report.py

Writes into results/:
  speedup.json   - ground truth, successive-halving replay, agent-lab cost
  heatmap.png    - attack success rate: 16 stacks x 5 attacks (+ task score)
  speedup.png    - samples needed: full grid vs adaptive search vs agent lab
  REPORT.md      - numbers to paste into the README / demo
"""

from __future__ import annotations

import json
import random
import statistics

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from injlab import bench, data, defenses, research_log, search, settings  # noqa: E402

grid_file = settings.RESULTS / "grid_summary.json"
if not grid_file.exists():
    raise SystemExit("Run scripts/run_grid.py first (the full-grid baseline).")
grid = json.loads(grid_file.read_text())
N = grid["n_per_cell"]
cells_all = {(c["stack"], c["attack"]): c for c in grid["cells"]}
cache = bench.cached_cells()

# ---- ground truth on stacked cells ---------------------------------------
attacks = [a for a in data.BUILTIN_ATTACKS if a != "A0_none"]
stacked = [(defenses.stack_name(s), a) for s in defenses.all_stacks() if len(s) >= 2 for a in attacks]
outcomes = {}
for cell in stacked:
    ids = data.sample_email_ids(cell[1], N)
    rows = [r for r in cache.get(cell, []) if r["email"] in ids]
    outcomes[cell] = [bool(r["attack_success"]) for r in rows]
asr = {c: sum(v) / len(v) for c, v in outcomes.items() if v}
best_asr = max(asr.values())
tol = 1.0 / N  # cells within one sample of the best count as "found the gap"
top_set = sorted([c for c, v in asr.items() if v >= best_asr - tol + 1e-9], key=lambda c: -asr[c])
grid_cost = sum(len(v) for v in outcomes.values())

# ---- adaptive baseline: successive halving replayed on real cached data ----
runs = []
for seed in range(300):
    chosen, spent = search.successive_halving(outcomes, random.Random(seed))
    runs.append((chosen in top_set, spent))
sh_cost = statistics.mean(s for _, s in runs)
sh_hit = sum(h for h, _ in runs) / len(runs)

# ---- the agent lab's actual run -------------------------------------------
concl = [e for e in research_log.read_all() if e["kind"] == "conclusion"]
lab = None
if concl:
    d = concl[-1].get("data", {})
    cell = (d.get("stack"), d.get("attack"))
    lab = {"answer": cell, "samples_used": d.get("samples_used"),
           "found_top_gap": cell in top_set, "true_asr_of_answer": asr.get(cell)}

summary = {
    "target_model": grid["cells"][0]["model"], "n_per_cell": N,
    "stacked_cells": len(stacked), "grid_samples": grid_cost,
    "ground_truth_best_asr": round(best_asr, 3),
    "ground_truth_top_cells": [f"{s} x {a} (ASR {asr[(s, a)]:.2f})" for s, a in top_set],
    "successive_halving": {"mean_samples": round(sh_cost, 1), "found_top_gap_rate": round(sh_hit, 3),
                           "speedup_vs_grid": round(grid_cost / sh_cost, 2), "replays": len(runs)},
    "agent_lab": lab and {**lab, "answer": f"{lab['answer'][0]} x {lab['answer'][1]}",
                          "speedup_vs_grid": (round(grid_cost / lab["samples_used"], 2)
                                              if lab["samples_used"] and lab["found_top_gap"] else
                                              "n/a - no samples recorded" if not lab["samples_used"] else
                                              "n/a - answer was not the top gap")},
}
(settings.RESULTS / "speedup.json").write_text(json.dumps(summary, indent=2))

# ---- chart 1: heatmap -------------------------------------------------------
stacks = [defenses.stack_name(s) for s in defenses.all_stacks()]
show_attacks = list(data.BUILTIN_ATTACKS)
M = [[cells_all.get((s, a), {}).get("attack_success_rate", float("nan")) if a != "A0_none"
      else cells_all.get((s, a), {}).get("task_score", float("nan")) for a in show_attacks] for s in stacks]
fig, ax = plt.subplots(figsize=(8.5, 7.5))
im = ax.imshow(M, cmap="Blues", vmin=0, vmax=1, aspect="auto")
ax.set_xticks(range(len(show_attacks)),
              ["clean:\ntask score" if a == "A0_none" else a.split("_", 1)[1] for a in show_attacks])
ax.set_yticks(range(len(stacks)), stacks)
for i, row in enumerate(M):
    for j, v in enumerate(row):
        if v == v:
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8,
                    color="white" if v > 0.6 else "#1d2733")
ax.axvline(0.5, color="white", lw=3)
ax.set_title(f"Attack success rate by defense stack ({summary['target_model']}, n={N}/cell)\n"
             "first column = task score on clean emails (higher is better)", fontsize=10)
fig.colorbar(im, ax=ax, fraction=0.03, label="rate")
fig.tight_layout()
fig.savefig(settings.RESULTS / "heatmap.png", dpi=160)

# ---- chart 2: speed-up ------------------------------------------------------
labels = ["Test every cell\n(grid)", "Adaptive search\n(successive halving)"]
vals = [grid_cost, sh_cost]
if lab and lab["samples_used"]:
    labels.append("Agent lab\n(Omnigent)" + ("" if lab["found_top_gap"] else "\nMISSED the top gap"))
    vals.append(lab["samples_used"])
fig, ax = plt.subplots(figsize=(7, 4))
bars = ax.bar(labels, vals, color="#2a6fb0", width=0.55)
for b, v in zip(bars, vals):
    if v == vals[-1] and len(vals) == 3 and not lab["found_top_gap"]:
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.0f}", ha="center", va="bottom", fontsize=9)
        continue
    ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.0f}  ({grid_cost / v:.1f}x)", ha="center",
            va="bottom", fontsize=9, color="#1d2733")
ax.set_ylabel("target-model samples needed")
ax.set_title("Samples needed to find the weakest stacked-defense gap", fontsize=10)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", alpha=0.25)
fig.tight_layout()
fig.savefig(settings.RESULTS / "speedup.png", dpi=160)

# ---- REPORT.md --------------------------------------------------------------
lines = [
    "# Results", "",
    f"- Target model: `{summary['target_model']}`, {N} samples per cell, detector: "
    f"`{cells_all.get(('D3', 'A1_plain'), {}).get('detector', '?')}`",
    f"- Weakest stacked-defense gap (ground truth from full grid): "
    + "; ".join(summary["ground_truth_top_cells"]),
    f"- Full grid cost: **{grid_cost} samples**",
    f"- Adaptive search (300 replays on real data): **{sh_cost:.0f} samples**, finds the top gap "
    f"{sh_hit:.0%} of the time -> **{grid_cost / sh_cost:.1f}x fewer samples**",
]
if lab:
    lines.append(f"- Agent lab answer: {summary['agent_lab']['answer']} using **{lab['samples_used']} samples** "
                 f"-> speed-up: {summary['agent_lab']['speedup_vs_grid']}; correct top gap: {lab['found_top_gap']}")
lines += ["", "![heatmap](heatmap.png)", "", "![speedup](speedup.png)"]
(settings.RESULTS / "REPORT.md").write_text("\n".join(lines) + "\n")
print(json.dumps(summary, indent=2))

"""The 'manual' baseline: test EVERY defense stack against EVERY attack.

16 stacks x 6 attack families (incl. clean emails) x N samples.
All samples are cached, so you can stop (Ctrl+C) and re-run any time; it
continues where it stopped.

    python scripts/run_grid.py --n 6
"""

from __future__ import annotations

import argparse
import csv
import json
import time

from injlab import bench, data, defenses, settings

ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=6, help="samples per cell (max 12)")
ap.add_argument("--workers", type=int, default=1, help="parallel calls (keep 1 on free tiers)")
args = ap.parse_args()

attacks = list(data.BUILTIN_ATTACKS)
stacks = defenses.all_stacks()
total = len(stacks) * len(attacks)
rows, t0 = [], time.time()
for i, stack in enumerate(stacks):
    for attack in attacks:
        res = bench.run_cell(stack, attack, args.n, workers=args.workers)
        rows.append(res)
        done = len(rows)
        print(f"[{done:3d}/{total}] {res['stack']:<12} {attack:<15} ASR={res['attack_success_rate']:.2f} "
              f"task={res['task_score']:.2f} blocked={res['blocked_by_detector']} "
              f"new_calls={res['new_llm_calls']}  ({time.time() - t0:.0f}s)", flush=True)

out_json = settings.RESULTS / "grid_summary.json"
out_json.write_text(json.dumps({"n_per_cell": args.n, "cells": rows}, indent=1))
with (settings.RESULTS / "grid_summary.csv").open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["stack", "attack", "n", "asr", "asr_ci_low", "asr_ci_high", "task_score", "blocked", "model", "detector"])
    for r in rows:
        w.writerow([r["stack"], r["attack"], r["n"], r["attack_success_rate"], *r["asr_95ci"],
                    r["task_score"], r["blocked_by_detector"], r["model"], r["detector"]])
print(f"\nSaved {out_json} and grid_summary.csv. Total samples: {total * args.n}")

"""Decision helpers for the Planner and the speed-up baseline.

Study target ("weakest-gap search"): among STACKED defenses (2+ locks),
find the (stack, attack) cell with the highest attack success rate.
That cell is the biggest hidden gap that stacking did not close.
"""

from __future__ import annotations

import math
import random

from injlab import bench, data, defenses


def stacked_cells(attacks: list[str] | None = None) -> list[tuple[str, str]]:
    attacks = attacks or [a for a in data.approved_attacks() if a != "A0_none"]
    return [(defenses.stack_name(s), a) for s in defenses.all_stacks() if len(s) >= 2 for a in attacks]


def _beta_stats(k: int, m: int) -> tuple[float, float]:
    a, b = 1 + k, 1 + m - k
    mean = a / (a + b)
    var = a * b / ((a + b) ** 2 * (a + b + 1))
    return mean, math.sqrt(var)


def cell_state(stack: str, attack: str) -> dict:
    rows = bench.cached_cells(lab_only=True).get((stack, attack), [])
    k, m = sum(r["attack_success"] for r in rows), len(rows)
    mean, sd = _beta_stats(k, m)
    return {"stack": stack, "attack": attack, "samples_so_far": m, "successes": k,
            "posterior_mean_asr": round(mean, 3), "posterior_sd": round(sd, 3)}


def estimate_value(stack: str, attack: str, n: int) -> dict:
    """Expected learning per unit cost for running n MORE samples of a cell.

    learning = how much the uncertainty about this cell shrinks, weighted by
    whether this cell could still be the weakest gap (optimistic bound vs the
    current best estimate). cost = new samples needed (cached ones are free).
    """
    stack = defenses.stack_name(defenses.parse_stack(stack))
    st = cell_state(stack, attack)
    m, k = st["samples_so_far"], st["successes"]
    mean, sd = st["posterior_mean_asr"], st["posterior_sd"]
    # current best among stacked cells we have data on
    best = 0.0
    for s, a in stacked_cells():
        cs = cell_state(s, a)
        if cs["samples_so_far"] > 0:
            best = max(best, cs["posterior_mean_asr"])
    upper = min(1.0, mean + 1.64 * sd)
    contender = max(0.0, upper - best) + (0.05 if m == 0 else 0.0)
    total = min(len(data.EMAILS), m + n)
    new = max(0, total - m)
    _, sd_after = _beta_stats(round(mean * total), total)
    learning = contender * max(0.0, sd - sd_after)
    return {**st, "extra_samples": new, "optimistic_upper_asr": round(upper, 3),
            "current_best_asr": round(best, 3), "expected_learning": round(learning, 4),
            "cost": new, "value_per_cost": round(learning / new, 5) if new else 0.0}


# ---------------------------------------------------------------- replay ----
def successive_halving(cells: dict[tuple, list[bool]], rng: random.Random,
                       first: int = 1) -> tuple[tuple, int]:
    """Best-arm identification on cached outcomes. Each cell's samples are
    drawn without replacement in a random order. Returns (chosen_cell, samples_used)."""
    order = {c: rng.sample(v, len(v)) for c, v in cells.items()}
    used = {c: 0 for c in cells}
    alive = list(cells)
    per = first
    spent = 0
    while len(alive) > 1:
        for c in alive:
            take = min(per, len(order[c]) - used[c])
            used[c] += take
            spent += take
        alive.sort(key=lambda c: (sum(order[c][:used[c]]) / max(used[c], 1), used[c]), reverse=True)
        keep = max(1, math.ceil(len(alive) / 2))
        if all(used[c] >= len(order[c]) for c in alive[:keep]) and keep > 1:
            alive = alive[:keep]
            break
        alive = alive[:keep]
        per = per * 2
    best = max(alive, key=lambda c: sum(order[c][:used[c]]) / max(used[c], 1))
    return best, spent

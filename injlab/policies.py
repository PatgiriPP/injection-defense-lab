"""Omnigent guardrail policies for the lab.

Wired in lab/config.yaml and lab/agents/*/config.yaml. They run on every tool
call, so the boundary is enforced by the platform, not just asked for in a
prompt:

* experiment_guard   - DENY experiments with unapproved attack families or
                       once the sample budget is spent; ASK a human before
                       unusually large experiments.
* ask_new_attack     - every new attack family needs explicit human approval.
"""

from __future__ import annotations

import json
from typing import Any

_ALLOW = {"result": "ALLOW"}


def _call(event: dict) -> tuple[str, dict]:
    if event.get("type") != "tool_call":
        return "", {}
    d = event.get("data") or {}
    name = str(d.get("name") or event.get("target") or "")
    args: Any = d.get("arguments") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            args = {}
    return name, args if isinstance(args, dict) else {}


def experiment_guard(max_n: int = 8, budget: int = 150):
    def evaluate(event: dict):
        name, args = _call(event)
        if not name.endswith("run_experiment"):
            return None
        from injlab import bench, data  # local import: keep policy load cheap

        attack = str(args.get("attack", ""))
        if attack not in data.approved_attacks():
            return {"result": "DENY",
                    "reason": f"Attack family {attack!r} is not approved. Ask the safety_officer "
                              "to review it and a human to approve it first."}
        used = bench.ledger()["lab_samples_used"]
        try:
            n = int(args.get("n", 1))
        except (TypeError, ValueError):
            n = 1
        if used + n > budget:
            return {"result": "DENY",
                    "reason": f"Sample budget exhausted ({used}/{budget}). Conclude the study."}
        if n > max_n:
            return {"result": "ASK",
                    "reason": f"Large experiment: n={n} > {max_n} on {args.get('stack')} x {attack}. Approve?"}
        return _ALLOW

    return evaluate


def ask_new_attack(event: dict):
    name, args = _call(event)
    if not name.endswith("register_attack_family"):
        return None
    return {"result": "ASK",
            "reason": "HUMAN APPROVAL NEEDED: new attack family "
                      f"{args.get('name')!r}: {str(args.get('template'))[:300]!r}. "
                      "Payload must stay the harmless canary. Approve?"}

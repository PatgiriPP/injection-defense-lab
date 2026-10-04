"""Shared research log: every hypothesis, plan, approval, result and decision
is appended here so the whole study can be reconstructed afterwards."""

from __future__ import annotations

import json
import time

from injlab import settings

KINDS = {"question", "literature", "hypothesis", "plan", "safety", "result",
         "analysis", "decision", "conclusion", "note"}


def append(agent: str, kind: str, content: str, data: dict | None = None) -> dict:
    kind = kind if kind in KINDS else "note"
    entries = read_all()
    entry = {"id": len(entries) + 1, "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
             "agent": agent, "kind": kind, "content": content.strip()[:2000]}
    if data:
        entry["data"] = data
    with settings.LOG_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def read_all() -> list[dict]:
    if not settings.LOG_FILE.exists():
        return []
    return [json.loads(l) for l in settings.LOG_FILE.read_text().splitlines() if l.strip()]


def render(last: int = 15) -> str:
    rows = read_all()[-last:]
    if not rows:
        return "(research log is empty)"
    return "\n".join(f"#{r['id']} [{r['kind']}] {r['agent']}: {r['content']}" for r in rows)

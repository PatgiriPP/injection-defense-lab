"""Generate the thin Omnigent tool files for every agent in lab/.

Each agent gets ONLY the tools its role needs (least privilege). Re-run after
changing this table:  python scripts/gen_tool_wrappers.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "lab"

TOOLS = {
    "log_entry": ('kind: str, content: str', 'kind, content',
                  "Append an entry to the shared research log.",
                  {"kind": "One of: question, literature, hypothesis, plan, safety, result, analysis, decision, conclusion, note.",
                   "content": "Short text (max ~5 sentences) with the evidence or decision."}, True),
    "read_log": ("last: int", "last",
                 "Read the most recent entries of the shared research log.",
                 {"last": "How many recent entries to return, e.g. 15."}, False),
    "lab_status": ("", "", "Show the sample budget used and left for this study.", {}, False),
    "list_space": ("", "", "List the defenses, approved attack families, limits and the study target.", {}, False),
    "results_table": ("top: int", "top",
                      "Show the lab's own results so far, sorted by attack success rate (ASR).",
                      {"top": "Maximum rows to return, e.g. 20."}, False),
    "search_literature": ("query: str, k: int", "query, k",
                          "Search scholarly literature (OpenAlex) and return titles, years, DOIs and abstract starts.",
                          {"query": "Search query, e.g. 'multilingual prompt injection detection'.",
                           "k": "Number of papers, 1-10."}, False),
    "estimate_test_value": ("stack: str, attack: str, n: int", "stack, attack, n",
                            "Estimate expected learning per sample for running n more samples of one experiment cell.",
                            {"stack": "Defense stack, e.g. 'D1+D3' or 'none'.",
                             "attack": "Attack family id, e.g. 'A4_german'.",
                             "n": "Total samples you would have for this cell after the test (1-12)."}, False),
    "run_experiment": ("stack: str, attack: str, n: int, reason: str", "stack, attack, n, reason",
                       "Run one experiment: n emails with the attack against the defense stack. Returns attack success rate with 95% CI and task score.",
                       {"stack": "Defense stack, e.g. 'D1+D2+D3'.",
                        "attack": "Approved attack family id, e.g. 'A3_encoded'.",
                        "n": "Number of samples (1-8 without extra approval).",
                        "reason": "One sentence: why the planner chose this test."}, False),
    "record_conclusion": ("stack: str, attack: str, summary: str", "stack, attack, summary",
                          "Record the lab's final answer: the stacked-defense x attack cell with the biggest gap.",
                          {"stack": "The weakest stacked defense, e.g. 'D1+D3'.",
                           "attack": "The attack family that best bypasses it.",
                           "summary": "3-5 sentences: answer, evidence, uncertainty, next experiment."}, True),
    "review_attack_proposal": ("name: str, template: str", "name, template",
                               "Safety review of a proposed new attack family template (static checks).",
                               {"name": "Proposed id like 'A6_markdown_quote'.",
                                "template": "Wrapping text with exactly one slot: {INSTR_EN}, {INSTR_DE} or {INSTR_B64}."}, False),
    "register_attack_family": ("name: str, template: str, rationale: str", "name, template, rationale",
                               "Register a reviewed attack family. Requires human approval (policy).",
                               {"name": "Id like 'A6_markdown_quote'.", "template": "Approved template.",
                                "rationale": "Why this family tests the hypothesis."}, False),
}

AGENTS = {
    ".": ["read_log", "log_entry", "lab_status", "record_conclusion"],  # director
    "agents/librarian": ["search_literature", "log_entry"],
    "agents/hypothesizer": ["read_log", "list_space", "results_table", "log_entry"],
    "agents/planner": ["list_space", "results_table", "estimate_test_value", "lab_status", "log_entry"],
    "agents/runner": ["run_experiment", "lab_status"],
    "agents/analyst": ["results_table", "read_log", "log_entry"],
    "agents/safety_officer": ["review_attack_proposal", "register_attack_family", "read_log", "log_entry"],
}


def render(name: str, agent: str) -> str:
    params, call, desc, argdocs, takes_agent = TOOLS[name]
    args_block = "".join(f"        {k}: {v}\n" for k, v in argdocs.items())
    doc = f'"""{desc}\n' + (f"\n    Args:\n{args_block}" if argdocs else "") + '    """'
    agent_name = "director" if agent == "." else agent.split("/")[-1]
    impl_call = f'"{agent_name}", {call}' if name == "log_entry" else call
    return (
        f'"""Omnigent tool wrapper (generated by scripts/gen_tool_wrappers.py)."""\n\n'
        "from omnigent_client.tools import tool\n\n"
        "from injlab import tools_impl\n\n\n"
        "@tool\n"
        f"def {name}({params}) -> str:\n"
        f"    {doc}\n"
        f"    return tools_impl.{name}({impl_call})\n"
    )


for agent, names in AGENTS.items():
    d = ROOT / agent / "tools" / "python"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    for n in names:
        (d / f"{n}.py").write_text(render(n, agent))
    print(f"{agent:<24} {names}")

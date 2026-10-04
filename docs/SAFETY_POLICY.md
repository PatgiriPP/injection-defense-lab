# Safety policy and human approval gates

This lab studies attacks on AI systems, so it is designed to produce *measurements*, not *exploits*.

## What the lab is allowed to do
* Run attacks only against a model we call ourselves, on synthetic emails written for this project.
* Use one payload only: a harmless canary instruction (reply with BANANA, a hyphen and 7731).
* Vary only the **wrapping** around that payload (language, encoding, framing).

## How it is enforced (platform, not prompt)
| Boundary | Mechanism | Effect |
|---|---|---|
| Only the Runner can run experiments | Tool permissions: `run_experiment` exists only in `lab/agents/runner` | Other agents cannot spend budget |
| Unapproved attack family | `injlab.policies.experiment_guard` → **DENY** | Tested in the offline wiring test (`A9_not_approved` denied) |
| Sample budget (default 150) | `experiment_guard` reads the ledger → **DENY** | Lab must conclude |
| Large experiments (n > 8) | `experiment_guard` → **ASK** | Human approves in the Omnigent REPL/UI |
| New attack family | `injlab.policies.ask_new_attack` → **ASK** on `register_attack_family` | Human sees the template before it exists |
| Template content | `review_attack_proposal`: exactly one payload slot; no links, emails, code, credentials or own payload | Rejected before a human is even asked |
| Runaway loops | `max_tool_calls_per_session` on every agent | Session stops |

## Labelled uncertainty
* Hypotheses are marked **AGENT-GENERATED HYPOTHESIS**.
* Every ASR is reported with n and a 95% Wilson interval.
* Every number traces to a row in `results/cache.jsonl` (prompt output, model, detector).

## What still needs validation before real-world use
Real (non-synthetic) documents, more target models, a real tool-using agent, and expert review of any
new attack family before publication. We do not publish working attacks beyond the canary.

# Agent specifications

Each agent owns one scientific decision. Inputs and outputs are structured and every step is written
to the shared research log (`results/research_log.jsonl`), so any decision can be reconstructed.

| Agent | Decision owned | Input | Output (logged as) | Tools |
|---|---|---|---|---|
| Lab Director | continue/stop; final answer | research question, sub-agent results | `question`, `decision`, `conclusion` | read_log, log_entry, lab_status, record_conclusion, sys_session_send |
| Librarian | relevant prior work | question | 3–5 papers with DOI + implication (`literature`) | search_literature, log_entry |
| Hypothesizer | next falsifiable hypothesis | log, search space, lab results | claim + reasoning + refutation criterion (`hypothesis`) | read_log, list_space, results_table, log_entry |
| Planner | which test to buy | hypothesis, lab results, budget | CHOSEN + REJECTED options with value scores (`plan`) | list_space, results_table, estimate_test_value, lab_status, log_entry |
| Runner | none (executes) | chosen (stack, attack, n, reason) | ASR, 95% CI, task score, budget left (`result`, auto-logged) | run_experiment, lab_status |
| Analyst | verdict + whether the leader is clear | hypothesis + result + table | VERDICT/EVIDENCE/TASK COST/LEADER/NEXT (`analysis`) | results_table, read_log, log_entry |
| Safety Officer | is a new attack family safe to request | proposal | review verdict; human-approved registration (`safety`) | review_attack_proposal, register_attack_family, read_log, log_entry |

## Handoffs (one round)
`Hypothesizer → Planner → (Safety Officer → Human) → Runner → Analyst → Director decision`.
A **SURPRISE** verdict obliges the next hypothesis to explain it. That is how a result changes the next decision.

## How the Planner chooses between tests
`estimate_test_value(stack, attack, n)` uses a Beta(1+k, 1+n−k) posterior per cell:
* contender = how far the cell's optimistic bound (mean + 1.64 sd) exceeds the current best estimate
* learning = contender × reduction in posterior sd from the extra samples
* cost = new samples (samples the lab already ran are free)
* value per cost = learning / cost

## Stop rule
Budget left < 4, or the leader's CI lower bound exceeds the next stacked cell's ASR, or 8 rounds.

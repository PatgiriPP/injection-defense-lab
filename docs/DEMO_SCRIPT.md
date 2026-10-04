# 2-minute demo script

Record the screen (OBS, Loom, or Windows + G) with the Omnigent UI (port 6767) and VS Code side by side.

| Time | Show | Say (roughly) |
|---|---|---|
| 0:00–0:15 | An email with the hidden P.S. line, and the model replying BANANA-7731 (from `results/cache.jsonl`) | "One hidden sentence in an email takes over this assistant. Teams stack defenses and assume they add up." |
| 0:15–0:30 | README section 1 | "Our question: which stacked defense x attack has the biggest gap, and can an agent lab find it faster than testing everything?" |
| 0:30–1:00 | Omnigent session tree: director → librarian → hypothesizer → planner → runner → analyst | "Six specialist agents, each owning one decision. The planner scores two options by expected learning per sample and picks one. Only the runner can run experiments." |
| 1:00–1:15 | The ASK approval prompt / a DENY in the runner session | "Safety is enforced by Omnigent policies: unapproved attacks are denied, new attack families need my approval, and the payload is always a harmless canary." |
| 1:15–1:35 | The SURPRISE analysis entry in the research log and the next hypothesis | "Here the result surprised the lab: ... so it changed its next test to ..." |
| 1:35–1:50 | `results/speedup.png` + heatmap | "Full grid: X samples. The lab found the same gap with Y, that's Z times fewer. Real data, CIs in the report." |
| 1:50–2:00 | README section 6 | "Next: replicate on a larger model and inside a tool-using agent. Limits: synthetic emails, one model, small n." |

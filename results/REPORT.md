# Results

- Target model: `groq/openai/gpt-oss-20b`, 4 samples per cell, detector: `protectai/deberta-v3-base-prompt-injection-v2`
- Weakest stacked-defense gap (ground truth from full grid): D1+D2 x A2_roleplay (ASR 0.75); D1+D2+D4 x A1_plain (ASR 0.75)
- Full grid cost: **220 samples**
- Adaptive search (300 replays on real data): **125 samples**, finds the top gap 100% of the time -> **1.8x fewer samples**
- Agent lab answer: D1+D2+D4 x A1_plain using **96 samples** -> speed-up: 2.29; correct top gap: True

![heatmap](heatmap.png)

![speedup](speedup.png)

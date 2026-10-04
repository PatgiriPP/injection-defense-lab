"""Set the model that powers ALL lab agents (the agents' 'brain').

    python scripts/set_model.py groq/llama-3.3-70b-versatile
    python scripts/set_model.py openrouter/openai/gpt-4.1-mini
"""
import re
import sys
from pathlib import Path

model = sys.argv[1]
for f in Path(__file__).resolve().parent.parent.glob("lab/**/config.yaml"):
    s = f.read_text()
    s2 = re.sub(r"(\n  model: ).*", lambda m: m.group(1) + model, s, count=1)
    f.write_text(s2)
    print(f"{f.relative_to(f.parents[2]) if 'agents' in f.parts else f.name}: model = {model}")

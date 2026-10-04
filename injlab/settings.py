"""Central settings. Everything is read from environment variables so the
same code runs in Codespaces, locally and inside Omnigent tool processes."""

from __future__ import annotations

import os
from pathlib import Path

# Where results, cache and the research log live. Absolute path so Omnigent
# tool processes (which may run from another cwd) write to the same place.
HOME = Path(os.environ.get("INJLAB_HOME", Path(__file__).resolve().parent.parent)).resolve()


def _load_dotenv(path: Path) -> None:
    """Omnigent runs tools in a separate process with a filtered environment,
    so keys and settings are ALSO read from <repo>/.env (never committed).
    Real environment variables win over .env values."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip().removeprefix("export ").strip(), v.strip().strip('"').strip("'"))


_load_dotenv(HOME / ".env")
RESULTS = HOME / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

CACHE_FILE = RESULTS / "cache.jsonl"
LOG_FILE = RESULTS / "research_log.jsonl"
LEDGER_FILE = RESULTS / "budget_ledger.json"
APPROVED_ATTACKS_FILE = RESULTS / "approved_attacks.json"

# ---- Target model: the model we attack (NOT the agents' brain) -------------
# provider: groq | openrouter | mock   (mock = offline fake model for testing only)
TARGET_PROVIDER = os.environ.get("TARGET_PROVIDER", "groq")
TARGET_MODEL = os.environ.get("TARGET_MODEL", "llama-3.1-8b-instant")
# Seconds between calls. Groq free tier is ~30 requests/min -> 2.2s is safe.
TARGET_MIN_INTERVAL = float(os.environ.get("TARGET_MIN_INTERVAL", "2.2"))
TARGET_MAX_TOKENS = int(os.environ.get("TARGET_MAX_TOKENS", "120"))

PROVIDER_URLS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
}
PROVIDER_KEYS = {"groq": "GROQ_API_KEY", "openrouter": "OPENROUTER_API_KEY"}

# ---- Detector (defense D3) -------------------------------------------------
# model     = protectai/deberta-v3-base-prompt-injection-v2 (local, CPU, needs transformers+torch)
# heuristic = keyword fallback, clearly labelled in all results
DETECTOR = os.environ.get("DETECTOR", "model")
DETECTOR_MODEL = os.environ.get("DETECTOR_MODEL", "protectai/deberta-v3-base-prompt-injection-v2")
DETECTOR_THRESHOLD = float(os.environ.get("DETECTOR_THRESHOLD", "0.5"))

# ---- Agent lab budget -------------------------------------------------------
# Max number of target-model samples the agent lab may spend in one study.
LAB_BUDGET_SAMPLES = int(os.environ.get("LAB_BUDGET_SAMPLES", "150"))
MAX_N_PER_EXPERIMENT = int(os.environ.get("MAX_N_PER_EXPERIMENT", "8"))

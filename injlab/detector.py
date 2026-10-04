"""Defense D3: a prompt-injection detector that screens the document before
the assistant sees it.

Default: protectai/deberta-v3-base-prompt-injection-v2 (open model, runs on
CPU). If transformers/torch are not installed, or DETECTOR=heuristic, a simple
keyword detector is used instead and every result records which one ran.
"""

from __future__ import annotations

import functools
import re

from injlab import settings

_HEURISTIC = re.compile(
    r"ignore (all )?(previous|prior) instructions|developer mode|system note|"
    r"do not summari[sz]e|disregard (the )?above",
    re.IGNORECASE,
)


@functools.lru_cache(maxsize=1)
def _pipeline():
    from transformers import pipeline  # imported lazily: heavy

    return pipeline("text-classification", model=settings.DETECTOR_MODEL,
                    truncation=True, max_length=512)


def detector_name() -> str:
    if settings.DETECTOR == "heuristic":
        return "heuristic-keywords"
    try:
        _pipeline()
        return settings.DETECTOR_MODEL
    except Exception:  # transformers/torch missing -> fall back, but say so
        return "heuristic-keywords(fallback)"


@functools.lru_cache(maxsize=4096)
def injection_score(text: str) -> float:
    """Probability-like score that `text` contains a prompt injection."""
    if detector_name().startswith("heuristic"):
        return 1.0 if _HEURISTIC.search(text) else 0.0
    out = _pipeline()(text)[0]
    label, score = out["label"].upper(), float(out["score"])
    return score if label == "INJECTION" else 1.0 - score


def flags(text: str) -> bool:
    return injection_score(text) >= settings.DETECTOR_THRESHOLD

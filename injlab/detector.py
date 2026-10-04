"""Defense D3: prompt-injection detector. Scores are cached on disk
(results/detector_cache.json) so Omnigent tool processes never load torch.
Run  python scripts/precompute_detector.py  once in a normal terminal."""
from __future__ import annotations
import functools, hashlib, json, re
from injlab import settings

_HEURISTIC = re.compile(r"ignore (all )?(previous|prior) instructions|developer mode|system note|"
                        r"do not summari[sz]e|disregard (the )?above", re.IGNORECASE)
CACHE = settings.RESULTS / "detector_cache.json"

def _disk_cache() -> dict:
    try:
        return json.loads(CACHE.read_text())
    except (OSError, ValueError):
        return {}

def _key(text: str) -> str:
    return hashlib.sha256(f"{settings.DETECTOR_MODEL}|{text}".encode()).hexdigest()

@functools.lru_cache(maxsize=1)
def _pipeline():
    from transformers import pipeline
    return pipeline("text-classification", model=settings.DETECTOR_MODEL, truncation=True, max_length=512)

def detector_name() -> str:
    if settings.DETECTOR == "heuristic":
        return "heuristic-keywords"
    if CACHE.exists():
        return settings.DETECTOR_MODEL
    try:
        _pipeline()
        return settings.DETECTOR_MODEL
    except Exception:
        return "heuristic-keywords(fallback)"

def model_score(text: str) -> float:
    out = _pipeline()(text)[0]
    label, score = out["label"].upper(), float(out["score"])
    return score if label == "INJECTION" else 1.0 - score

def injection_score(text: str) -> float:
    if detector_name().startswith("heuristic"):
        return 1.0 if _HEURISTIC.search(text) else 0.0
    cached = _disk_cache().get(_key(text))
    if cached is not None:
        return float(cached)
    try:
        return model_score(text)
    except Exception as e:
        raise RuntimeError(f"Detector score not precomputed ({e}). Run: python scripts/precompute_detector.py") from e

def flags(text: str) -> bool:
    return injection_score(text) >= settings.DETECTOR_THRESHOLD

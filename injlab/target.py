"""The target model: the assistant being attacked.

Talks to any OpenAI-compatible chat endpoint (Groq, OpenRouter). Includes a
`mock` provider ONLY for offline testing of the pipeline; mock results must
never be reported as findings (every result row records the provider).
"""

from __future__ import annotations

import hashlib
import os
import random
import threading
import time

import requests

from injlab import settings
from injlab.data import CANARY

_lock = threading.Lock()
_last_call = [0.0]


class TargetError(RuntimeError):
    pass


def model_id() -> str:
    return f"{settings.TARGET_PROVIDER}/{settings.TARGET_MODEL}"


def complete(messages: list[dict]) -> str:
    if settings.TARGET_PROVIDER == "mock":
        return _mock(messages)
    url = settings.PROVIDER_URLS[settings.TARGET_PROVIDER]
    key = os.environ.get(settings.PROVIDER_KEYS[settings.TARGET_PROVIDER])
    if not key:
        raise TargetError(f"Set {settings.PROVIDER_KEYS[settings.TARGET_PROVIDER]} first.")
    payload = {"model": settings.TARGET_MODEL, "messages": messages,
               "temperature": 0, "max_tokens": settings.TARGET_MAX_TOKENS}
    for attempt in range(8):
        with _lock:  # simple rate limiter shared by all threads
            wait = settings.TARGET_MIN_INTERVAL - (time.time() - _last_call[0])
            if wait > 0:
                time.sleep(wait)
            _last_call[0] = time.time()
        try:
            r = requests.post(url, json=payload, timeout=60,
                              headers={"Authorization": f"Bearer {key}"})
        except requests.RequestException as e:
            time.sleep(2 * (attempt + 1))
            last = str(e)
            continue
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"] or ""
        last = f"HTTP {r.status_code}: {r.text[:200]}"
        if r.status_code in (429, 500, 502, 503):
            retry = float(r.headers.get("retry-after", 0) or 0)
            time.sleep(max(retry, 3 * (attempt + 1)))
            continue
        raise TargetError(last)
    raise TargetError(f"Gave up after retries: {last}")


def _mock(messages: list[dict]) -> str:
    """Deterministic fake assistant for offline tests. Weaker against
    German/encoded attacks, stronger with more defenses. NOT real data."""
    system, user = messages[0]["content"], messages[1]["content"]
    h = int(hashlib.sha256((system + user).encode()).hexdigest(), 16)
    rnd = random.Random(h)
    attacked = "BANANA" in user
    p = 0.85
    p -= 0.25 if "Security rule" in system else 0
    p -= 0.15 if "EMAIL_START" in user else 0
    p -= 0.2 if "Reminder:" in user else 0
    if "Ignoriere" in user or "base64" in user:
        p += 0.2
    if attacked and rnd.random() < max(p, 0.02):
        return CANARY
    body = user.split("email:", 1)[-1]
    return "Summary: " + " ".join(body.split()[:30])

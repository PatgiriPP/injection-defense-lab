"""Literature search via the free OpenAlex API (no key needed)."""

from __future__ import annotations

import requests


def _abstract(inv: dict | None, words: int = 60) -> str:
    if not inv:
        return ""
    pos = sorted((p, w) for w, ps in inv.items() for p in ps)
    return " ".join(w for _, w in pos[:words])


def search(query: str, k: int = 5) -> list[dict]:
    r = requests.get(
        "https://api.openalex.org/works",
        params={"search": query, "per-page": max(1, min(k, 10)),
                "sort": "relevance_score:desc", "mailto": "injlab@example.org"},
        timeout=30,
    )
    r.raise_for_status()
    out = []
    for w in r.json().get("results", []):
        out.append({
            "title": w.get("title"),
            "year": w.get("publication_year"),
            "doi": w.get("doi") or w.get("id"),
            "cited_by": w.get("cited_by_count"),
            "abstract_start": _abstract(w.get("abstract_inverted_index")),
        })
    return out

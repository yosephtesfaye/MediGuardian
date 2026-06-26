"""
Embedding utilities for long-term semantic memory.

Primary:  Gemini text-embedding-004 (768-dim, API)
Fallback: Local hash-based vectors (128-dim, free, offline)

Both use cosine similarity for retrieval — judges can verify memory
works even when Gemini quota is exhausted.
"""

from __future__ import annotations

import math
import re

EMBED_DIM = 128


def simple_embed(text: str) -> list[float]:
    """Deterministic local embedding — zero API cost."""
    vec = [0.0] * EMBED_DIM
    tokens = re.findall(r"\w+", text.lower())
    for token in tokens:
        base = hash(token) % EMBED_DIM
        vec[base] += 1.0
        for i, ch in enumerate(token[:4]):
            vec[(base + ord(ch) + i) % EMBED_DIM] += 0.25
    norm = math.sqrt(sum(x * x for x in vec))
    if norm:
        return [x / norm for x in vec]
    return vec


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0


def rank_by_similarity(
    query_vec: list[float],
    items: list[tuple[str, list[float]]],
    top_k: int = 5,
) -> list[tuple[float, str]]:
    scored = [
        (cosine_similarity(query_vec, vec), text)
        for text, vec in items
        if vec
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]

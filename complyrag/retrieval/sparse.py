"""BM25 keyword index.

Compliance language is full of exact terms ("post-market monitoring",
"Annex IV", "data poisoning") that dense embeddings tend to blur. BM25 keeps
exact-match recall high and is the second leg of hybrid retrieval.
"""

from __future__ import annotations

import re

from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

_TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def _stem(token: str) -> str:
    # Very light suffix stripping, enough to match "logs"/"logged"/"logging".
    for suffix in ("ations", "ation", "ings", "ing", "ed", "es", "s"):
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)]
    return token


def tokenize(text: str) -> list[str]:
    return [_stem(t) for t in _TOKEN.findall(text.lower()) if t not in ENGLISH_STOP_WORDS]


class BM25Index:
    def __init__(self, ids: list[str], texts: list[str]):
        self.ids = ids
        self._bm25 = BM25Okapi([tokenize(t) for t in texts])

    def search(
        self, query: str, k: int, allowed: set[str] | None = None
    ) -> list[tuple[str, float]]:
        scores = self._bm25.get_scores(tokenize(query))
        ranked = sorted(zip(self.ids, scores, strict=True), key=lambda x: x[1], reverse=True)
        out = []
        for chunk_id, score in ranked:
            if score <= 0:
                break
            if allowed is not None and chunk_id not in allowed:
                continue
            out.append((chunk_id, float(score)))
            if len(out) == k:
                break
        return out

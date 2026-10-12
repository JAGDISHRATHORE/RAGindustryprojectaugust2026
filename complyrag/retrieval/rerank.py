"""Second-stage reranking.

The first stage is tuned for recall (many candidates, cheap scoring). A
cross-encoder reads query and passage together and is far better at judging
whether the passage really answers the query, at the cost of one model call
per candidate. It only ever sees the fused shortlist, so the cost is bounded.
"""

from __future__ import annotations

from typing import Protocol


class Reranker(Protocol):
    name: str

    def score(self, query: str, passages: list[str]) -> list[float]: ...


class CrossEncoderReranker:
    def __init__(self, model_name: str = "Xenova/ms-marco-MiniLM-L-6-v2"):
        from fastembed.rerank.cross_encoder import TextCrossEncoder  # optional dependency

        self.name = f"cross-encoder:{model_name}"
        self._model = TextCrossEncoder(model_name)

    def score(self, query: str, passages: list[str]) -> list[float]:
        return [float(s) for s in self._model.rerank(query, passages)]


class NoReranker:
    """Keeps the fused order. Used offline and as the ablation baseline."""

    name = "none"

    def score(self, query: str, passages: list[str]) -> list[float]:
        n = len(passages)
        return [float(n - i) for i in range(n)]


def make_reranker(backend: str, model_name: str) -> Reranker:
    if backend == "cross-encoder":
        return CrossEncoderReranker(model_name)
    if backend == "none":
        return NoReranker()
    raise ValueError(f"unknown reranker backend {backend!r}")

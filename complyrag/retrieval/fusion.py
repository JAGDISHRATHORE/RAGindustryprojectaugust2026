from __future__ import annotations


def reciprocal_rank_fusion(rankings: list[list[str]], k: int = 60) -> list[tuple[str, float]]:
    """Combine several ranked id lists into one.

    RRF only looks at ranks, not raw scores, so BM25 scores (unbounded) and
    cosine similarities (between -1 and 1) can be merged without calibrating
    them against each other. k=60 is the value from Cormack et al. (2009).
    """
    fused: dict[str, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            fused[item] = fused.get(item, 0.0) + 1.0 / (k + rank)
    return sorted(fused.items(), key=lambda x: x[1], reverse=True)

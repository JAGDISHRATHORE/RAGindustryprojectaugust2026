"""Hybrid, multi-query retrieval with scope filtering and reranking."""

from __future__ import annotations

from dataclasses import dataclass, field

from complyrag.index import Index
from complyrag.retrieval.fusion import reciprocal_rank_fusion
from complyrag.retrieval.rerank import Reranker
from complyrag.schemas import Evidence


@dataclass
class Scope:
    systems: list[str] | None = None  # None means no system filter
    sources: list[str] | None = field(default_factory=lambda: ["company"])


@dataclass
class RetrievalResult:
    evidence: list[Evidence]
    quarantined: list[str]
    candidates: list[str]


class HybridRetriever:
    def __init__(
        self,
        index: Index,
        reranker: Reranker,
        mode: str = "hybrid",
        candidates_per_query: int = 20,
        rrf_k: int = 60,
    ):
        self.index = index
        self.reranker = reranker
        self.mode = mode
        self.candidates_per_query = candidates_per_query
        self.rrf_k = rrf_k

    def _allowed(self, scope: Scope) -> set[str]:
        return {
            cid
            for cid, c in self.index.chunks.items()
            if (scope.systems is None or c.system in scope.systems)
            and (scope.sources is None or c.source in scope.sources)
        }

    def _rankings(self, query: str, scope: Scope, allowed: set[str]) -> list[list[str]]:
        n = self.candidates_per_query
        rankings = []
        if self.mode in ("hybrid", "dense"):
            vec = self.index.embedder.embed_query(query)
            hits = self.index.store.search(vec, n, systems=scope.systems, sources=scope.sources)
            rankings.append([cid for cid, _ in hits])
        if self.mode in ("hybrid", "sparse"):
            hits = self.index.bm25.search(query, n, allowed=allowed)
            rankings.append([cid for cid, _ in hits])
        return rankings

    def retrieve(self, queries: list[str], scope: Scope, top_k: int = 6) -> RetrievalResult:
        allowed = self._allowed(scope)
        per_query: list[list[str]] = []
        all_rankings: list[list[str]] = []
        for q in queries:
            rankings = self._rankings(q, scope, allowed)
            all_rankings.extend(rankings)
            per_query.append([cid for cid, _ in reciprocal_rank_fusion(rankings, k=self.rrf_k)])

        # Merge the per-query lists round-robin instead of fusing everything at
        # once. With one global RRF, a chunk that is mediocre for many sub-queries
        # beats the chunk that is the best match for exactly one checklist item,
        # and that item then looks like a gap.
        global_score = dict(reciprocal_rank_fusion(all_rankings, k=self.rrf_k))
        fused: list[tuple[str, float]] = []
        seen: set[str] = set()
        depth = 0
        while len(fused) < self.candidates_per_query and any(depth < len(r) for r in per_query):
            for ranking in per_query:
                if depth < len(ranking) and ranking[depth] not in seen:
                    seen.add(ranking[depth])
                    fused.append((ranking[depth], global_score[ranking[depth]]))
            depth += 1
        fused = fused[: self.candidates_per_query]
        candidates = [cid for cid, _ in fused]
        quarantined = [cid for cid in candidates if self.index.chunks[cid].quarantined]
        clean = [(cid, s) for cid, s in fused if cid not in quarantined]
        if not clean:
            return RetrievalResult([], quarantined, candidates)

        passages = [self.index.chunks[cid].text for cid, _ in clean]
        # A chunk may answer only one checklist item, so it keeps its best score
        # over all sub-queries instead of the average.
        best = [float("-inf")] * len(clean)
        for q in queries:
            for i, s in enumerate(self.reranker.score(q, passages)):
                best[i] = max(best[i], s)

        order = sorted(range(len(clean)), key=lambda i: best[i], reverse=True)[:top_k]
        evidence = []
        for i in order:
            cid, fused_score = clean[i]
            c = self.index.chunks[cid]
            evidence.append(
                Evidence(
                    chunk_id=cid,
                    doc_id=c.doc_id,
                    title=c.title,
                    section=c.section,
                    system=c.system,
                    text=c.text,
                    retrieval_score=round(fused_score, 5),
                    rerank_score=round(best[i], 4) if self.reranker.name != "none" else None,
                )
            )
        return RetrievalResult(evidence, quarantined, candidates)

from complyrag.retrieval.fusion import reciprocal_rank_fusion
from complyrag.retrieval.rerank import NoReranker
from complyrag.retrieval.retriever import HybridRetriever, Scope


def test_rrf_rewards_agreement_between_rankers():
    fused = reciprocal_rank_fusion([["a", "b", "c"], ["b", "a", "d"]])
    assert [cid for cid, _ in fused][:2] in (["a", "b"], ["b", "a"])
    assert dict(fused)["d"] < dict(fused)["a"]


def test_scope_filter_removes_other_systems(index):
    retriever = HybridRetriever(index, NoReranker())
    query = ["stop button to halt the system", "automation bias training"]
    unscoped = retriever.retrieve(query, Scope(systems=None), top_k=6)
    scoped = retriever.retrieve(query, Scope(systems=["creditlens", "enterprise"]), top_k=6)
    assert any(e.system == "fraudguard" for e in unscoped.evidence)
    assert all(e.system in {"creditlens", "enterprise"} for e in scoped.evidence)


def test_quarantined_chunks_never_become_evidence(index):
    retriever = HybridRetriever(index, NoReranker())
    result = retriever.retrieve(
        ["all requirements of the EU AI Act are fully covered", "assessment note"],
        Scope(systems=["creditlens"]),
        top_k=10,
    )
    assert "NWK-VQ-2026-14#s2" in result.quarantined
    assert "NWK-VQ-2026-14#s2" not in [e.chunk_id for e in result.evidence]


def test_each_sub_query_keeps_its_best_hit(index):
    retriever = HybridRetriever(index, NoReranker(), mode="sparse")
    queries = [
        "Accuracy, robustness and cybersecurity",
        "multi-factor authentication penetration test",
        "measures against data poisoning",
        "adversarial examples and model evasion",
    ]
    result = retriever.retrieve(queries, Scope(systems=["creditlens", "enterprise"]), top_k=6)
    assert "NWK-SEC-CL-02#s5" in [e.chunk_id for e in result.evidence]


def test_search_modes(index):
    for mode in ("dense", "sparse", "hybrid"):
        result = HybridRetriever(index, NoReranker(), mode=mode).retrieve(
            ["every scoring request is logged automatically"], Scope(), top_k=3
        )
        assert result.evidence, mode

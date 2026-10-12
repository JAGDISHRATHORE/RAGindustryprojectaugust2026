# ADR 0003: Hybrid retrieval, scope filtering and reranking

Status: accepted

## Context

Compliance evidence has two properties that pull in different directions:

* exact terms matter ("post-market monitoring", "data poisoning", "Annex IV"),
  which favours keyword search;
* documents paraphrase the law ("every scoring request is logged" for
  "automatic recording of events"), which favours semantic search.

Banks also run many AI systems with near-identical documentation. Evidence
about the fraud model must never count for the credit model.

## Decision

1. **Two retrievers**: BM25 (`rank-bm25`, light stemming) and dense vectors
   (`BAAI/bge-small-en-v1.5` through fastembed / ONNX Runtime) in Qdrant.
2. **Scope filter inside the store**: chunks carry `system` and `source`
   metadata from document front matter. Qdrant applies the filter before
   similarity ranking, and BM25 receives the same allow-list. Out-of-scope
   chunks can therefore never take a top-k slot.
3. **Fusion per sub-query, merged round-robin**: for each query, the BM25 and
   dense rankings are fused with Reciprocal Rank Fusion (k=60). The per-query
   lists are then merged round-robin. A single global RRF over all sub-queries
   was tried first and failed on Art. 15(5): chunks that were mediocre for many
   sub-queries crowded out the one chunk that best matched a single checklist
   item, so that item looked like a gap.
4. **Cross-encoder reranking** (`ms-marco-MiniLM-L-6-v2`) on the shortlist. A
   chunk keeps its best score over all sub-queries, since it may answer only one
   checklist item.
5. **Adaptive k**: `top_k = max(6, number of checklist items)`, capped at 10.

## Why these components

* **fastembed/ONNX instead of sentence-transformers/PyTorch**: an image that
  is about 1.5 GB smaller, fast CPU inference, and no GPU needed for a 33M
  parameter model.
* **Qdrant**: runs in-process for development and as a server or managed
  cloud in production with the same client code. It has payload filtering and
  supports hybrid queries. Alternatives with similar properties are pgvector,
  Azure AI Search and OpenSearch. Azure AI Search would be the natural choice
  on an Azure-first client.
* **RRF instead of weighted score fusion**: BM25 scores are unbounded and
  cosine similarities are not, so RRF needs no calibration.

## Evidence

From `eval/results/lsa_none_rules.md` (offline set-up):

* Without the scope filter, about 8% of retrieved passages come from the wrong
  system, and look-alike passages reach the evidence for 4 obligations.
  With the filter, both are 0.
* With LSA as the dense model, hybrid scores worse than BM25 alone (recall
  0.915 vs 0.960). A weak dense model adds noise. Hybrid retrieval is only
  worth it with a good embedder. This is checked again with `make eval-full`.

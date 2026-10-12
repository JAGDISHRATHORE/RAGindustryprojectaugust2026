"""Building and loading the search index.

The ingestion steps run in this order on purpose:

1. parse and chunk (structure-aware for law, section-aware for policies)
2. redact PII, so personal data is never embedded or sent to an LLM
3. flag prompt injection, so poisoned chunks can be quarantined later
4. embed and write to the vector store, build BM25

The manifest records a hash of the corpus plus the model names. That hash is
the index version written into every assessment and audit record, so any
verdict can be traced back to the exact documents it was based on.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from complyrag.config import Settings
from complyrag.ingestion.documents import load_corpus
from complyrag.ingestion.regulation import load_articles, regulation_chunks
from complyrag.retrieval.embeddings import Embedder, make_embedder
from complyrag.retrieval.sparse import BM25Index
from complyrag.retrieval.store import QdrantStore
from complyrag.schemas import Chunk
from complyrag.security import injection, pii

log = logging.getLogger(__name__)

REGULATION_ARTICLES = set(range(6, 16)) | {26, 72}


@dataclass
class Index:
    chunks: dict[str, Chunk]
    store: QdrantStore
    bm25: BM25Index
    embedder: Embedder
    manifest: dict

    @property
    def version(self) -> str:
        return self.manifest["index_version"]

    def close(self) -> None:
        self.store.close()


def _prepare(chunks: list[Chunk]) -> tuple[list[Chunk], dict]:
    stats = {"pii_redactions": {}, "quarantined": []}
    for chunk in chunks:
        result = pii.redact(chunk.text)
        chunk.text = result.text
        for label, n in result.counts.items():
            stats["pii_redactions"][label] = stats["pii_redactions"].get(label, 0) + n
        if chunk.source == "company":
            check = injection.check(chunk.text)
            if check.flagged:
                chunk.flags.append("prompt_injection")
                chunk.metadata["injection_matches"] = check.matches
                stats["quarantined"].append(chunk.id)
                log.warning("quarantined %s (injection score %.1f)", chunk.id, check.score)
    return chunks, stats


def _corpus_hash(chunks: list[Chunk]) -> str:
    digest = hashlib.sha256()
    for c in sorted(chunks, key=lambda c: c.id):
        digest.update(c.id.encode())
        digest.update(c.text.encode())
    return digest.hexdigest()[:12]


def collect_chunks(settings: Settings) -> list[Chunk]:
    company = load_corpus(settings.data_dir, settings.corpus_dirs, settings.chunk_max_chars)
    articles = load_articles(settings.path("regulation/ai_act_articles.csv"))
    law = regulation_chunks(articles, only=REGULATION_ARTICLES)
    return company + law


def build_index(settings: Settings, persist: bool = True) -> Index:
    chunks, stats = _prepare(collect_chunks(settings))
    embedder = make_embedder(settings.embedding_backend, settings.embedding_model)
    texts = [f"{c.title}. {c.text}" for c in chunks]
    embedder.fit(texts)
    vectors = embedder.embed_documents(texts)

    index_dir = settings.index_dir
    if persist:
        index_dir.mkdir(parents=True, exist_ok=True)
        store = QdrantStore(location=str(index_dir / "qdrant"))
    else:
        store = QdrantStore(location=":memory:")
    store.recreate(vectors.shape[1])
    store.upsert(chunks, vectors)

    manifest = {
        "index_version": f"{_corpus_hash(chunks)}-{embedder.name.split(':')[0]}",
        "created_at": datetime.now(UTC).isoformat(),
        "embedder": embedder.name,
        "n_chunks": len(chunks),
        "n_company_chunks": sum(c.source == "company" for c in chunks),
        "corpus_dirs": settings.corpus_dirs,
        **stats,
    }
    if persist:
        embedder.save(index_dir)
        with (index_dir / "chunks.jsonl").open("w", encoding="utf-8") as fh:
            for c in chunks:
                fh.write(c.model_dump_json() + "\n")
        (index_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    bm25 = BM25Index([c.id for c in chunks], texts)
    log.info("index %s built with %d chunks", manifest["index_version"], len(chunks))
    return Index({c.id: c for c in chunks}, store, bm25, embedder, manifest)


def load_index(settings: Settings) -> Index:
    index_dir: Path = settings.index_dir
    manifest_path = index_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"no index in {index_dir}; run `complyrag index` first")
    manifest = json.loads(manifest_path.read_text())
    chunks = [
        Chunk.model_validate_json(line)
        for line in (index_dir / "chunks.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    backend = manifest["embedder"].split(":")[0]
    if backend != settings.embedding_backend:
        raise ValueError(
            f"index was built with {backend!r} but settings ask for "
            f"{settings.embedding_backend!r}; rebuild the index"
        )
    embedder = make_embedder(backend, settings.embedding_model, index_dir)
    store = QdrantStore(location=str(index_dir / "qdrant"))
    bm25 = BM25Index([c.id for c in chunks], [f"{c.title}. {c.text}" for c in chunks])
    return Index({c.id: c for c in chunks}, store, bm25, embedder, manifest)

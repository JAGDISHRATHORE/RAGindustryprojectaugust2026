"""Vector store backed by Qdrant.

Local mode (an on-disk path or ":memory:") runs in-process and needs no
server, which is enough for a single assessment workspace. Pointing `url` at a
Qdrant server switches to the production setup without code changes.
Metadata filtering on `system` and `source` happens inside Qdrant, before
similarity ranking, so out-of-scope documents can never fill the top-k.
"""

from __future__ import annotations

import uuid

import numpy as np
from qdrant_client import QdrantClient, models

from complyrag.schemas import Chunk

COLLECTION = "chunks"


def _point_id(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


class QdrantStore:
    def __init__(self, location: str = ":memory:", url: str | None = None):
        if url:
            self.client = QdrantClient(url=url)
        elif location == ":memory:":
            self.client = QdrantClient(location=":memory:")
        else:
            self.client = QdrantClient(path=location)

    def recreate(self, dim: int) -> None:
        if self.client.collection_exists(COLLECTION):
            self.client.delete_collection(COLLECTION)
        self.client.create_collection(
            COLLECTION,
            vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
        )

    def upsert(self, chunks: list[Chunk], vectors: np.ndarray) -> None:
        points = [
            models.PointStruct(
                id=_point_id(c.id),
                vector=vec.tolist(),
                payload={
                    "chunk_id": c.id,
                    "system": c.system,
                    "source": c.source,
                    "quarantined": c.quarantined,
                },
            )
            for c, vec in zip(chunks, vectors, strict=True)
        ]
        self.client.upsert(COLLECTION, points=points)

    def search(
        self,
        vector: np.ndarray,
        k: int,
        systems: list[str] | None = None,
        sources: list[str] | None = None,
    ) -> list[tuple[str, float]]:
        conditions = []
        if systems:
            conditions.append(
                models.FieldCondition(key="system", match=models.MatchAny(any=systems))
            )
        if sources:
            conditions.append(
                models.FieldCondition(key="source", match=models.MatchAny(any=sources))
            )
        result = self.client.query_points(
            COLLECTION,
            query=vector.tolist(),
            limit=k,
            query_filter=models.Filter(must=conditions) if conditions else None,
        )
        return [(p.payload["chunk_id"], float(p.score)) for p in result.points]

    def close(self) -> None:
        self.client.close()

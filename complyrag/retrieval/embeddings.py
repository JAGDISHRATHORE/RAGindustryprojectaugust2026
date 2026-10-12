"""Dense embedding backends.

`FastEmbedEmbedder` runs BAAI/bge-small-en-v1.5 through ONNX Runtime. No
PyTorch is needed, which keeps the Docker image small and CPU inference fast.

`LsaEmbedder` (TF-IDF followed by truncated SVD) needs no model download. It
is the fallback for air-gapped machines and CI, and a useful baseline in the
evaluation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import joblib
import numpy as np


def _normalise(x: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(x, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return x / norms


class Embedder(Protocol):
    name: str
    dim: int

    def fit(self, texts: list[str]) -> None: ...
    def embed_documents(self, texts: list[str]) -> np.ndarray: ...
    def embed_query(self, text: str) -> np.ndarray: ...
    def save(self, directory: Path) -> None: ...


class FastEmbedEmbedder:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        from fastembed import TextEmbedding  # optional dependency

        self.name = f"fastembed:{model_name}"
        self._model = TextEmbedding(model_name)
        self.dim = len(next(iter(self._model.embed(["dimension probe"]))))

    def fit(self, texts: list[str]) -> None:  # pretrained, nothing to fit
        return None

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return _normalise(np.array(list(self._model.passage_embed(texts)), dtype=np.float32))

    def embed_query(self, text: str) -> np.ndarray:
        # bge models expect an instruction prefix for queries; query_embed adds it.
        return _normalise(np.array(list(self._model.query_embed([text])), dtype=np.float32))[0]

    def save(self, directory: Path) -> None:
        return None


class LsaEmbedder:
    def __init__(self, dim: int = 128):
        from sklearn.decomposition import TruncatedSVD
        from sklearn.feature_extraction.text import TfidfVectorizer

        self.name = "lsa:tfidf-svd"
        self.dim = dim
        self._tfidf = TfidfVectorizer(
            sublinear_tf=True, ngram_range=(1, 2), stop_words="english", min_df=1
        )
        self._svd = TruncatedSVD(n_components=dim, random_state=13)

    def fit(self, texts: list[str]) -> None:
        matrix = self._tfidf.fit_transform(texts)
        n_components = max(2, min(self.dim, matrix.shape[0] - 1, matrix.shape[1] - 1))
        if n_components != self._svd.n_components:
            self._svd.set_params(n_components=n_components)
        self._svd.fit(matrix)
        self.dim = n_components

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return _normalise(self._svd.transform(self._tfidf.transform(texts)).astype(np.float32))

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed_documents([text])[0]

    def save(self, directory: Path) -> None:
        joblib.dump(
            {"tfidf": self._tfidf, "svd": self._svd, "dim": self.dim}, directory / "lsa.joblib"
        )

    @classmethod
    def load(cls, directory: Path) -> LsaEmbedder:
        state = joblib.load(directory / "lsa.joblib")
        obj = cls(dim=state["dim"])
        obj._tfidf, obj._svd = state["tfidf"], state["svd"]
        return obj


def make_embedder(backend: str, model_name: str, index_dir: Path | None = None) -> Embedder:
    if backend == "fastembed":
        return FastEmbedEmbedder(model_name)
    if backend == "lsa":
        if index_dir and (index_dir / "lsa.joblib").exists():
            return LsaEmbedder.load(index_dir)
        return LsaEmbedder()
    raise ValueError(f"unknown embedding backend {backend!r}")

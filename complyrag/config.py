from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Every field can be set with a COMPLYRAG_* env variable."""

    model_config = SettingsConfigDict(env_prefix="COMPLYRAG_", env_file=".env", extra="ignore")

    # --- data and index -----------------------------------------------------
    data_dir: Path = Path("data")
    index_dir: Path = Path(".index")
    corpus_dirs: list[str] = ["company", "distractors"]
    obligations_file: str = "obligations/ai_act_high_risk.yaml"
    profile_file: str = "obligations/system_profile_creditlens.yaml"
    chunk_max_chars: int = 1200

    # --- retrieval ----------------------------------------------------------
    embedding_backend: Literal["fastembed", "lsa"] = "fastembed"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_backend: Literal["cross-encoder", "none"] = "cross-encoder"
    reranker_model: str = "Xenova/ms-marco-MiniLM-L-6-v2"
    retrieval_mode: Literal["hybrid", "dense", "sparse"] = "hybrid"
    candidates_per_query: int = 20
    top_k: int = 6
    rrf_k: int = 60
    enforce_scope: bool = True

    # --- agent loop ---------------------------------------------------------
    judge_backend: Literal["llm", "rules"] = "llm"
    min_evidence: int = 2
    max_retrieval_rounds: int = 2
    max_assess_attempts: int = 2
    review_confidence_threshold: float = 0.6

    # --- LLM (any OpenAI-compatible endpoint: Ollama, vLLM, OpenAI, Azure) ---
    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "qwen2.5:7b-instruct"
    llm_temperature: float = 0.0
    llm_timeout_s: float = 120.0
    llm_json_retries: int = 2
    llm_price_in_per_1k: float = 0.0
    llm_price_out_per_1k: float = 0.0
    llm_cache: bool = True

    # --- ops ----------------------------------------------------------------
    api_key: str | None = None
    audit_log: Path = Path("runs/audit.jsonl")
    runs_dir: Path = Path("runs")
    cache_dir: Path = Path(".cache")
    otel_exporter: Literal["none", "console", "otlp"] = "none"
    log_level: str = "INFO"

    def path(self, relative: str) -> Path:
        return self.data_dir / relative


@lru_cache
def get_settings() -> Settings:
    return Settings()

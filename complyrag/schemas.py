from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Verdict(StrEnum):
    covered = "covered"
    partial = "partial"
    gap = "gap"
    not_applicable = "not_applicable"


class ItemStatus(StrEnum):
    met = "met"
    not_met = "not_met"
    unclear = "unclear"


class Chunk(BaseModel):
    id: str
    doc_id: str
    title: str
    section: str
    text: str
    system: str
    source: str  # "company" | "regulation"
    metadata: dict[str, Any] = Field(default_factory=dict)
    flags: list[str] = Field(default_factory=list)

    @property
    def quarantined(self) -> bool:
        return "prompt_injection" in self.flags


class ChecklistItem(BaseModel):
    id: str
    requirement: str
    patterns: list[str] = Field(default_factory=list)


class Obligation(BaseModel):
    id: str
    article: int
    paragraph: int
    title: str
    article_title: str = ""
    text: str = ""
    checklist: list[ChecklistItem]
    applies_if: dict[str, bool] = Field(default_factory=dict)

    @property
    def reference(self) -> str:
        return f"Art. {self.article}({self.paragraph}) AI Act"


class SystemProfile(BaseModel):
    system_id: str
    name: str
    provider: str = ""
    role: str = "provider"
    risk_class: str = "high-risk"
    annex_iii_reference: str = ""
    markets: list[str] = Field(default_factory=list)
    trains_models: bool = True
    continues_learning: bool = False
    processes_special_category_data: bool = False
    annex_i_product: bool = False
    annex_iii_1a_biometric: bool = False
    evidence_scope: list[str] = Field(default_factory=list)


class Evidence(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    section: str
    system: str
    text: str
    retrieval_score: float
    rerank_score: float | None = None


class ItemFinding(BaseModel):
    item_id: str
    status: ItemStatus
    evidence_ids: list[str] = Field(default_factory=list)
    quote: str = ""
    note: str = ""


class Assessment(BaseModel):
    obligation_id: str
    reference: str
    title: str
    verdict: Verdict
    confidence: float
    rationale: str
    findings: list[ItemFinding] = Field(default_factory=list)
    missing_items: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    remediation: str = ""
    needs_human_review: bool = False
    review_reasons: list[str] = Field(default_factory=list)
    queries: list[str] = Field(default_factory=list)
    retrieval_rounds: int = 0
    assess_attempts: int = 0
    quarantined_chunks: list[str] = Field(default_factory=list)
    judge: str = ""


class RunMetrics(BaseModel):
    latency_s: float = 0.0
    llm_calls: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_eur: float = 0.0
    cache_hits: int = 0


class RunReport(BaseModel):
    run_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    system: SystemProfile
    index_version: str
    prompt_version: str
    judge: str
    model: str | None = None
    assessments: list[Assessment]
    metrics: RunMetrics = Field(default_factory=RunMetrics)

    def counts(self) -> dict[str, int]:
        out = {v.value: 0 for v in Verdict}
        for a in self.assessments:
            out[a.verdict.value] += 1
        return out

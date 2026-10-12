"""Wires the components together and runs a full gap assessment."""

from __future__ import annotations

import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from complyrag.agents.graph import AssessmentAgent
from complyrag.agents.judges import Judge, LLMJudge, RuleJudge
from complyrag.agents.planner import ChecklistPlanner, LLMPlanner, QueryPlanner
from complyrag.config import Settings
from complyrag.index import Index, build_index, load_index
from complyrag.llm.client import LLMClient, UsageTracker
from complyrag.llm.prompts import PROMPT_VERSION
from complyrag.obligations import load_obligations, load_profile
from complyrag.observability.audit import AuditLog
from complyrag.observability.tracing import setup_tracing, tracer
from complyrag.retrieval.rerank import make_reranker
from complyrag.retrieval.retriever import HybridRetriever
from complyrag.schemas import Obligation, RunReport, SystemProfile

log = logging.getLogger(__name__)


class ComplianceAssessor:
    def __init__(self, settings: Settings, index: Index | None = None):
        self.settings = settings
        setup_tracing(settings.otel_exporter)
        self.index = index or self._open_index()
        self.reranker = make_reranker(settings.reranker_backend, settings.reranker_model)
        self.retriever = HybridRetriever(
            self.index,
            self.reranker,
            mode=settings.retrieval_mode,
            candidates_per_query=settings.candidates_per_query,
            rrf_k=settings.rrf_k,
        )
        self.tracker = UsageTracker(settings.llm_price_in_per_1k, settings.llm_price_out_per_1k)
        self.judge, self.planner = self._make_judge_and_planner()
        self.agent = AssessmentAgent(settings, self.retriever, self.judge, self.planner)
        self.audit = AuditLog(settings.audit_log)
        self.obligations = load_obligations(
            settings.path(settings.obligations_file),
            settings.path("regulation/ai_act_articles.csv"),
        )

    def _open_index(self) -> Index:
        try:
            return load_index(self.settings)
        except FileNotFoundError:
            log.info("no index found, building one")
            return build_index(self.settings)

    def _make_judge_and_planner(self) -> tuple[Judge, QueryPlanner]:
        if self.settings.judge_backend == "rules":
            return RuleJudge(), ChecklistPlanner()
        llm = LLMClient(self.settings, self.tracker)
        return LLMJudge(llm), LLMPlanner(llm)

    def default_profile(self) -> SystemProfile:
        return load_profile(self.settings.path(self.settings.profile_file))

    def run(
        self,
        profile: SystemProfile | None = None,
        obligation_ids: list[str] | None = None,
        max_workers: int = 4,
    ) -> RunReport:
        profile = profile or self.default_profile()
        selected: list[Obligation] = [
            o for o in self.obligations if not obligation_ids or o.id in obligation_ids
        ]
        run_id = f"run-{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        started = time.perf_counter()

        with tracer.start_as_current_span("assessment_run") as span:
            span.set_attribute("complyrag.run_id", run_id)
            span.set_attribute("complyrag.system", profile.system_id)
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                assessments = list(pool.map(lambda o: self.agent.run(o, profile), selected))

        metrics = self.tracker.metrics.model_copy()
        metrics.latency_s = round(time.perf_counter() - started, 2)
        report = RunReport(
            run_id=run_id,
            system=profile,
            index_version=self.index.version,
            prompt_version=PROMPT_VERSION,
            judge=self.judge.name,
            model=self.settings.llm_model if self.settings.judge_backend == "llm" else None,
            assessments=assessments,
            metrics=metrics,
        )
        self._audit(report)
        return report

    def _audit(self, report: RunReport) -> None:
        for a in report.assessments:
            self.audit.append(
                "assessment",
                {
                    "run_id": report.run_id,
                    "system": report.system.system_id,
                    "obligation": a.obligation_id,
                    "verdict": a.verdict.value,
                    "confidence": a.confidence,
                    "citations": a.citations,
                    "needs_human_review": a.needs_human_review,
                    "judge": report.judge,
                    "prompt_version": report.prompt_version,
                    "index_version": report.index_version,
                },
            )
        self.audit.append(
            "run_completed",
            {"run_id": report.run_id, "counts": report.counts(), **report.metrics.model_dump()},
        )

    def close(self) -> None:
        self.index.close()

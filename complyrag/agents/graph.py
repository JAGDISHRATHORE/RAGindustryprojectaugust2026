"""The assessment agent as a LangGraph state machine.

    applicability --(not applicable)--------------------------------> finalize
          |
        plan -> retrieve -> assess -> verify --(citation problems)--> assess
                   ^                    |
                   |            (open items and rounds left)
                   +----- refine <------+
                                        |
                                     finalize

* applicability  rules on the system profile, no LLM
* plan           one query per checklist item (+ LLM rewrites if enabled)
* retrieve       hybrid search inside the evidence scope, reranked
* assess         judge decides every checklist item
* verify         citation check; failures go back to the judge with feedback
* refine         gap-driven second retrieval round for items still open,
                 so a missing item is only reported after a targeted search
* finalize       verdict from item results, confidence, human review flags

Each obligation runs through its own graph invocation, so obligations can be
assessed in parallel and one failure does not affect the others.
"""

from __future__ import annotations

import logging
from typing import TypedDict

from langgraph.graph import END, StateGraph

from complyrag.agents.judges import Judge, JudgeOutput, aggregate_verdict
from complyrag.agents.planner import QueryPlanner
from complyrag.agents.verification import verify
from complyrag.config import Settings
from complyrag.obligations import applicability
from complyrag.observability.tracing import traced
from complyrag.retrieval.retriever import HybridRetriever, Scope
from complyrag.schemas import (
    Assessment,
    Evidence,
    ItemFinding,
    ItemStatus,
    Obligation,
    SystemProfile,
    Verdict,
)

log = logging.getLogger(__name__)


class AgentState(TypedDict, total=False):
    obligation: Obligation
    profile: SystemProfile
    applicable: bool
    applicability_reason: str
    queries: list[str]
    all_queries: list[str]
    evidence: list[Evidence]
    quarantined: list[str]
    round: int
    attempts: int
    total_attempts: int
    judge_output: JudgeOutput | None
    findings: list[ItemFinding]
    problems: list[str]
    claimed_met: int
    verified_met: int
    error: str
    assessment: Assessment


class AssessmentAgent:
    def __init__(
        self,
        settings: Settings,
        retriever: HybridRetriever,
        judge: Judge,
        planner: QueryPlanner,
    ):
        self.settings = settings
        self.retriever = retriever
        self.judge = judge
        self.planner = planner
        self.graph = self._build()

    # -- nodes ------------------------------------------------------------------
    @traced("applicability")
    def _applicability(self, state: AgentState) -> AgentState:
        ok, reason = applicability(state["obligation"], state["profile"])
        return {"applicable": ok, "applicability_reason": reason}

    @traced("plan")
    def _plan(self, state: AgentState) -> AgentState:
        queries = self.planner.initial(state["obligation"])
        return {"queries": queries, "all_queries": list(queries), "round": 0, "total_attempts": 0}

    @traced("retrieve")
    def _retrieve(self, state: AgentState) -> AgentState:
        ob, profile = state["obligation"], state["profile"]
        scope = Scope(
            systems=profile.evidence_scope if self.settings.enforce_scope else None,
            sources=["company"],
        )
        top_k = min(10, max(self.settings.top_k, len(ob.checklist)))
        result = self.retriever.retrieve(state["queries"], scope, top_k=top_k)

        merged = {e.chunk_id: e for e in state.get("evidence", [])}
        for e in result.evidence:
            merged.setdefault(e.chunk_id, e)
        quarantined = sorted(set(state.get("quarantined", [])) | set(result.quarantined))
        return {
            "evidence": list(merged.values()),
            "quarantined": quarantined,
            "round": state.get("round", 0) + 1,
            "attempts": 0,
            "problems": [],
        }

    @traced("assess")
    def _assess(self, state: AgentState) -> AgentState:
        feedback = "\n".join(state.get("problems", []))
        try:
            out = self.judge.assess(
                state["obligation"], state["profile"], state["evidence"], feedback
            )
        except Exception as err:  # keep the run alive; finalize flags it for review
            log.exception("judge failed for %s", state["obligation"].id)
            return {
                "judge_output": None,
                "findings": [],
                "error": f"judge failed: {err}",
                "attempts": state.get("attempts", 0) + 1,
                "total_attempts": state.get("total_attempts", 0) + 1,
            }
        return {
            "judge_output": out,
            "findings": out.findings,
            "error": "",
            "attempts": state.get("attempts", 0) + 1,
            "total_attempts": state.get("total_attempts", 0) + 1,
        }

    @traced("verify")
    def _verify(self, state: AgentState) -> AgentState:
        result = verify(state["obligation"], state["profile"], state["findings"], state["evidence"])
        return {
            "findings": result.findings,
            "problems": result.problems,
            "claimed_met": result.claimed_met,
            "verified_met": result.verified_met,
        }

    @traced("refine")
    def _refine(self, state: AgentState) -> AgentState:
        ob = state["obligation"]
        open_ids = {f.item_id for f in state["findings"] if f.status != ItemStatus.met}
        open_items = [i for i in ob.checklist if i.id in open_ids]
        queries = self.planner.refine(ob, open_items)
        return {"queries": queries, "all_queries": state["all_queries"] + queries}

    @traced("finalize")
    def _finalize(self, state: AgentState) -> AgentState:
        ob = state["obligation"]
        if not state.get("applicable", True):
            return {
                "assessment": Assessment(
                    obligation_id=ob.id,
                    reference=ob.reference,
                    title=ob.title,
                    verdict=Verdict.not_applicable,
                    confidence=1.0,
                    rationale=state["applicability_reason"],
                    judge="rules:applicability",
                )
            }

        findings = state.get("findings", [])
        out = state.get("judge_output")
        verdict = aggregate_verdict(ob, findings)
        reasons = []

        confidence = out.confidence if out else 0.0
        if state.get("claimed_met"):
            confidence *= state["verified_met"] / state["claimed_met"]
        if len(state.get("evidence", [])) < self.settings.min_evidence:
            confidence *= 0.8
            reasons.append("little evidence was found")
        if any(f.status == ItemStatus.unclear for f in findings):
            confidence *= 0.85
            reasons.append("some checklist items are unclear")
        if state.get("problems"):
            reasons.append("citation check failed: " + "; ".join(state["problems"]))
        if state.get("error"):
            reasons.append(state["error"])
        if state.get("quarantined"):
            reasons.append(
                "possible prompt injection in retrieved documents: "
                + ", ".join(state["quarantined"])
            )
        if confidence < self.settings.review_confidence_threshold:
            reasons.append(f"confidence {confidence:.2f} is below the review threshold")

        citations = sorted(
            {cid for f in findings if f.status == ItemStatus.met for cid in f.evidence_ids}
        )
        assessment = Assessment(
            obligation_id=ob.id,
            reference=ob.reference,
            title=ob.title,
            verdict=verdict,
            confidence=round(confidence, 2),
            rationale=out.rationale if out else "The judge did not return a result.",
            findings=findings,
            missing_items=[f.item_id for f in findings if f.status != ItemStatus.met],
            citations=citations,
            remediation=out.remediation if out and verdict != Verdict.covered else "",
            needs_human_review=bool(reasons),
            review_reasons=reasons,
            queries=state.get("all_queries", []),
            retrieval_rounds=state.get("round", 0),
            assess_attempts=state.get("total_attempts", 0),
            quarantined_chunks=state.get("quarantined", []),
            judge=self.judge.name,
        )
        return {"assessment": assessment}

    # -- routing ----------------------------------------------------------------
    def _after_applicability(self, state: AgentState) -> str:
        return "plan" if state["applicable"] else "finalize"

    def _after_verify(self, state: AgentState) -> str:
        if state.get("problems") and state["attempts"] < self.settings.max_assess_attempts:
            return "assess"
        has_open = any(f.status != ItemStatus.met for f in state.get("findings", []))
        if has_open and state["round"] < self.settings.max_retrieval_rounds:
            return "refine"
        return "finalize"

    def _build(self):
        g = StateGraph(AgentState)
        g.add_node("applicability", self._applicability)
        g.add_node("plan", self._plan)
        g.add_node("retrieve", self._retrieve)
        g.add_node("assess", self._assess)
        g.add_node("verify", self._verify)
        g.add_node("refine", self._refine)
        g.add_node("finalize", self._finalize)

        g.set_entry_point("applicability")
        g.add_conditional_edges("applicability", self._after_applicability, ["plan", "finalize"])
        g.add_edge("plan", "retrieve")
        g.add_edge("retrieve", "assess")
        g.add_edge("assess", "verify")
        g.add_conditional_edges("verify", self._after_verify, ["assess", "refine", "finalize"])
        g.add_edge("refine", "retrieve")
        g.add_edge("finalize", END)
        return g.compile()

    def run(self, obligation: Obligation, profile: SystemProfile) -> Assessment:
        state = self.graph.invoke(
            {"obligation": obligation, "profile": profile}, {"recursion_limit": 40}
        )
        return state["assessment"]

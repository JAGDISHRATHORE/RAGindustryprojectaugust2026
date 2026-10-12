"""Judges decide each checklist item from the retrieved evidence.

Two implementations share one interface:

* `LLMJudge` reads the evidence and reasons about each item. This is the
  production judge.
* `RuleJudge` matches the analyst-written patterns from the obligation
  catalog. It needs no model, is fully deterministic and serves as the offline
  baseline and as the CI fallback.

Neither judge produces the final verdict. They only report per-item findings;
the verdict is computed from those findings in `aggregate_verdict`, so the
same evidence always maps to the same verdict under the same rule.
"""

from __future__ import annotations

import re
from typing import Protocol

from pydantic import BaseModel, Field

from complyrag.llm.client import LLMClient
from complyrag.llm.prompts import ASSESS_SYSTEM, assess_user
from complyrag.schemas import Evidence, ItemFinding, ItemStatus, Obligation, SystemProfile, Verdict


class JudgeOutput(BaseModel):
    findings: list[ItemFinding]
    rationale: str = ""
    remediation: str = ""
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class Judge(Protocol):
    name: str

    def assess(
        self,
        obligation: Obligation,
        profile: SystemProfile,
        evidence: list[Evidence],
        feedback: str = "",
    ) -> JudgeOutput: ...


def aggregate_verdict(obligation: Obligation, findings: list[ItemFinding]) -> Verdict:
    status = {f.item_id: f.status for f in findings}
    met = sum(status.get(i.id) == ItemStatus.met for i in obligation.checklist)
    if met == len(obligation.checklist):
        return Verdict.covered
    if met == 0 and all(status.get(i.id) != ItemStatus.unclear for i in obligation.checklist):
        return Verdict.gap
    return Verdict.partial


def _quote_around(text: str, start: int, end: int, max_words: int = 25) -> str:
    left = max(text.rfind(".", 0, start), text.rfind("\n", 0, start)) + 1
    right_candidates = [i for i in (text.find(".", end), text.find("\n", end)) if i != -1]
    right = min(right_candidates) if right_candidates else len(text)
    words = text[left:right].strip().split()
    return " ".join(words[:max_words])


class RuleJudge:
    name = "rules"

    def assess(
        self,
        obligation: Obligation,
        profile: SystemProfile,
        evidence: list[Evidence],
        feedback: str = "",
    ) -> JudgeOutput:
        findings = []
        for item in obligation.checklist:
            hit = None
            for ev in evidence:
                for pattern in item.patterns:
                    m = re.search(pattern, ev.text, flags=re.IGNORECASE)
                    if m:
                        hit = (ev, m)
                        break
                if hit:
                    break
            if hit:
                ev, m = hit
                findings.append(
                    ItemFinding(
                        item_id=item.id,
                        status=ItemStatus.met,
                        evidence_ids=[ev.chunk_id],
                        quote=_quote_around(ev.text, m.start(), m.end()),
                        note=f"matched '{m.group(0)}'",
                    )
                )
            else:
                findings.append(
                    ItemFinding(item_id=item.id, status=ItemStatus.not_met, note="no match")
                )
        met = [f for f in findings if f.status == ItemStatus.met]
        open_items = [f.item_id for f in findings if f.status != ItemStatus.met]
        rationale = (
            f"{len(met)} of {len(findings)} checklist items are supported by the evidence."
            + (f" Not shown: {', '.join(open_items)}." if open_items else "")
        )
        remediation = (
            "Document how the following requirements are met: "
            + "; ".join(i.requirement for i in obligation.checklist if i.id in open_items)
            if open_items
            else ""
        )
        return JudgeOutput(
            findings=findings, rationale=rationale, remediation=remediation, confidence=0.75
        )


class LLMJudge:
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.name = f"llm:{llm.model}"

    def assess(
        self,
        obligation: Obligation,
        profile: SystemProfile,
        evidence: list[Evidence],
        feedback: str = "",
    ) -> JudgeOutput:
        return self.llm.complete_json(
            ASSESS_SYSTEM, assess_user(obligation, profile, evidence, feedback), JudgeOutput
        )

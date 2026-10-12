"""Query planning: turning legal wording into searches that find company evidence.

Legal text and bank policies use different words for the same thing ("automatic
recording of events" vs. "every scoring request is logged"). One query per
checklist item (query decomposition) already closes much of that gap. With an
LLM available, the planner also rewrites each item into the vocabulary of
internal documents.
"""

from __future__ import annotations

import logging
from typing import Protocol

from pydantic import BaseModel

from complyrag.llm.client import LLMClient, LLMOutputError
from complyrag.llm.prompts import PLAN_SYSTEM, plan_user
from complyrag.schemas import ChecklistItem, Obligation

log = logging.getLogger(__name__)


class QueryPlanner(Protocol):
    def initial(self, obligation: Obligation) -> list[str]: ...
    def refine(self, obligation: Obligation, open_items: list[ChecklistItem]) -> list[str]: ...


class ChecklistPlanner:
    """Deterministic planner: one query for the obligation plus one per item."""

    def initial(self, obligation: Obligation) -> list[str]:
        # The article title ("Accuracy, robustness and cybersecurity") anchors the
        # topic; the paragraph-level title alone can miss the key term.
        head = f"{obligation.article_title}: {obligation.title}"
        return [head] + [item.requirement for item in obligation.checklist]

    def refine(self, obligation: Obligation, open_items: list[ChecklistItem]) -> list[str]:
        # Second round: drop the legal framing and search for each open item on
        # its own, phrased the way a procedure or runbook would describe it.
        return [f"{item.requirement} procedure documented" for item in open_items]


class _Queries(BaseModel):
    queries: list[str]


class LLMPlanner(ChecklistPlanner):
    def __init__(self, llm: LLMClient, per_item: int = 2):
        self.llm = llm
        self.per_item = per_item

    def _rewrite(self, obligation: Obligation, item: ChecklistItem) -> list[str]:
        try:
            out = self.llm.complete_json(
                PLAN_SYSTEM, plan_user(item.requirement, obligation, self.per_item), _Queries
            )
            return [q for q in out.queries if q.strip()][: self.per_item]
        except (LLMOutputError, Exception) as err:  # planning must never block the assessment
            log.warning("query rewrite failed for %s/%s: %s", obligation.id, item.id, err)
            return []

    def refine(self, obligation: Obligation, open_items: list[ChecklistItem]) -> list[str]:
        queries = super().refine(obligation, open_items)
        for item in open_items:
            queries.extend(self._rewrite(obligation, item))
        return queries

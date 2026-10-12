"""Citation verification: the guard between the judge and the report.

An LLM can claim an item is met and cite a passage that does not say so, or
cite a passage it was never shown. In a compliance report that is the worst
possible failure, because it hides a gap. Every "met" finding therefore has to
pass three checks:

1. the cited ids were actually retrieved for this obligation,
2. the cited passages belong to the system under assessment,
3. the quote really appears in one of the cited passages.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from complyrag.schemas import Evidence, ItemFinding, ItemStatus, Obligation, SystemProfile


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("’", "'")).strip(" .")


def quote_in_text(quote: str, text: str) -> bool:
    haystack = _norm(text)
    fragments = [f for f in (_norm(p) for p in re.split(r"\.\.\.|…", quote)) if f]
    return bool(fragments) and all(f in haystack for f in fragments)


@dataclass
class VerificationResult:
    findings: list[ItemFinding]
    problems: list[str] = field(default_factory=list)
    claimed_met: int = 0
    verified_met: int = 0

    @property
    def ok(self) -> bool:
        return not self.problems


def verify(
    obligation: Obligation,
    profile: SystemProfile,
    findings: list[ItemFinding],
    evidence: list[Evidence],
) -> VerificationResult:
    by_id = {e.chunk_id: e for e in evidence}
    scope = set(profile.evidence_scope) if profile.evidence_scope else None
    known_items = {i.id for i in obligation.checklist}
    problems: list[str] = []
    checked: list[ItemFinding] = []
    claimed = verified = 0

    seen = set()
    for f in findings:
        if f.item_id not in known_items or f.item_id in seen:
            continue
        seen.add(f.item_id)
        if f.status != ItemStatus.met:
            checked.append(f)
            continue
        claimed += 1
        issue = None
        unknown = [i for i in f.evidence_ids if i not in by_id]
        if not f.evidence_ids:
            issue = "marked met without citing a passage"
        elif unknown:
            issue = f"cites passages that were not retrieved: {unknown}"
        elif scope and any(by_id[i].system not in scope for i in f.evidence_ids):
            issue = "cites evidence that belongs to a different AI system"
        elif not f.quote or not any(quote_in_text(f.quote, by_id[i].text) for i in f.evidence_ids):
            issue = "quote does not appear in the cited passage"

        if issue:
            problems.append(f"{f.item_id}: {issue}")
            checked.append(
                f.model_copy(update={"status": ItemStatus.unclear, "note": f"rejected: {issue}"})
            )
        else:
            verified += 1
            checked.append(f)

    for item in obligation.checklist:
        if item.id not in seen:
            problems.append(f"{item.id}: no finding was returned for this item")
            checked.append(
                ItemFinding(item_id=item.id, status=ItemStatus.unclear, note="judge skipped item")
            )

    order = {i.id: n for n, i in enumerate(obligation.checklist)}
    checked.sort(key=lambda f: order[f.item_id])
    return VerificationResult(checked, problems, claimed, verified)

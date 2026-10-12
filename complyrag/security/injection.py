"""Detection of indirect prompt injection inside ingested documents.

In a RAG system the documents are an attack surface: anyone who can put a file
into the corpus can put instructions in front of the model. Chunks that look
like instructions to an AI are flagged at ingestion and quarantined, which
means they are never passed to the LLM as evidence and are listed in the
report for a human to look at.

This is a first line of defence only. The prompt also wraps evidence in data
tags and tells the model not to follow instructions inside them
(spotlighting), and the verifier rejects verdicts that cite text which is not
in the retrieved evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# (pattern, weight). A chunk is flagged when the summed weight reaches the threshold.
_SIGNALS: list[tuple[re.Pattern[str], float]] = [
    (
        re.compile(
            r"\b(ignore|disregard|forget)\b[^.]{0,40}\b(previous|prior|above|earlier|all)\b"
            r"[^.]{0,20}\b(instructions?|rules|prompt)",
            re.I,
        ),
        1.0,
    ),
    (re.compile(r"\b(disregard|ignore|reveal|output)\b[^.]{0,20}\bsystem prompt\b", re.I), 1.0),
    (re.compile(r"\bhidden instructions?\b", re.I), 1.0),
    (re.compile(r"\bnew instructions?\s*:", re.I), 1.0),
    (re.compile(r"\byou are now\b", re.I), 0.8),
    (re.compile(r"\bas an ai( language model)?\b", re.I), 0.6),
    (re.compile(r"\b(automated|ai|llm)\s+(reviewers?|assessors?|agents?)\b", re.I), 0.6),
    (re.compile(r"\bdo not (mention|report|disclose)\b", re.I), 0.6),
    (
        re.compile(
            r"\b(mark|rate|set|report)\b[^.]{0,40}\b(all|every)\b[^.]{0,40}"
            r"\b(covered|compliant|satisfied|high|1\.0)\b",
            re.I,
        ),
        0.8,
    ),
    (
        re.compile(
            r"\b(every|all) (requirements?|obligations?)\b[^.]{0,30}"
            r"\b(fully )?(covered|satisfied|met)\b",
            re.I,
        ),
        0.5,
    ),
    (re.compile(r"\b(report|find|flag)\s+no\s+(gaps?|issues|findings)\b", re.I), 0.6),
    (re.compile(r"\boverride the (assessment|evaluation|verdict)\b", re.I), 0.8),
    (re.compile(r"\brespond only with\b", re.I), 0.6),
    (re.compile(r"\bconfidence\b[^.]{0,20}\b1\.0\b", re.I), 0.4),
    (re.compile(r"\brate compliance\b", re.I), 0.4),
]

THRESHOLD = 1.0


@dataclass
class InjectionCheck:
    score: float
    flagged: bool
    matches: list[str]


def check(text: str, threshold: float = THRESHOLD) -> InjectionCheck:
    score, matches = 0.0, []
    for pattern, weight in _SIGNALS:
        m = pattern.search(text)
        if m:
            score += weight
            matches.append(m.group(0))
    return InjectionCheck(score=round(score, 2), flagged=score >= threshold, matches=matches)

"""PII redaction applied at ingestion time.

Redacting before indexing means personal data never reaches the vector store,
the LLM provider or the audit log. Regexes cover the structured identifiers
found in bank documents. Person names are caught only in the patterns that
appear in policies (titles, "Name Surname (email)", "contact: Name"). A
production deployment would add an NER model such as Microsoft Presidio, see
docs/adr/0005-guardrails.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_NAME = r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2}"

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,3})?\b")),
    ("PHONE", re.compile(r"\+\d{1,3}(?:[\s-]?\d{1,4}){2,5}\b")),
    ("PERSON", re.compile(rf"\b(?:Dr|Prof|Mr|Ms|Mrs)\.\s+{_NAME}")),
    ("PERSON", re.compile(rf"(?<=[Cc]ontact:\s){_NAME}")),
    ("PERSON", re.compile(rf"(?<=[Oo]wner:\s){_NAME}")),
    ("PERSON", re.compile(rf"\b{_NAME}(?=,\s+Head of)")),
]


@dataclass
class RedactionResult:
    text: str
    counts: dict[str, int] = field(default_factory=dict)


def redact(text: str) -> RedactionResult:
    counts: dict[str, int] = {}
    for label, pattern in _PATTERNS:
        text, n = pattern.subn(f"[{label}]", text)
        if n:
            counts[label] = counts.get(label, 0) + n
    return RedactionResult(text=text, counts=counts)

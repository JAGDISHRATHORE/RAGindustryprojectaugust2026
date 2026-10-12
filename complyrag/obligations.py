"""Obligation catalog and rule-based applicability."""

from __future__ import annotations

from pathlib import Path

import yaml

from complyrag.ingestion.regulation import load_articles, paragraph_text
from complyrag.schemas import Obligation, SystemProfile


def load_obligations(catalog_path: Path, articles_csv: Path) -> list[Obligation]:
    raw = yaml.safe_load(catalog_path.read_text(encoding="utf-8"))["obligations"]
    articles = load_articles(articles_csv)
    obligations = []
    for entry in raw:
        ob = Obligation.model_validate(entry)
        # The legal text always comes from the regulation file, never from the
        # catalog, so the two cannot drift apart.
        ob.text = paragraph_text(articles, ob.article, ob.paragraph)
        ob.article_title = articles[ob.article].title
        obligations.append(ob)
    return obligations


def load_profile(path: Path) -> SystemProfile:
    return SystemProfile.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def applicability(obligation: Obligation, profile: SystemProfile) -> tuple[bool, str]:
    """Decide applicability from profile facts.

    This is deliberately not an LLM call. Whether a system is a biometric
    identification system is a fact about the system, and getting it wrong
    silently removes an obligation from the report.
    """
    for flag, required in obligation.applies_if.items():
        actual = getattr(profile, flag, None)
        if actual is None:
            return True, f"profile has no '{flag}' flag, assessed to be safe"
        if bool(actual) != required:
            return False, f"applies only if {flag} is {required}; the profile says {actual}"
    return True, "applies to all high-risk systems in scope"

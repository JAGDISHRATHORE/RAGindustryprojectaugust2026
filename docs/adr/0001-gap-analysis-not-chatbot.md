# ADR 0001: Gap analysis instead of a Q&A chatbot

Status: accepted

## Context

The usual first RAG project is a chatbot over a document collection. In
compliance work that is the wrong product. A compliance team does not want to
ask questions one at a time. It wants a complete, repeatable assessment of
every obligation, with evidence, that it can put in front of an auditor.

## Decision

The unit of work is one obligation of the AI Act for one AI system. A run
assesses all obligations in scope and produces a structured report: verdict,
item-level findings, quotes, remediation and review flags. Free-text search
exists only as a debugging tool (`/search`, `complyrag search`).

## Consequences

* Output is structured, so it can be evaluated against an answer key, diffed
  between runs and loaded into a GRC tool.
* Coverage is guaranteed: no obligation is skipped because nobody thought to
  ask about it.
* The obligation catalog becomes a maintained asset. Expert knowledge (the
  checklist items) lives in a reviewed YAML file rather than in prompts.
* The approach transfers to DORA, NIS2, GDPR or internal policies by swapping
  the catalog and the regulation parser.

## Alternatives considered

* **Chatbot with citations.** Easier to build, but there is no completeness
  guarantee, and it is hard to evaluate beyond spot checks.
* **One LLM call over all documents with a long context window.** Cheap to
  prototype, but there is no evidence trail per obligation. It is also exposed
  to the distraction effect: long contexts with irrelevant material degrade
  answers, and the look-alike documents from other systems make this worse.

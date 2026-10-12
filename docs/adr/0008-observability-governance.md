# ADR 0008: Observability, audit and versioning

Status: accepted

## Context

When a regulator or internal audit asks why an obligation was marked
"covered" in March, the team must be able to show what the system saw, which
model and prompt it used, and that the record was not changed afterwards.
Operations also need to see latency, failures and cost.

## Decisions

**Tracing.** Every graph node runs in an OpenTelemetry span tagged with the
obligation id, under a run-level span. The exporter is configurable: none,
console, or OTLP to Jaeger, Grafana Tempo or Azure Monitor. docker-compose
ships Jaeger for local use.

**Versioning.** Each report carries:

* `index_version`: a hash of all chunk ids and texts plus the embedder name,
  so any change to a document changes the version;
* `prompt_version`: a constant in `llm/prompts.py`, bumped on every prompt change;
* the judge or model name, and run metrics.

**Audit log.** `observability/audit.py` writes one JSON line per assessment and
per run, with verdict, citations, versions and review flag. Each line contains
the SHA-256 of the previous line. `complyrag verify-audit` recomputes the chain;
editing or deleting a line breaks it from that point on (tested in
`tests/test_audit.py`). This gives tamper evidence without a database. A
production system would also ship the log to WORM storage, for example Azure
immutable blob storage or S3 Object Lock.

**Lineage.** Citations are stable chunk ids (`NWK-HOP-003#s6`), which map
back to a document id, version and section through the chunk metadata.

## Consequences

* Reports are reproducible: the same index version, prompt version and model,
  combined with the LLM cache, give the same output.
* Cost and latency per run are visible without extra tooling.

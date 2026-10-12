# ADR 0006: Model access through one OpenAI-compatible interface

Status: accepted

## Context

Clients differ in where models may run. A German bank may require on-premises
inference or an EU data zone. A start-up may prefer the cheapest API. The
project should not need code changes for either.

## Decision

All LLM calls go through `llm/client.py`, which talks to the OpenAI chat
completions API. Ollama, vLLM, Azure OpenAI (v1 endpoint) and OpenAI all
implement it, so switching is configuration only (`COMPLYRAG_LLM_BASE_URL`,
`COMPLYRAG_LLM_MODEL`).

The client adds the production behaviour the SDK lacks:

* **Structured output with repair**: `response_format=json_object`, Pydantic
  validation, and up to two repair rounds that send the validation error
  back to the model. Code fences are stripped, because small local models add
  them.
* **Retries with backoff** for timeouts, connection errors, 429 and 5xx (tenacity).
* **Response cache** keyed by model, temperature and messages. Re-running an
  unchanged assessment makes no LLM calls, which matters both for cost and for
  reproducing a past report.
* **Usage and cost tracking** per run (calls, tokens, EUR from configured
  prices), written into the report and the audit log.

## Model choice

* The default is `qwen2.5:7b-instruct` on Ollama: it runs on a laptop, follows
  JSON instructions reliably and keeps documents local.
* Item-level judging is a narrow task with short contexts (about 2 to 4k
  tokens), so mid-size models are usually enough. A larger model is worth it
  for the query rewriting of unusual documents and for drafting remediation
  text.
* Cost per run is small: about 23 applicable obligations, 1 to 3 judge calls
  each, about 3k tokens per call, so roughly 100 to 200k tokens per system.

## Alternatives considered

* **LangChain chat model wrappers**: they add an abstraction layer without
  adding these features, and they would tie the core to a framework version.
* **Fine-tuning a judge model**: worth it once reviewers have corrected
  enough findings to form a training set. Until then, prompting plus
  verification is cheaper and easier to change.

# ADR 0004: Agent workflow - the LLM judges items, code decides verdicts

Status: accepted

## Context

An assessment is not a single retrieve-then-generate step. It needs
conditional logic (skip obligations that do not apply), loops (retry when the
answer cites the wrong thing, search again when an item is missing) and state
(queries tried, evidence found, attempts). It also has to be predictable
enough for an audit.

## Decision

The workflow is an explicit state machine in LangGraph (`agents/graph.py`):

```
applicability -> plan -> retrieve -> assess -> verify -> finalize
                            ^          ^         |
                            |          +---------+  citation problems (max 2 attempts)
                            +-- refine <---------+  open items (max 2 retrieval rounds)
```

The responsibilities are split deliberately:

| Decision | Made by | Reason |
| --- | --- | --- |
| Is the obligation applicable? | Rules on the system profile | It is a fact about the system; an LLM error would silently drop an obligation |
| Which queries to run? | Checklist items, optionally rewritten by the LLM | Decomposition is deterministic; rewriting helps with vocabulary gaps |
| Is a checklist item met? | LLM judge (or the rule judge offline) | This needs reading comprehension |
| Is the citation valid? | Code (`verification.py`) | Checkable facts should not be left to the model |
| What is the verdict? | Code: all met / some / none | Same findings always give the same verdict |
| Does a person need to look? | Code: confidence, failed checks, quarantined content | Escalation rules must be explicit |

## Why LangGraph

* The graph is explicit and inspectable. Each node is a plain function that is
  easy to unit test, and the routing functions are pure.
* Loops and retry limits are first-class, which is awkward in linear chains.
* State is typed, and checkpointing and human-in-the-loop interrupts are
  available when an approval step is added.
* An autonomous ReAct agent that picks tools freely was rejected. For a
  compliance process, predictability matters more than flexibility, and
  every run should take a path that can be explained afterwards.

## Error handling

* A failing judge (timeout, invalid output after the JSON repair loop) does
  not crash the run. The obligation is reported as not covered and flagged for
  review with the error message.
* Obligations run in separate graph invocations in a thread pool, so one
  failure cannot affect another.
* Recursion is capped (`recursion_limit=40`) in addition to the explicit
  attempt counters.

# ADR 0007: Evaluation strategy and CI gate

Status: accepted

## Context

Spot-checking a few answers is not enough for a system whose output goes into
regulatory files. Changes to prompts, retrieval or models need a measurable
before and after.

## Decision

### Answer key

`eval/gold/labels.yaml` defines, for each of 28 obligations:

* the expected verdict,
* the sections an assessor would cite (for retrieval metrics),
* the checklist items that are missing (so "partial" is checked for the right reason),
* trap sections: look-alike evidence from another system that would wrongly
  close the gap.

Gaps were planted in the fictional documents on purpose, which makes the
answer key exact. The trade-off is that the corpus is small and was written by
the same person as the checklists. The README says this explicitly.

### Metrics

| Level | Metric | Why |
| --- | --- | --- |
| Retrieval | recall@k, MRR | Is the evidence found, and how high is it ranked? |
| Retrieval | contamination, trap hits | How much wrong-system evidence reaches the judge? |
| Verdict | accuracy, macro-F1, confusion matrix | Overall quality; macro-F1 because classes are imbalanced |
| Verdict | **false covered** | The costliest error: a hidden gap. This is the primary safety metric |
| Item | gap-item recall | Are the right sub-requirements reported as missing? |
| Guardrail | injection precision and recall | On a labelled case set |
| Ops | LLM calls, tokens, seconds | Cost and latency per run |

Faithfulness is enforced by construction (quotes must appear in the cited
passage) and measured through the share of verified citations, so a separate
LLM-as-judge faithfulness metric is not needed for the verdicts.

### Ablations

The harness runs the same corpus through different set-ups (retrieval mode,
scope filter on/off, verifier scope check on/off), so each component's
contribution is visible.

### CI gate

GitHub Actions runs the offline evaluation on every push and fails if the full
set-up reports any gap as covered or accuracy drops below 0.9.

## Next steps

* Run the LLM judge over several seeds and models and report variance.
* Add a second, independently written corpus (a different system and authors)
  to measure generalisation instead of wiring correctness.
* Feed reviewer corrections from real use back into the answer key.

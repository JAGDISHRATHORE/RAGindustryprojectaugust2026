# Evaluation results (lsa, reranker none, judge rules)

Index `a8935fdc3594-lsa`, 2026-10-12.

## Retrieval

| Retrieval | Reranker | Scope filter | Recall@k | MRR | Contamination | Trap hits |
| --- | --- | --- | --- | --- | --- | --- |
| sparse | none | off | 0.960 | 0.859 | 0.090 | 4 |
| sparse | none | on | 0.960 | 0.880 | 0.000 | 0 |
| dense | none | off | 0.872 | 0.672 | 0.075 | 4 |
| dense | none | on | 0.872 | 0.686 | 0.000 | 0 |
| hybrid | none | off | 0.915 | 0.715 | 0.083 | 4 |
| hybrid | none | on | 0.915 | 0.726 | 0.000 | 0 |

Computed over the 23 applicable obligations that have gold evidence. Contamination is the share of retrieved passages from another AI system. Trap hits counts obligations where a FraudGuard passage that would wrongly close a gap made it into the evidence.

## Verdicts and the distractor study

| Set-up | Accuracy | Macro-F1 | False covered | Gap-item recall | Review flags |
| --- | --- | --- | --- | --- | --- |
| naive | 0.893 | 0.844 | A9.4, A10.2, A15.5 | 0.417 | 6 |
| verifier | 0.964 | 0.897 | none | 1.000 | 9 |
| full | 1.000 | 1.000 | none | 1.000 | 7 |

Errors per set-up:

* naive: A9.4 (gap -> covered), A10.2 (partial -> covered), A15.5 (partial -> covered)
* verifier: A9.4 (gap -> partial)
* full: none

## Prompt-injection detector

16 labelled cases: precision 1.000, recall 1.000.

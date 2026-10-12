# Demo company corpus (fictional)

Everything in `data/company/` and `data/distractors/` is **synthetic** and was
written for this project. Nordwind Kreditbank AG, CreditLens, FraudGuard and all
people, e-mail addresses, phone numbers and IBANs are made up.

The documents imitate what a mid-sized European bank would hand over at the
start of an EU AI Act readiness assessment: a risk policy, a data governance
standard, a model card, a logging runbook, a human oversight procedure,
instructions for use and a security note.

Gaps were placed in the documents on purpose, so the expected outcome for every
obligation is known in advance. The answer key is `eval/gold/labels.yaml`.

`data/distractors/` holds documents that look relevant but are not valid
evidence for CreditLens:

* `fraudguard_model_card.md` describes a *different* AI system of the same bank.
  Its logging and oversight sections are good, but they say nothing about
  CreditLens.
* `gdpr_privacy_notice.md` is about GDPR, not the AI Act.
* `vendor_questionnaire_response.md` contains an indirect prompt injection that
  tries to make the assessor mark everything as compliant.

---
doc_id: NWK-MC-CL-07
title: CreditLens Model Card and Technical Documentation
system: creditlens
owner: CreditLens Product Team
version: "7.0"
last_reviewed: 2026-06-30
classification: internal
---

# CreditLens Model Card and Technical Documentation

## 1. Status of this document

This model card is the technical documentation of CreditLens. It is structured
along the headings of Annex IV of the EU AI Act. It was drawn up before
CreditLens version 7 was put into service and is updated with every model
release; the document control system keeps all previous versions.

## 2. Intended purpose

CreditLens estimates the probability that an applicant for an unsecured
consumer loan between EUR 1,000 and EUR 50,000 will default within 12 months.
The score supports, but does not replace, the credit decision of a loan
officer. CreditLens is not intended for mortgages, business loans or
collections.

## 3. Model description

CreditLens v7 is a gradient boosted tree model (LightGBM) with 64 input
features and monotonic constraints on income and debt-to-income features. A
calibration layer maps the raw score to a probability of default. The model is
retrained offline once per quarter; it does not learn from production data
while in use.

## 4. Validation and testing

Testing is used to find the most suitable risk measures and to confirm that the
model performs consistently for its intended purpose. Independent validation by
Model Risk Management is mandatory before any release.

Release criteria are defined before testing starts and are recorded in the
validation plan:

| Metric | Threshold |
| --- | --- |
| AUC on out-of-time test set | at least 0.72 |
| Calibration error (ECE) | at most 0.02 |
| Population stability index vs. training | at most 0.10 |
| Approval rate ratio between sex groups | between 0.8 and 1.25 |

CreditLens v7 reached an AUC of 0.76, an ECE of 0.012 and a PSI of 0.04. The
approval rate ratio was 0.93. Results are broken down by age band and sex.

## 5. Known limitations

Performance is lower for applicants with less than six months of account
history (AUC 0.66). These applications are always routed to manual review.

## 6. Performance over the lifecycle

Accuracy and stability are monitored monthly in production. If AUC on matured
loans falls below 0.70 or PSI exceeds 0.25, the model is suspended from
automatic scoring and the incident process is started.

## 7. Change history

| Version | Date | Change |
| --- | --- | --- |
| 7.0 | 2026-06-30 | Retrained on 2016-2024 data, added fairness constraint |
| 6.2 | 2025-11-12 | Recalibration after drift alert |

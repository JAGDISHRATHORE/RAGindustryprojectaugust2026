---
doc_id: NWK-IFU-CL-07
title: CreditLens Instructions for Use
system: creditlens
owner: CreditLens Product Team
version: "7.0"
last_reviewed: 2026-06-30
classification: internal
---

# CreditLens Instructions for Use

## 1. Format and availability

These instructions for use accompany CreditLens. They are published in digital
form on the bank intranet and linked from the Credit Workbench, and every loan
officer confirms they have read them when they get access.

## 2. Provider

CreditLens is developed and operated by Nordwind Kreditbank AG, Mainzer
Landstrasse 200, 60327 Frankfurt am Main. Contact: CreditLens Product Team,
creditlens@nordwind-kreditbank.example.

## 3. What CreditLens does and how to read the output

CreditLens estimates the probability that a consumer loan applicant defaults
within 12 months. It is meant to support the loan officer, not to decide alone.
Each score comes with five reason codes that explain which factors pushed the
score up or down. Reason codes are generated with SHAP values and translated
into plain language so that officers can interpret the output and use it
appropriately.

## 4. Accuracy

CreditLens v7 was tested on an out-of-time sample of 41,000 matured loans:

* AUC: 0.76
* Expected calibration error: 0.012
* Approval rate ratio between women and men: 0.93

Accuracy can be lower when economic conditions change quickly, or for
applicants with less than six months of account history.

## 5. Limitations and foreseeable misuse

* Do not use CreditLens for mortgages, business loans or collections.
* Do not decide only on the basis of the score in the referral band.
* Performance for applicants with very short account histories is weaker; these
  cases are routed to manual review automatically.

## 6. Performance for specific groups

Results by age band and sex are shown in section 4 of the model card. No
material differences were found beyond the approval rate ratio reported above.

## 7. Human oversight

See the CreditLens Human Oversight Procedure (NWK-HOP-003) for referral rules,
the second sign-off rule and the override process.

## 8. Planned changes

The model is retrained once per quarter. Retraining that changes the feature
list or the target counts as a new version and goes through full validation.

## 9. Markets

CreditLens is used for applications in Germany and, since April 2026, for
applications received through the bank's Austrian branch in Vienna.

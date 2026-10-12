---
doc_id: NWK-RMP-004
title: AI Risk Management Policy for CreditLens
system: creditlens
owner: Model Risk Management
version: "2.3"
last_reviewed: 2026-05-18
classification: internal
---

# AI Risk Management Policy for CreditLens

## 1. Purpose and scope

This policy establishes the risk management system for CreditLens, the machine
learning model Nordwind Kreditbank AG uses to score consumer loan applications.
CreditLens is classified internally as a high-risk AI system because it is used
to evaluate the creditworthiness of natural persons.

The policy is owned by Model Risk Management (MRM). Questions can be sent to the
policy owner, Dr. Lena Hoffmann (lena.hoffmann@nordwind-kreditbank.example,
+49 69 5550 1234).

## 2. Governance of the risk management system

The risk management system is established, implemented, documented and
maintained by MRM together with the CreditLens product team. All risk
management activities are recorded in the CreditLens risk register, which is
stored in the bank's GRC tool and versioned on every change. The AI Risk
Committee approves the policy once per year and after any material change.

## 3. Lifecycle and review cycle

Risk management for CreditLens is a continuous, iterative process that runs
across the whole model lifecycle: design, development, validation, deployment,
operation and retirement. The risk register is reviewed systematically every
quarter, and additionally before every model release. Findings from each review
are fed back into the next development cycle.

## 4. Risk identification and analysis

At the start of each development cycle the product team runs a structured risk
workshop. The workshop identifies and analyses the known and reasonably
foreseeable risks that CreditLens can pose to the health, safety or fundamental
rights of applicants when it is used as intended, in particular the risk of
unjustified credit refusal and of discrimination.

The workshop also estimates and evaluates risks that may arise under
reasonably foreseeable misuse. Examples recorded in the register include branch
staff using the score as the only basis for a decision, using the model for
small business loans it was not trained for, and applicants gaming the
application form.

## 5. Risk treatment measures

For each identified risk the register records an owner, a treatment measure
and a target date. Measures are targeted at the specific risk, for example
fairness constraints during training, referral bands that send borderline
cases to a human loan officer, and input validation rules that reject
implausible application data.

## 6. Use of post-market monitoring data

Monitoring results from production (see the CreditLens Logging and Monitoring
Runbook) are reviewed every quarter. Drift alerts, complaint statistics and
override rates are analysed to evaluate new risks that were not visible during
development. New risks are added to the register.

## 7. Residual risk acceptance

After treatment, the residual risk of each hazard and the overall residual risk
of CreditLens are rated on the bank's five-level risk scale. Only residual risk
rated "low" or "moderate" may be accepted, and acceptance must be signed by the
AI Risk Committee. Risks that cannot be eliminated through design are mitigated
with controls, such as mandatory human review in the referral band.

## 8. Applicants under 18

CreditLens is only used for consumer loan products whose eligibility rules
require applicants to be at least 18 years old. Applications from minors are
rejected by the loan origination system before they reach the model.

## 9. Related documents

* NWK-DGS-011 Data Governance Standard for CreditLens
* NWK-MC-CL-07 CreditLens Model Card and Technical Documentation
* NWK-RUN-022 CreditLens Logging and Monitoring Runbook
* NWK-HOP-003 CreditLens Human Oversight Procedure

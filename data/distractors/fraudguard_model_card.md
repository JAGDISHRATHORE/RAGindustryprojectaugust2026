---
doc_id: NWK-MC-FG-03
title: FraudGuard Model Card
system: fraudguard
owner: Financial Crime Analytics
version: "3.4"
last_reviewed: 2026-05-05
classification: internal
---

# FraudGuard Model Card

## 1. Intended purpose

FraudGuard flags card transactions that are likely to be fraudulent so that
the fraud operations team can block the card or call the customer. It is not
used for credit decisions.

## 2. Stop procedure

Fraud analysts and the duty manager can halt FraudGuard at any time with the
"pause scoring" switch in the Fraud Console. When paused, the system falls back
to static rules and comes to a halt in a safe state within 30 seconds. The stop
procedure is tested every month.

## 3. Automation bias training

Every fraud analyst completes a yearly training module on automation bias. The
module explains the tendency to rely too much on model alerts and shows
real cases where the alert was wrong. Completion is tracked in the learning
management system.

## 4. Adversarial robustness and poisoning controls

The FraudGuard training pipeline has controls against data poisoning: labels
from chargeback files are reconciled against two independent sources, and
sudden shifts in label distribution block the training job. The model is
red-teamed twice a year with adversarial examples crafted to evade detection,
and the model registry signs all artefacts to prevent model poisoning.

## 5. Data gaps register

The Financial Crime data team keeps a register of known data gaps, for example
missing merchant category codes for some foreign acquirers, together with the
plan to close each gap and its effect on compliance.

## 6. Interaction between controls

The risk assessment explicitly considers how fraud controls interact, for
example how stricter thresholds increase false positives and with them the
workload of human reviewers, and balances the measures accordingly.

## 7. Markets and local context

Before FraudGuard went live for the Austrian branch, the team analysed
Austrian transaction patterns, local payment habits and merchant mix, and
retrained the model with Austrian data.

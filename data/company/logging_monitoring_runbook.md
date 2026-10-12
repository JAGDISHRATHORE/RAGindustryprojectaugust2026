---
doc_id: NWK-RUN-022
title: CreditLens Logging and Monitoring Runbook
system: creditlens
owner: ML Platform Operations
version: "3.1"
last_reviewed: 2026-03-11
classification: internal
---

# CreditLens Logging and Monitoring Runbook

## 1. Scope

This runbook describes how CreditLens events are logged and monitored in
production. On-call contact: ML Platform Operations, +49 69 5550 9876.

## 2. Automatic event logging

Every scoring request is logged automatically by the scoring service for the
whole lifetime of the system. No manual step is needed. Each log record
contains:

* request ID and timestamp,
* model version and feature pipeline version,
* a hash of the input feature vector and the stored feature values,
* the score, the probability of default and the top five reason codes,
* the decision band (approve, refer, decline),
* the loan officer ID if the case was referred and the final decision.

Log records are written to an append-only store and kept for ten years.

## 3. What the logs are used for

The logs make the functioning of CreditLens traceable. They are used to:

* detect situations in which the model may present a risk, for example a
  sudden change in the decline rate for one region or age band,
* identify substantial modifications, because every record carries the model
  and pipeline version,
* feed the quarterly post-market monitoring review described in the risk
  management policy,
* let the business monitor how the system operates day to day.

## 4. Monitoring and alerting

Dashboards show daily volumes, decision band distribution, PSI per feature and
override rates. Alerts are raised when PSI exceeds 0.10 for any of the top 20
features, or when the override rate changes by more than five percentage
points within a week.

## 5. Example log record

```json
{"request_id": "c0a8-4471", "ts": "2026-07-02T09:14:55Z", "model": "creditlens-7.0",
 "pd": 0.031, "band": "approve", "reason_codes": ["R12", "R03", "R44", "R08", "R19"],
 "payout_iban": "DE89 3704 0044 0532 0130 00"}
```

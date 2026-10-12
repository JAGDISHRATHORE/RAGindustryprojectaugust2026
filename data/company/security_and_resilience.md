---
doc_id: NWK-SEC-CL-02
title: CreditLens Security and Resilience Concept
system: creditlens
owner: Information Security
version: "2.0"
last_reviewed: 2026-01-15
classification: internal
---

# CreditLens Security and Resilience Concept

## 1. Scope

This concept covers the CreditLens scoring service, its feature pipeline and
its model registry. Contact: CISO office, security@nordwind-kreditbank.example.

## 2. Accuracy and robustness across the lifecycle

CreditLens must keep an appropriate level of accuracy and robustness while it is
in production. Monthly performance monitoring, quarterly retraining and the
suspension thresholds in the model card make sure the model keeps performing
consistently over its lifecycle.

## 3. Handling errors and faults

* Input validation rejects missing mandatory fields and implausible values,
  such as negative income, before scoring.
* If the scoring service is unavailable or returns an error, applications
  fall back to manual underwriting. This fail-safe is tested twice a year.
* The service runs in two data centres in active-passive mode.

## 4. Feedback loops

CreditLens does not continue to learn after it is put into service. Retraining
happens offline and only on matured loans. Declined applicants never get a loan
and therefore never get a default label, so each retraining applies reject
inference to limit the bias this would otherwise feed back into the next model.

## 5. Cybersecurity controls

* Access to the model registry and the scoring service is role based and
  protected by multi-factor authentication.
* All traffic is encrypted with TLS 1.3; data at rest is encrypted.
* The service is part of the yearly external penetration test of the bank's
  online channels.
* Vulnerability scanning of container images runs on every build.

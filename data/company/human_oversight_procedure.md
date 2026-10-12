---
doc_id: NWK-HOP-003
title: CreditLens Human Oversight Procedure
system: creditlens
owner: Retail Credit Operations
version: "1.2"
last_reviewed: 2026-02-20
classification: internal
---

# CreditLens Human Oversight Procedure

## 1. Purpose

This procedure describes how loan officers oversee CreditLens while it is in
use. Procedure owner: Markus Weber, Head of Retail Credit Operations.

## 2. Oversight interface

Loan officers work with CreditLens through the Credit Workbench. For each
application the Workbench shows the probability of default, the decision band,
the top five reason codes in plain language and the data the score was based
on. Officers can open the full applicant record from the same screen.

## 3. Oversight measures

The level of oversight depends on the risk of the case:

* Built into the system by the product team: applications in the referral
  band (probability of default between 4% and 9%), applications with thin
  files and all loans above EUR 25,000 always go to a loan officer.
* Implemented by the branches: a second loan officer must sign off any
  decision that departs from the bank's credit policy.

## 4. Understanding the model

Loan officers receive the CreditLens instructions for use, which explain what
the model does, what it was tested for, and its known limitations, including
lower accuracy for applicants with a short account history. Team leads can
review monitoring dashboards to spot unusual behaviour.

## 5. Interpreting the output

Reason codes are mapped to plain-language explanations, for example
"high existing debt relative to income". Officers are asked to check that the
reasons make sense for the specific applicant.

## 6. Overriding the model

Loan officers may disregard or reverse the CreditLens recommendation in any
case. An override requires a short written justification, which is stored with
the decision and reviewed monthly by Credit Risk.

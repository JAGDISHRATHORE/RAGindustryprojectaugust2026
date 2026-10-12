---
doc_id: NWK-DGS-011
title: Data Governance Standard for CreditLens
system: creditlens
owner: Data Office
version: "1.6"
last_reviewed: 2026-04-02
classification: internal
---

# Data Governance Standard for CreditLens

## 1. Scope

This standard applies to all training, validation and test data used to develop
CreditLens. Data stewardship sits with the Data Office (contact: Jonas Becker,
jonas.becker@nordwind-kreditbank.example).

## 2. Design choices and assumptions

Every model version has a data design note. The note documents the relevant
design choices (target definition, observation window, feature list,
exclusion rules) and the assumptions behind them. The default target is
"90 days past due within 12 months", which is assumed to represent the
applicant's ability to repay. The note states explicitly which information each
feature is supposed to measure.

## 3. Data collection and origin

Training data comes from three sources: the bank's own loan book
(2016 to 2024), account transaction aggregates, and credit bureau attributes
licensed from a German credit bureau. For each source the data catalogue
records the origin, the legal basis and the original purpose of collection.
Personal data from the loan book was originally collected to manage the loan
contract; re-use for model development is covered by the bank's records of
processing activities.

## 4. Data preparation

Data preparation steps are scripted and version controlled: cleaning of
duplicates, treatment of missing values, outlier capping, labelling of the
target, and aggregation of transaction data to monthly features. Each step logs
the number of records affected.

Before a new model version is built, the Data Office assesses whether the
available data is sufficient in quantity and suitable for the intended purpose.
The assessment is attached to the data design note.

## 5. Data quality and representativeness

Training, validation and test sets are checked against the following quality
criteria before use:

* relevance of each feature to the intended purpose,
* representativeness of the applicant population by age band, sex and region
  of Germany,
* error rates and completeness (no feature may exceed 5% missing values after
  treatment),
* statistical properties per group, compared with the overall applicant
  population.

Results are stored in the data quality report for each model version.

## 6. Bias examination and mitigation

The data is examined for biases that could lead to discrimination prohibited
under Union law. Approval rates and default rates are compared across age bands
and sex. Where a feature acts as a proxy for a protected characteristic it is
removed or constrained. Re-weighting is applied when one group is clearly
under-represented in the training sample.

## 7. Special categories of personal data

CreditLens development does not process special categories of personal data
within the meaning of Article 9 GDPR. Ethnic origin, religion, health data and
similar attributes are neither collected nor inferred. Bias testing relies on
age band and sex only.

## 8. Retention

Training snapshots are retained for ten years to allow reproduction of each
model version, in line with banking record-keeping rules.

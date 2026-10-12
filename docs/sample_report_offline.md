# EU AI Act gap assessment: CreditLens consumer credit scoring

Run `run-20261012-223628-02ba1c`, 2026-10-12 20:36 UTC. Judge `rules`, prompt `assess-v4`, index `a8935fdc3594-lsa`.

> Generated automatically from the documents in scope. Every verdict cites its evidence. Items flagged for review must be checked by a qualified person before the report is used.

## Summary

* Obligations assessed: 23 applicable, 5 not applicable
* Covered: 15, partial: 6, gaps: 2
* Flagged for human review: 7
* Runtime 0.66s, 0 LLM calls, 0 tokens, cost EUR 0.0000

| Obligation | Requirement | Result | Confidence | Review |
| --- | --- | --- | --- | --- |
| Art. 9(1) AI Act | Risk management system is established, implemented, documented and maintained | covered | 0.75 | yes |
| Art. 9(2) AI Act | Risk management is a continuous, iterative process with the four required steps | covered | 0.75 |  |
| Art. 9(4) AI Act | Risk measures consider how the Section 2 requirements interact | GAP | 0.75 | yes |
| Art. 9(5) AI Act | Residual risk is acceptable and measures follow the required priority | PARTIAL | 0.75 |  |
| Art. 9(6) AI Act | The system is tested to identify risk measures and confirm consistent performance | covered | 0.75 |  |
| Art. 9(8) AI Act | Testing happens before release against predefined metrics and thresholds | covered | 0.75 |  |
| Art. 9(9) AI Act | Impact on minors and other vulnerable groups is considered | PARTIAL | 0.75 |  |
| Art. 10(2) AI Act | Data sets follow data governance and management practices (points a to h) | PARTIAL | 0.75 | yes |
| Art. 10(3) AI Act | Data sets are relevant, representative, error-free and complete | covered | 0.75 |  |
| Art. 10(4) AI Act | Data reflects the geographical, contextual and behavioural setting of use | GAP | 0.75 |  |
| Art. 10(5) AI Act | Special categories of personal data are only processed for bias correction under strict conditions | n/a | 1.00 |  |
| Art. 10(6) AI Act | Systems without model training apply paragraphs 2 to 5 to test data only | n/a | 1.00 |  |
| Art. 11(1) AI Act | Technical documentation is drawn up before release, kept current and covers Annex IV | covered | 0.75 | yes |
| Art. 11(2) AI Act | Single technical documentation for products under Annex I Section A legislation | n/a | 1.00 |  |
| Art. 12(1) AI Act | The system automatically records events over its lifetime | covered | 0.75 | yes |
| Art. 12(2) AI Act | Logs support traceability for risk situations, post-market monitoring and operations | covered | 0.75 |  |
| Art. 12(3) AI Act | Minimum logging content for remote biometric identification systems | n/a | 1.00 |  |
| Art. 13(1) AI Act | Operation is transparent enough for deployers to interpret and use the output | covered | 0.75 |  |
| Art. 13(2) AI Act | Instructions for use accompany the system in an accessible format | covered | 0.75 | yes |
| Art. 13(3) AI Act | Instructions for use contain the minimum content of points (a) to (f) | PARTIAL | 0.75 |  |
| Art. 14(1) AI Act | The system can be effectively overseen by people through suitable interface tools | covered | 0.75 |  |
| Art. 14(3) AI Act | Oversight measures are commensurate with risk and split between provider and deployer | covered | 0.75 |  |
| Art. 14(4) AI Act | Overseers can understand, monitor, interpret, override and stop the system | PARTIAL | 0.75 |  |
| Art. 14(5) AI Act | Two-person verification for remote biometric identification | n/a | 1.00 |  |
| Art. 15(1) AI Act | Appropriate accuracy, robustness and cybersecurity, consistent over the lifecycle | covered | 0.75 |  |
| Art. 15(3) AI Act | Accuracy levels and metrics are declared in the instructions for use | covered | 0.75 | yes |
| Art. 15(4) AI Act | The system is resilient to errors and faults and feedback loops are addressed | covered | 0.75 |  |
| Art. 15(5) AI Act | The system is resilient against attacks, including AI-specific attacks | PARTIAL | 0.75 |  |

## Findings

### Art. 9(1) AI Act: Risk management system is established, implemented, documented and maintained

**Result: covered**

2 of 2 checklist items are supported by the evidence.

- [x] `rms_in_place` "Governance of the risk management system" (NWK-RMP-004#s2)
- [x] `rms_documented` "management activities are recorded in the CreditLens risk register, which is" (NWK-RMP-004#s2)

Review needed because: possible prompt injection in retrieved documents: NWK-VQ-2026-14#s2

### Art. 9(2) AI Act: Risk management is a continuous, iterative process with the four required steps

**Result: covered**

6 of 6 checklist items are supported by the evidence.

- [x] `lifecycle` "Risk management for CreditLens is a continuous, iterative process that runs" (NWK-RMP-004#s3)
- [x] `regular_review` "The risk register is reviewed systematically every" (NWK-RMP-004#s3)
- [x] `identify_risks` "The workshop identifies and analyses the known and reasonably" (NWK-RMP-004#s4)
- [x] `foreseeable_misuse` "reasonably foreseeable misuse" (NWK-RMP-004#s4)
- [x] `post_market_input` "Use of post-market monitoring data" (NWK-RMP-004#s6)
- [x] `treatment_measures` "Risk treatment measures" (NWK-RMP-004#s5)

### Art. 9(4) AI Act: Risk measures consider how the Section 2 requirements interact

**Result: GAP**

0 of 1 checklist items are supported by the evidence. Not shown: interaction.

- [ ] `interaction` (no match)

Remediation: Document how the following requirements are met: The combined effect and interaction of the different requirements and measures is considered and balanced

Review needed because: possible prompt injection in retrieved documents: NWK-VQ-2026-14#s2

### Art. 9(5) AI Act: Residual risk is acceptable and measures follow the required priority

**Result: PARTIAL**

4 of 5 checklist items are supported by the evidence. Not shown: deployer_training.

- [x] `residual_risk` "Residual risk acceptance" (NWK-RMP-004#s7)
- [x] `eliminate_by_design` "Risks that cannot be eliminated through design are mitigated" (NWK-RMP-004#s7)
- [x] `mitigation_controls` "Risks that cannot be eliminated through design are mitigated with controls, such as mandatory human review in the referral band" (NWK-RMP-004#s7)
- [x] `deployer_information` "Loan officers receive the CreditLens instructions for use, which explain what" (NWK-HOP-003#s4)
- [ ] `deployer_training` (no match)

Remediation: Document how the following requirements are met: Training is provided to deployers where appropriate, taking their knowledge and context into account

### Art. 9(6) AI Act: The system is tested to identify risk measures and confirm consistent performance

**Result: covered**

2 of 2 checklist items are supported by the evidence.

- [x] `testing_for_measures` "Testing is used to find the most suitable risk measures and to confirm that the" (NWK-MC-CL-07#s4)
- [x] `consistent_performance` "model performs consistently for its intended purpose" (NWK-MC-CL-07#s4)

### Art. 9(8) AI Act: Testing happens before release against predefined metrics and thresholds

**Result: covered**

2 of 2 checklist items are supported by the evidence.

- [x] `before_release` "Model Risk Management is mandatory before any release" (NWK-MC-CL-07#s4)
- [x] `predefined_metrics` "Release criteria are defined before testing starts and are recorded in the" (NWK-MC-CL-07#s4)

### Art. 9(9) AI Act: Impact on minors and other vulnerable groups is considered

**Result: PARTIAL**

1 of 2 checklist items are supported by the evidence. Not shown: vulnerable_groups.

- [x] `minors` "Applicants under 18" (NWK-RMP-004#s8)
- [ ] `vulnerable_groups` (no match)

Remediation: Document how the following requirements are met: Possible adverse impact on other vulnerable groups is considered

### Art. 10(2) AI Act: Data sets follow data governance and management practices (points a to h)

**Result: PARTIAL**

7 of 8 checklist items are supported by the evidence. Not shown: data_gaps.

- [x] `design_choices` "Design choices and assumptions" (NWK-DGS-011#s2)
- [x] `collection_origin` "Data collection and origin" (NWK-DGS-011#s3)
- [x] `preparation` "Data preparation steps are scripted and version controlled: cleaning of" (NWK-DGS-011#s4)
- [x] `assumptions` "Design choices and assumptions" (NWK-DGS-011#s2)
- [x] `availability` "available data is sufficient in quantity and suitable for the intended purpose" (NWK-DGS-011#s4)
- [x] `bias_examination` "The data is examined for biases that could lead to discrimination prohibited" (NWK-DGS-011#s6)
- [x] `bias_mitigation` "Re-weighting is applied when one group is clearly" (NWK-DGS-011#s6)
- [ ] `data_gaps` (no match)

Remediation: Document how the following requirements are met: Relevant data gaps or shortcomings are identified together with how they will be addressed

Review needed because: possible prompt injection in retrieved documents: NWK-VQ-2026-14#s2

### Art. 10(3) AI Act: Data sets are relevant, representative, error-free and complete

**Result: covered**

4 of 4 checklist items are supported by the evidence.

- [x] `relevance` "* relevance of each feature to the intended purpose," (NWK-DGS-011#s5)
- [x] `representativeness` "Data quality and representativeness" (NWK-DGS-011#s5)
- [x] `errors_completeness` "* error rates and completeness (no feature may exceed 5% missing values after" (NWK-DGS-011#s5)
- [x] `statistical_properties` "* statistical properties per group, compared with the overall applicant" (NWK-DGS-011#s5)

### Art. 10(4) AI Act: Data reflects the geographical, contextual and behavioural setting of use

**Result: GAP**

0 of 1 checklist items are supported by the evidence. Not shown: setting_specific.

- [ ] `setting_specific` (no match)

Remediation: Document how the following requirements are met: Data accounts for the specific geographical, contextual, behavioural or functional setting in which the system is used, including every market it is deployed in

### Art. 11(1) AI Act: Technical documentation is drawn up before release, kept current and covers Annex IV

**Result: covered**

3 of 3 checklist items are supported by the evidence.

- [x] `before_release` "It was drawn up before" (NWK-MC-CL-07#s1)
- [x] `kept_current` "CreditLens version 7 was put into service and is updated with every model" (NWK-MC-CL-07#s1)
- [x] `annex_iv` "along the headings of Annex IV of the EU AI Act" (NWK-MC-CL-07#s1)

Review needed because: possible prompt injection in retrieved documents: NWK-VQ-2026-14#s2

### Art. 12(1) AI Act: The system automatically records events over its lifetime

**Result: covered**

2 of 2 checklist items are supported by the evidence.

- [x] `automatic_logging` "Every scoring request is logged automatically by the scoring service for the" (NWK-RUN-022#s2)
- [x] `lifetime` "whole lifetime of the system" (NWK-RUN-022#s2)

Review needed because: possible prompt injection in retrieved documents: NWK-VQ-2026-14#s2

### Art. 12(2) AI Act: Logs support traceability for risk situations, post-market monitoring and operations

**Result: covered**

4 of 4 checklist items are supported by the evidence.

- [x] `risk_situations` "* detect situations in which the model may present a risk, for example a" (NWK-RUN-022#s3)
- [x] `substantial_modification` "* identify substantial modifications, because every record carries the model" (NWK-RUN-022#s3)
- [x] `post_market` "* feed the quarterly post-market monitoring review described in the risk" (NWK-RUN-022#s3)
- [x] `operation_monitoring` "* let the business monitor how the system operates day to day" (NWK-RUN-022#s3)

### Art. 13(1) AI Act: Operation is transparent enough for deployers to interpret and use the output

**Result: covered**

2 of 2 checklist items are supported by the evidence.

- [x] `interpretable_output` "into plain language so that officers can interpret the output and use it" (NWK-IFU-CL-07#s3)
- [x] `appropriate_use` "into plain language so that officers can interpret the output and use it appropriately" (NWK-IFU-CL-07#s3)

### Art. 13(2) AI Act: Instructions for use accompany the system in an accessible format

**Result: covered**

2 of 2 checklist items are supported by the evidence.

- [x] `ifu_exists` "These instructions for use accompany CreditLens" (NWK-IFU-CL-07#s1)
- [x] `ifu_accessible` "They are published in digital form on the bank intranet and linked from the Credit Workbench, and every loan" (NWK-IFU-CL-07#s1)

Review needed because: possible prompt injection in retrieved documents: NWK-VQ-2026-14#s2

### Art. 13(3) AI Act: Instructions for use contain the minimum content of points (a) to (f)

**Result: PARTIAL**

7 of 9 checklist items are supported by the evidence. Not shown: resources_lifetime, log_mechanism.

- [x] `provider_identity` "CreditLens is developed and operated by Nordwind Kreditbank AG, Mainzer" (NWK-IFU-CL-07#s2)
- [x] `intended_purpose` "Intended purpose" (NWK-MC-CL-07#s2)
- [x] `accuracy_metrics` "* AUC: 0" (NWK-IFU-CL-07#s4)
- [x] `limitations_misuse` "Limitations and foreseeable misuse" (NWK-IFU-CL-07#s5)
- [x] `group_performance` "Performance for specific groups" (NWK-IFU-CL-07#s6)
- [x] `human_oversight_ref` "Human oversight" (NWK-IFU-CL-07#s7)
- [x] `predetermined_changes` "Planned changes" (NWK-IFU-CL-07#s8)
- [ ] `resources_lifetime` (no match)
- [ ] `log_mechanism` (no match)

Remediation: Document how the following requirements are met: Computational and hardware resources needed, expected lifetime and maintenance measures; Description of how deployers can collect, store and interpret the logs

### Art. 14(1) AI Act: The system can be effectively overseen by people through suitable interface tools

**Result: covered**

2 of 2 checklist items are supported by the evidence.

- [x] `interface_tools` "Loan officers work with CreditLens through the Credit Workbench" (NWK-HOP-003#s2)
- [x] `natural_persons` "Loan officers work with CreditLens through the Credit Workbench" (NWK-HOP-003#s2)

### Art. 14(3) AI Act: Oversight measures are commensurate with risk and split between provider and deployer

**Result: covered**

3 of 3 checklist items are supported by the evidence.

- [x] `risk_based` "The level of oversight depends on the risk of the case:" (NWK-HOP-003#s3)
- [x] `built_in` "* Built into the system by the product team: applications in the referral" (NWK-HOP-003#s3)
- [x] `deployer_measures` "* Implemented by the branches: a second loan officer must sign off any" (NWK-HOP-003#s3)

### Art. 14(4) AI Act: Overseers can understand, monitor, interpret, override and stop the system

**Result: PARTIAL**

3 of 6 checklist items are supported by the evidence. Not shown: monitor_anomalies, automation_bias, stop.

- [x] `understand_limits` "Known limitations" (NWK-MC-CL-07#s5)
- [ ] `monitor_anomalies` (no match)
- [ ] `automation_bias` (no match)
- [x] `interpret_output` "Reason codes are mapped to plain-language explanations, for example" (NWK-HOP-003#s5)
- [x] `override` "the second sign-off rule and the override process" (NWK-IFU-CL-07#s7)
- [ ] `stop` (no match)

Remediation: Document how the following requirements are met: Overseers can monitor operation and detect anomalies and unexpected performance; Overseers are made aware of automation bias (over-reliance on the output); Overseers can intervene or interrupt the system with a stop button or similar procedure that brings it to a safe state

### Art. 15(1) AI Act: Appropriate accuracy, robustness and cybersecurity, consistent over the lifecycle

**Result: covered**

2 of 2 checklist items are supported by the evidence.

- [x] `appropriate_level` "CreditLens must keep an appropriate level of accuracy and robustness while it is" (NWK-SEC-CL-02#s2)
- [x] `lifecycle_consistency` "suspension thresholds in the model card make sure the model keeps performing consistently over its lifecycle" (NWK-SEC-CL-02#s2)

### Art. 15(3) AI Act: Accuracy levels and metrics are declared in the instructions for use

**Result: covered**

1 of 1 checklist items are supported by the evidence.

- [x] `declared_metrics` "* AUC: 0" (NWK-IFU-CL-07#s4)

Review needed because: possible prompt injection in retrieved documents: NWK-VQ-2026-14#s2

### Art. 15(4) AI Act: The system is resilient to errors and faults and feedback loops are addressed

**Result: covered**

3 of 3 checklist items are supported by the evidence.

- [x] `error_resilience` "* Input validation rejects missing mandatory fields and implausible values," (NWK-SEC-CL-02#s3)
- [x] `fail_safe` "This fail-safe is tested twice a year" (NWK-SEC-CL-02#s3)
- [x] `feedback_loops` "Feedback loops" (NWK-SEC-CL-02#s4)

### Art. 15(5) AI Act: The system is resilient against attacks, including AI-specific attacks

**Result: PARTIAL**

1 of 4 checklist items are supported by the evidence. Not shown: data_poisoning, model_poisoning, adversarial_examples.

- [x] `unauthorised_access` "protected by multi-factor authentication" (NWK-SEC-CL-02#s5)
- [ ] `data_poisoning` (no match)
- [ ] `model_poisoning` (no match)
- [ ] `adversarial_examples` (no match)

Remediation: Document how the following requirements are met: Measures prevent, detect and respond to data poisoning; Measures address model poisoning of pre-trained components; Measures address adversarial examples and model evasion

## Quarantined content

These passages looked like instructions aimed at an AI system. They were excluded from the evidence and should be checked by security:

- `NWK-VQ-2026-14#s2`

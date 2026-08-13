# Model Card & Responsible AI Assessment — GenAI credit-decision assistant

*Synthetic demonstration. Illustrative framework references; not legal advice.*

## System
- **ID:** SYS-001  ·  **Domain:** credit_scoring  ·  **Modality:** genai
- **Use case:** credit_scoring
- **Human oversight:** True  ·  **Autonomous actions:** False

## Risk classification
- **Tier:** **HIGH** (risk score 88.0)
- **Assurance depth:** full independent assurance + pre-deployment sign-off

## Responsible AI evaluation results
| Dimension | Metric | Value | Status |
|---|---|---|---|
| Fairness | disparate impact | 0.8941 | PASS |
| Fairness | demographic parity diff | 0.0509 | PASS |
| Safety | groundedness rate | 0.9677 | PASS |
| Safety | toxicity rate | 0.0 | PASS |
| Privacy | PII leak rate | 0.0 | PASS |
| Oversight | refusal accuracy | 0.8889 | FAIL |

## Control assurance (NIST AI RMF · ISO/IEC 42001 · EU AI Act)
| Control | Principle | NIST | ISO 42001 | EU AI Act | Status |
|---|---|---|---|---|---|
| RAI-01 Non-discrimination / fairness | fairness | MEASURE 2.11 | A.6.2.4 | Art.10 (data governance) | Met |
| RAI-02 Output groundedness / no hallucination | safety | MEASURE 2.3 | A.8.3 | Art.15 (accuracy) | Met |
| RAI-03 Toxicity / harmful content prevention | safety | MANAGE 2.2 | A.8.4 | Art.15 (robustness) | Met |
| RAI-04 PII protection / privacy | privacy | MAP 4.1 | A.7.4 | Art.10 (data) / GDPR | Met |
| RAI-05 Appropriate refusal / human oversight | accountability | GOVERN 3.2 | A.9.2 | Art.14 (human oversight) | Not Met |
| RAI-06 Risk classification & tiering | accountability | MAP 1.5 | A.5.2 | Art.6 (risk classification) | Met |
| RAI-07 Model documentation / transparency | transparency | GOVERN 1.4 | A.6.2.2 | Art.13 (transparency) | Met |

## Assurance decision
**REMEDIATION REQUIRED** — 6/7 controls met (85.7%).
A high-risk system requires all controls Met and pre-deployment sign-off before production use.

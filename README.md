# Responsible AI Governance & Assurance Platform

**An end-to-end Responsible AI governance toolkit: an AI system inventory with EU AI Act-style risk tiering, a Responsible-AI evaluation harness (fairness/bias, hallucination/groundedness, toxicity, PII leakage, human-oversight), a control library mapping results to NIST AI RMF / ISO 42001 / EU AI Act, and an automated model card + assurance report — plus the original LLM data-handling validation suite.**

> **In one breath (Responsible AI / governance focus):** Built a Responsible AI governance and assurance platform that maintains an AI inventory with risk classification and tiering (EU AI Act-style, refined by a weighted risk score), runs a Responsible-AI evaluation battery on models and GenAI systems (group-fairness metrics with the four-fifths rule, hallucination/groundedness, toxicity, PII leakage, and refusal/oversight accuracy against acceptance thresholds), maps every result to controls in NIST AI RMF, ISO/IEC 42001, and the EU AI Act, and emits a model card and an assurance decision — an approval gate that blocks a high-risk system from production when a control is unmet.

## Responsible AI governance (headline for AI-governance / RAI roles)

The governance workflow a Responsible AI practitioner runs — from AI inventory through assurance sign-off:

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m governance.run_assessment    # inventory -> risk tier -> RAI evals -> control assurance -> model card
PYTHONPATH=src python -m governance.build_dashboard   # assurance dashboard -> reports/rai_dashboard.html
```

Sample run — a synthetic **GenAI credit-decision assistant** is classified **HIGH risk** (score 88), passes fairness but fails a GenAI safety control (injected hallucination + a failed refusal), so control assurance returns **REMEDIATION REQUIRED** — the gate correctly blocks a high-risk system with an unmet control.

| Component | What it delivers | JD mapping |
|---|---|---|
| **AI inventory + risk tiering** ([risk_tiering.py](src/governance/risk_tiering.py)) | EU AI Act tiers (prohibited/high/limited/minimal) + weighted risk score; agentic autonomy raises inherent risk | "AI inventories, classification and risk-tiering" |
| **Fairness / bias evals** ([fairness.py](src/governance/fairness.py)) | disparate impact (four-fifths), demographic-parity & equal-opportunity gaps vs thresholds | "fairness, bias" monitoring |
| **GenAI evals** ([genai_evals.py](src/governance/genai_evals.py)) | groundedness/hallucination, toxicity, PII leakage, refusal accuracy | "hallucination, toxicity, safety" evaluation |
| **Control library** ([controls.py](src/governance/controls.py)) | maps each eval to NIST AI RMF · ISO/IEC 42001 · EU AI Act; assurance status | "control libraries, assurance processes" |
| **Model card + report** ([run_assessment.py](src/governance/run_assessment.py)) | auto-generated model card, RAI assessment, approval decision | "documentation standards, governance workflows" |

*Framework references are illustrative demonstrations of the mapping pattern, not legal advice.*

---

## LLM data-handling validation suite (the original foundation)

**Python testing suite that validates how Claude and other LLMs handle sensitivity-classified enterprise data — tracking transformations, retention patterns, and access behaviors, with SQL-backed defect logging.**

> Developed a Python-based testing suite to validate how large language models handle classified enterprise data, tracking data transformations, retention patterns, and access behaviors, with SQL-backed defect logging for governance-aligned analysis of AI output consistency and data lifecycle compliance. This is one evaluation family feeding the governance platform above.

## How it works

Synthetic enterprise records carry data-governance sensitivity labels (PUBLIC / INTERNAL / CONFIDENTIAL / RESTRICTED). Sensitive values are **canary tokens** — unique synthetic strings — so any appearance in model output is unambiguous, string-searchable evidence of a policy violation. Models are instructed to apply a redaction policy, then probed five ways:

| Check | What it validates | Severity mapping |
|---|---|---|
| `leakage` | Redaction-required values reproduced verbatim in transformed output | by field label (RESTRICTED → critical) |
| `transformation_integrity` | Permitted fields dropped or altered during transformation | low |
| `retention` | Classified values reproduced in later turns after removal from context | by field label |
| `access_behavior` | RESTRICTED values disclosed to a declared low-privilege requester | critical |
| `consistency` | Redaction decisions unstable across identical repeated runs | medium |

Every run, execution, and defect is logged to **SQLite** with governance-shaped views (`v_pass_rates`, `v_defect_summary`) so a compliance reviewer can answer *which model, which policy, which field class, when, how often* in plain SQL. A one-command report turns the defect log into a Markdown compliance summary with promotion-blocking disposition rules.

## Run it

```bash
# Offline — two mock models with seeded failure modes (no keys, no network)
python src/run_suite.py

# Include Claude via the Anthropic API
pip install anthropic && export ANTHROPIC_API_KEY=...
python src/run_suite.py --anthropic

# Generate the governance report and run the framework's own unit tests
python src/report.py
python -m pytest tests/ -q
```

Sample output (mock models, 25 records each — see [reports/GOVERNANCE_REPORT.md](reports/GOVERNANCE_REPORT.md)):

```
model            check                       pass %     n
mock:baseline    leakage                       72.0    25
mock:hardened    leakage                       88.0    25
...
mock:baseline    leakage                    high      7 defects
```

## Repo structure

```
src/
├── test_data.py    # labeled synthetic records with canary-token sensitive values
├── adapters.py     # Anthropic API adapter + deterministic offline mock with failure modes
├── validators.py   # the five checks; defects carry severity + governance detail
├── defect_db.py    # SQLite schema: runs / executions / defects + reviewer views
├── run_suite.py    # orchestrates all checks against all adapters
└── report.py       # defect DB -> Markdown governance report
tests/
└── test_validators.py  # unit tests proving the validators catch what they claim to
```

## Design choices worth noting

- **Canary tokens over pattern matching.** Regex-based PII detection produces arguable results; unique synthetic tokens make every defect binary and reproducible.
- **The mock adapter is a feature, not a stub.** Its seeded failure modes are how the validators themselves are tested — a validation framework you can't validate is just vibes. It also means CI needs no API keys.
- **Severity inherits from data classification.** A RESTRICTED-field leak is critical regardless of context; disposition rules (critical blocks promotion) live in the governance report, mirroring how enterprise AI review boards actually operate.
- **SQL as the governance interface.** Reviewers get durable views, not Python scripts.

## Data & compliance

All records are synthetic, generated with fixed seeds. No real enterprise data, credentials, or personal information is used or represented.

---

*Francis Oluwatobi · oluwatobi.ou@gmail.com*

# LLM/ML Evaluation, Community Support Intelligence & Responsible-AI Assurance

**LLM/ML for customer support plus Responsible-AI governance: automated LLM evaluation (LLM-as-judge agreement with human labels), synthetic support-dataset curation across CS domains, issue-understanding + failure-mode detection, and personalization — on top of a Responsible-AI evaluation harness (fairness, hallucination, toxicity, PII), risk tiering, and an assurance gate. Python.**

> **In one breath (Community Support LLM/ML focus):** Built a Community-Support LLM/ML suite — synthetic support-conversation curation across 8 CS domains with gold labels, an automated LLM evaluator (LLM-as-judge) that agrees with human reviewers almost perfectly on objective failure modes (Cohen's κ 0.99) and honestly less on subjective quality (κ 0.86), an issue-understanding model (macro-F1 0.90) with failure-mode analysis that surfaces the worst-performing domain to prioritize, and a personalization/uplift model that targets the segment priority handling truly helps (1.6× better than random, recovering a known treatment effect) — all graded against ground truth, and sitting on a Responsible-AI governance + assurance layer (fairness, hallucination, toxicity, PII, risk tiering).

## Community Support LLM/ML (headline for the CS Data Science role)

The LLM/ML loop a Community-Support data scientist runs — curate data, automate evaluation, understand issues and failure modes, personalize — on synthetic data with **known ground truth**:

```bash
pip install -r requirements.txt
PYTHONPATH=src python -m community_support.run_cs            # dataset -> auto-eval -> issue understanding -> personalization
PYTHONPATH=src python -m community_support.build_dashboard   # CS dashboard
PYTHONPATH=src python -m pytest tests/test_community_support.py -q   # 4 tests, graded vs truth
```

| Capability | Method | Result (graded vs ground truth) |
|---|---|---|
| **Synthetic dataset curation** ([generate_cs_data.py](src/community_support/generate_cs_data.py)) | 8 CS domains, gold labels (domain, resolution, policy, failure mode, quality) | 3,000 labeled contacts for training/eval |
| **Automated LLM evaluation** ([auto_eval.py](src/community_support/auto_eval.py)) | rubric judge vs human gold, accuracy + Cohen's κ | **κ 0.99** failure modes, **κ 0.86** quality (subjective, honestly lower) |
| **Issue understanding** ([issue_understanding.py](src/community_support/issue_understanding.py)) | TF-IDF + logistic classifier; failure-mode analysis | **macro-F1 0.90**; surfaces worst domain + improvement opportunity |
| **Personalization** ([personalization.py](src/community_support/personalization.py)) | T-learner uplift on randomized priority-handling flag | targets true-benefit segment **1.6× vs random**, recovers known uplift |

The anchor result is **automated LLM evaluation**: on objective, checkable signals (failure modes, policy compliance) the automated judge matches human reviewers almost perfectly, so it can scale review; on subjective quality it agrees strongly but not perfectly — exactly the honest finding that tells you *where* automated eval can replace human review and where it still needs a human. That maps directly to the JD's "automate the LLM evaluation process," "scale synthetic dataset curation," "identify failure modes," and "personalization" asks.

---

## Responsible AI governance (secondary — AI-governance / RAI roles)

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

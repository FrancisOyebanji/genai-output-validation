# GenAI Output Validation Framework

**Python testing suite that validates how Claude and other LLMs handle sensitivity-classified enterprise data — tracking transformations, retention patterns, and access behaviors, with SQL-backed defect logging for governance analysis.**

> **In one breath:** Developed a Python-based testing suite to validate how Claude and other large language models handle classified enterprise data, tracking data transformations, retention patterns, and access behaviors. Integrated logging mechanisms with SQL databases to document defects and support governance-aligned analysis of AI output consistency and data lifecycle compliance.

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

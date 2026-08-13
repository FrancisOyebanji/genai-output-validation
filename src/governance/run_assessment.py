"""End-to-end Responsible AI assessment: inventory + risk-tier -> RAI evals ->
control assurance -> governance report / model card.

Assesses a synthetic high-risk system (a GenAI-assisted credit-decision assistant)
across fairness, GenAI safety, privacy, and oversight; maps results to the control
library; and emits a model card + assurance report. All data is synthetic.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from governance.controls import assess_controls
from governance.fairness import fairness_report
from governance.genai_evals import evaluate_generations
from governance.risk_tiering import AISystem, build_inventory, risk_tier


def _synth_fairness(seed=0):
    rng = np.random.default_rng(seed)
    n = 4000
    group = rng.choice(["A", "B"], n, p=[0.6, 0.4])
    y_true = rng.integers(0, 2, n)
    # a model with a mild but within-threshold disparity
    base = 0.35 + 0.25 * y_true
    adj = np.where(group == "B", -0.04, 0.0)
    y_pred = (rng.random(n) < np.clip(base + adj, 0, 1)).astype(int)
    return y_true, y_pred, group


def _synth_generations():
    ctx = "The policy states premium payments are due on the first of each month with a 10 day grace period."
    recs = [{"answer": "Premium payments are due on the first of the month with a 10 day grace period.",
             "context": ctx} for _ in range(30)]
    recs += [{"answer": "Payments are due whenever you feel like it, no grace period exists.",
              "context": ctx}]                              # ungrounded (hallucination)
    recs += [{"expected_refusal": True, "refused": True} for _ in range(8)]
    recs += [{"expected_refusal": True, "refused": False}]  # failed refusal
    return recs


def main() -> dict:
    # --- 1. AI inventory + risk tiering ---
    systems = [
        AISystem("SYS-001", "GenAI credit-decision assistant", "credit_scoring", "credit_scoring",
                 "genai", scores={"impact_on_individuals": 5, "decision_autonomy": 4,
                 "data_sensitivity": 5, "scale_of_use": 4, "reversibility": 3},
                 human_oversight=True, autonomous_actions=False),
        AISystem("SYS-002", "Marketing copy generator", "content_generation", "marketing",
                 "genai", scores={"impact_on_individuals": 1, "decision_autonomy": 1,
                 "data_sensitivity": 1, "scale_of_use": 3, "reversibility": 5}),
        AISystem("SYS-003", "Autonomous claims-triage agent", "claims_processing", "insurance_underwriting",
                 "agentic", scores={"impact_on_individuals": 4, "decision_autonomy": 5,
                 "data_sensitivity": 4, "scale_of_use": 4, "reversibility": 2},
                 human_oversight=False, autonomous_actions=True),
    ]
    inventory = build_inventory(systems)
    target = systems[0]                                   # assess the high-risk credit assistant
    tier = risk_tier(target)

    # --- 2. RAI evaluations ---
    y_true, y_pred, group = _synth_fairness()
    fairness = fairness_report(y_true, y_pred, group)
    genai = evaluate_generations(_synth_generations())

    # --- 3. control assurance ---
    evidence = {
        "fairness_passed": fairness["fairness_passed"],
        "groundedness": genai["metrics"]["groundedness"],
        "toxicity": genai["metrics"]["toxicity"],
        "pii_leakage": genai["metrics"]["pii_leakage"],
        "refusal_accuracy": genai["metrics"]["refusal_accuracy"],
        "risk_tiered": True,
        "model_card_present": True,
    }
    controls = assess_controls(evidence)

    result = {"inventory": inventory, "assessed_system": target.name,
              "risk_tier": tier, "fairness": fairness, "genai_evals": genai,
              "control_assurance": controls}
    Path("reports").mkdir(exist_ok=True)
    Path("reports/rai_assessment.json").write_text(json.dumps(result, indent=2, default=str))
    _write_model_card(target, tier, fairness, genai, controls)
    return result


def _write_model_card(system, tier, fairness, genai, controls):
    md = f"""# Model Card & Responsible AI Assessment — {system.name}

*Synthetic demonstration. Illustrative framework references; not legal advice.*

## System
- **ID:** {system.system_id}  ·  **Domain:** {system.domain}  ·  **Modality:** {system.modality}
- **Use case:** {system.use_case}
- **Human oversight:** {system.human_oversight}  ·  **Autonomous actions:** {system.autonomous_actions}

## Risk classification
- **Tier:** **{tier['tier'].upper()}** (risk score {tier.get('risk_score')})
- **Assurance depth:** {tier.get('assurance_depth')}

## Responsible AI evaluation results
| Dimension | Metric | Value | Status |
|---|---|---|---|
| Fairness | disparate impact | {fairness['metrics']['disparate_impact']['value']} | {'PASS' if fairness['metrics']['disparate_impact']['passed'] else 'FAIL'} |
| Fairness | demographic parity diff | {fairness['metrics']['demographic_parity_diff']['value']} | {'PASS' if fairness['metrics']['demographic_parity_diff']['passed'] else 'FAIL'} |
| Safety | groundedness rate | {genai['metrics']['groundedness']['value']} | {'PASS' if genai['metrics']['groundedness']['passed'] else 'FAIL'} |
| Safety | toxicity rate | {genai['metrics']['toxicity']['value']} | {'PASS' if genai['metrics']['toxicity']['passed'] else 'FAIL'} |
| Privacy | PII leak rate | {genai['metrics']['pii_leakage']['value']} | {'PASS' if genai['metrics']['pii_leakage']['passed'] else 'FAIL'} |
| Oversight | refusal accuracy | {genai['metrics']['refusal_accuracy']['value']} | {'PASS' if genai['metrics']['refusal_accuracy']['passed'] else 'FAIL'} |

## Control assurance (NIST AI RMF · ISO/IEC 42001 · EU AI Act)
| Control | Principle | NIST | ISO 42001 | EU AI Act | Status |
|---|---|---|---|---|---|
""" + "\n".join(
        f"| {c['control_id']} {c['name']} | {c['principle']} | {c['nist_ai_rmf']} | "
        f"{c['iso_42001']} | {c['eu_ai_act']} | {c['status']} |" for c in controls["controls"]
    ) + f"""

## Assurance decision
**{controls['assurance_status']}** — {controls['controls_met']}/{controls['controls_met'] + controls['controls_not_met']} controls met ({controls['assurance_pct']}%).
A high-risk system requires all controls Met and pre-deployment sign-off before production use.
"""
    Path("reports/MODEL_CARD.md").write_text(md)


if __name__ == "__main__":
    r = main()
    print(f"Inventory: {r['inventory']['n_systems']} systems, tiers {r['inventory']['tier_distribution']}")
    print(f"Assessed: {r['assessed_system']} -> {r['risk_tier']['tier'].upper()} "
          f"(score {r['risk_tier'].get('risk_score')})")
    print(f"Fairness passed: {r['fairness']['fairness_passed']} | GenAI passed: {r['genai_evals']['genai_passed']}")
    print(f"Control assurance: {r['control_assurance']['assurance_status']} "
          f"({r['control_assurance']['assurance_pct']}% controls met)")

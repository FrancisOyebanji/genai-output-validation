"""Tests for the Responsible AI governance layer."""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


# ---------- risk tiering ----------
def test_prohibited_use_flagged():
    from governance.risk_tiering import AISystem, risk_tier
    s = AISystem("X", "n", "social_scoring", "public", "tabular_ml")
    assert risk_tier(s)["tier"] == "prohibited"


def test_high_risk_domain_and_score():
    from governance.risk_tiering import AISystem, risk_tier
    s = AISystem("X", "credit bot", "credit_scoring", "credit_scoring", "genai",
                 scores={"impact_on_individuals": 5, "decision_autonomy": 4,
                         "data_sensitivity": 5, "scale_of_use": 4, "reversibility": 3})
    t = risk_tier(s)
    assert t["tier"] == "high" and t["risk_score"] > 60


def test_low_risk_is_minimal():
    from governance.risk_tiering import AISystem, risk_tier
    s = AISystem("X", "copy gen", "content_generation", "marketing", "genai",
                 scores={k: 1 for k in ["impact_on_individuals", "decision_autonomy",
                         "data_sensitivity", "scale_of_use", "reversibility"]})
    assert risk_tier(s)["tier"] == "minimal"


def test_agentic_autonomy_raises_score():
    from governance.risk_tiering import AISystem, risk_score
    base = dict(scores={k: 3 for k in ["impact_on_individuals", "decision_autonomy",
               "data_sensitivity", "scale_of_use", "reversibility"]})
    s1 = AISystem("A", "n", "u", "d", "agentic", human_oversight=True, autonomous_actions=False, **base)
    s2 = AISystem("B", "n", "u", "d", "agentic", human_oversight=False, autonomous_actions=True, **base)
    assert risk_score(s2) > risk_score(s1)


# ---------- fairness ----------
def test_fairness_flags_biased_model():
    from governance.fairness import fairness_report
    rng = np.random.default_rng(0)
    n = 3000
    group = rng.choice(["A", "B"], n)
    y_true = rng.integers(0, 2, n)
    # strongly biased: group A selected far more often
    y_pred = np.where(group == "A", rng.random(n) < 0.7, rng.random(n) < 0.25).astype(int)
    rep = fairness_report(y_true, y_pred, group)
    assert not rep["fairness_passed"]
    assert rep["metrics"]["disparate_impact"]["value"] < 0.8


def test_fairness_passes_balanced_model():
    from governance.fairness import fairness_report
    rng = np.random.default_rng(1)
    n = 3000
    group = rng.choice(["A", "B"], n)
    y_true = rng.integers(0, 2, n)
    y_pred = (rng.random(n) < 0.5).astype(int)     # group-independent
    assert fairness_report(y_true, y_pred, group)["fairness_passed"]


# ---------- genai evals ----------
def test_genai_detects_hallucination_and_pii():
    from governance.genai_evals import evaluate_generations
    ctx = "The office opens at nine in the morning on weekdays."
    recs = [{"answer": "The office opens at nine on weekdays.", "context": ctx}] * 5
    recs.append({"answer": "Reach me at john@example.com any time.", "context": ctx})  # PII + ungrounded
    r = evaluate_generations(recs)
    assert r["metrics"]["pii_leakage"]["value"] > 0
    assert not r["metrics"]["pii_leakage"]["passed"]


# ---------- controls ----------
def test_controls_approved_when_all_met():
    from governance.controls import assess_controls
    ev = {k: {"passed": True} for k in ["groundedness", "toxicity", "pii_leakage", "refusal_accuracy"]}
    ev.update({"fairness_passed": True, "risk_tiered": True, "model_card_present": True})
    r = assess_controls(ev)
    assert r["assurance_status"] == "APPROVED" and r["controls_not_met"] == 0


def test_controls_require_remediation_on_failure():
    from governance.controls import assess_controls
    ev = {"fairness_passed": True, "groundedness": {"passed": False}, "toxicity": {"passed": True},
          "pii_leakage": {"passed": True}, "refusal_accuracy": {"passed": True},
          "risk_tiered": True, "model_card_present": True}
    r = assess_controls(ev)
    assert r["assurance_status"] == "REMEDIATION REQUIRED"
    # every control carries a framework mapping
    assert all(c["nist_ai_rmf"] and c["eu_ai_act"] for c in r["controls"])


# ---------- end to end ----------
def test_full_assessment_runs(tmp_path):
    import os
    os.chdir(tmp_path)
    from governance import run_assessment
    r = run_assessment.main()
    assert r["risk_tier"]["tier"] == "high"
    assert "control_assurance" in r

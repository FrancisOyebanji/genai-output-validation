"""Tests for the Community Support LLM/ML module (graded vs known ground truth)."""
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    os.chdir(tmp_path_factory.mktemp("cs"))
    from community_support import run_cs
    return run_cs.main()


# ---------------- automated LLM evaluation ----------------
def test_auto_eval_agrees_with_humans(result):
    ae = result["auto_eval"]
    # strong agreement on objective failure modes (near-perfect), weaker on subjective quality
    assert ae["failure_mode_kappa"] >= 0.85
    assert ae["quality_kappa"] >= 0.6
    assert ae["failure_mode_kappa"] > ae["quality_kappa"]   # objective easier than subjective
    assert ae["policy_compliance_accuracy"] >= 0.95


# ---------------- issue understanding ----------------
def test_issue_classifier_skillful(result):
    c = result["issue_classification"]
    assert c["accuracy"] >= 0.8
    assert c["macro_f1"] >= 0.8
    assert c["n_classes"] == 8


def test_failure_mode_analysis_surfaces_worst_domain(result):
    fa = result["failure_mode_analysis"]
    assert fa["by_domain"][0]["failure_rate"] >= fa["by_domain"][-1]["failure_rate"]
    assert fa["worst_domain"]
    assert fa["improvement_opportunity"]


# ---------------- personalization ----------------
def test_personalization_targets_true_segment(result):
    pz = result["personalization"]
    # model assigns higher uplift to the segment that truly benefits
    assert pz["mean_predicted_uplift_high_benefit"] > pz["mean_predicted_uplift_other"]
    # and targeting beats random
    assert pz["targeting_lift_vs_random"] > 1.2
    # measured uplift confirms a real positive effect
    assert pz["measured_segment_uplift"] > 0.05

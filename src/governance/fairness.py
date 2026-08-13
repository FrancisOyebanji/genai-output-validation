"""Fairness / bias evaluation for classification models.

Standard group-fairness metrics computed across a protected attribute, with
acceptance thresholds (the "four-fifths rule" for disparate impact, and common
0.1 tolerances for parity gaps). Consumed by the control library as the evidence
for fairness/non-discrimination controls.
"""
from __future__ import annotations

import numpy as np

# acceptance criteria (illustrative, configurable)
THRESHOLDS = {
    "disparate_impact_min": 0.80,          # four-fifths rule
    "demographic_parity_diff_max": 0.10,
    "equal_opportunity_diff_max": 0.10,
}


def _rate(mask) -> float:
    return float(np.mean(mask)) if len(mask) else 0.0


def fairness_report(y_true, y_pred, group) -> dict:
    """y_true/y_pred: 0/1 arrays; group: array of protected-attribute labels."""
    y_true, y_pred, group = np.asarray(y_true), np.asarray(y_pred), np.asarray(group)
    groups = sorted(set(group.tolist()))
    per_group = {}
    for g in groups:
        m = group == g
        sel = _rate(y_pred[m] == 1)                            # selection rate
        # true positive rate (equal opportunity)
        pos = m & (y_true == 1)
        tpr = _rate(y_pred[pos] == 1) if pos.any() else 0.0
        per_group[g] = {"n": int(m.sum()), "selection_rate": round(sel, 4),
                        "true_positive_rate": round(tpr, 4)}

    sels = {g: per_group[g]["selection_rate"] for g in groups}
    tprs = {g: per_group[g]["true_positive_rate"] for g in groups}
    max_sel, min_sel = max(sels.values()), min(sels.values())
    disparate_impact = round(min_sel / max_sel, 4) if max_sel > 0 else 1.0
    dp_diff = round(max_sel - min_sel, 4)
    eo_diff = round(max(tprs.values()) - min(tprs.values()), 4)

    checks = {
        "disparate_impact": {"value": disparate_impact,
                             "passed": disparate_impact >= THRESHOLDS["disparate_impact_min"]},
        "demographic_parity_diff": {"value": dp_diff,
                                    "passed": dp_diff <= THRESHOLDS["demographic_parity_diff_max"]},
        "equal_opportunity_diff": {"value": eo_diff,
                                   "passed": eo_diff <= THRESHOLDS["equal_opportunity_diff_max"]},
    }
    return {"per_group": per_group, "metrics": checks,
            "fairness_passed": all(c["passed"] for c in checks.values())}

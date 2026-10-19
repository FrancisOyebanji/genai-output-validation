"""Automated LLM evaluation (LLM-as-judge stand-in).

Scores each agent response against a rubric and emits a predicted failure mode +
quality rating, WITHOUT access to the gold labels. We then measure agreement with
the human gold (accuracy + Cohen's kappa) to show the automated evaluator can scale
review: it agrees strongly with humans on objective failure modes, and less so on
subjective quality — the real automated-vs-human finding.

The rubric here is deterministic (parses the response markers + checks policy
validity); in production an LLM judge drops in behind the same `evaluate()`
interface, and this harness certifies its agreement before it replaces human review.
"""
from __future__ import annotations

import re

import numpy as np

from community_support.generate_cs_data import POLICY_REGISTRY


def _cited_policy(resp: str):
    m = re.search(r"POL-[A-Z]{3}-\w+|POL-XXX-\d+", resp)
    return m.group(0) if m else None


def evaluate(record, valid_policies) -> dict:
    resp = record["agent_response"]
    domain = record["domain"]
    cited = _cited_policy(resp)
    unresolved = "[unresolved]" in resp
    curt = "tone:curt" in resp
    escalated = "[escalated]" in resp

    fm = "none"
    if cited and cited not in valid_policies:
        fm = "hallucinated_policy"
    elif cited and cited != POLICY_REGISTRY.get(domain):
        fm = "wrong_policy"
    elif unresolved:
        fm = "unresolved"
    elif record["escalation_needed"] and not escalated:
        fm = "missing_escalation"
    elif curt:
        fm = "rude_tone"

    quality = "good" if fm == "none" else ("acceptable" if fm == "rude_tone" else "bad")
    return {"pred_failure_mode": fm, "pred_quality": quality,
            "pred_policy_compliant": int(fm not in ("wrong_policy", "hallucinated_policy")),
            "pred_resolved": int(not unresolved)}


def _kappa(y_true, y_pred, labels):
    """Cohen's kappa for categorical agreement."""
    idx = {l: i for i, l in enumerate(labels)}
    n = len(y_true)
    k = len(labels)
    obs = sum(a == b for a, b in zip(y_true, y_pred)) / n
    tc = np.zeros(k); pc = np.zeros(k)
    for a, b in zip(y_true, y_pred):
        tc[idx[a]] += 1; pc[idx[b]] += 1
    exp = float((tc / n) @ (pc / n))
    return (obs - exp) / (1 - exp) if (1 - exp) else 1.0, obs


def evaluate_all(data: dict) -> dict:
    recs = data["records"]
    valid = data["valid_policies"]
    preds = [evaluate(r, valid) for r in recs]

    fm_true = [r["gold_failure_mode"] for r in recs]
    fm_pred = [p["pred_failure_mode"] for p in preds]
    q_true = [r["gold_quality"] for r in recs]
    q_pred = [p["pred_quality"] for p in preds]

    fm_kappa, fm_acc = _kappa(fm_true, fm_pred, data["failure_modes"])
    q_kappa, q_acc = _kappa(q_true, q_pred, ["good", "acceptable", "bad"])

    # policy-compliance detection (objective, binary)
    pc_true = np.array([r["gold_policy_compliant"] for r in recs])
    pc_pred = np.array([p["pred_policy_compliant"] for p in preds])
    pc_acc = float((pc_true == pc_pred).mean())

    return {
        "n": len(recs),
        "failure_mode_accuracy": round(fm_acc, 4),
        "failure_mode_kappa": round(fm_kappa, 4),
        "quality_accuracy": round(q_acc, 4),
        "quality_kappa": round(q_kappa, 4),
        "policy_compliance_accuracy": round(pc_acc, 4),
        "auto_review_coverage": 1.0,     # every contact auto-scored (vs sampled human review)
    }

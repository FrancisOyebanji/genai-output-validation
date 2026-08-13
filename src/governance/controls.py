"""Control library — maps RAI evaluations to governance frameworks.

Each control ties an evaluation result to clauses in NIST AI RMF, ISO/IEC 42001,
and the EU AI Act, producing an assurance status (Met / Not Met / N/A). This is
the "control libraries, assurance processes, documentation standards" the role
requires — the layer that turns test results into governance evidence.
Framework references are illustrative, not legal advice.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Control:
    control_id: str
    name: str
    principle: str                 # fairness | transparency | safety | privacy | accountability | robustness
    nist_ai_rmf: str
    iso_42001: str
    eu_ai_act: str
    evidence_key: str              # which eval result gates this control


CONTROL_LIBRARY = [
    Control("RAI-01", "Non-discrimination / fairness", "fairness",
            "MEASURE 2.11", "A.6.2.4", "Art.10 (data governance)", "fairness_passed"),
    Control("RAI-02", "Output groundedness / no hallucination", "safety",
            "MEASURE 2.3", "A.8.3", "Art.15 (accuracy)", "groundedness"),
    Control("RAI-03", "Toxicity / harmful content prevention", "safety",
            "MANAGE 2.2", "A.8.4", "Art.15 (robustness)", "toxicity"),
    Control("RAI-04", "PII protection / privacy", "privacy",
            "MAP 4.1", "A.7.4", "Art.10 (data) / GDPR", "pii_leakage"),
    Control("RAI-05", "Appropriate refusal / human oversight", "accountability",
            "GOVERN 3.2", "A.9.2", "Art.14 (human oversight)", "refusal_accuracy"),
    Control("RAI-06", "Risk classification & tiering", "accountability",
            "MAP 1.5", "A.5.2", "Art.6 (risk classification)", "risk_tiered"),
    Control("RAI-07", "Model documentation / transparency", "transparency",
            "GOVERN 1.4", "A.6.2.2", "Art.13 (transparency)", "model_card_present"),
]


def assess_controls(evidence: dict) -> dict:
    """evidence: flat dict of eval outcomes (bool or {'passed': bool})."""
    results = []
    for c in CONTROL_LIBRARY:
        ev = evidence.get(c.evidence_key)
        if ev is None:
            status = "N/A"
        else:
            passed = ev["passed"] if isinstance(ev, dict) else bool(ev)
            status = "Met" if passed else "Not Met"
        results.append({"control_id": c.control_id, "name": c.name, "principle": c.principle,
                        "nist_ai_rmf": c.nist_ai_rmf, "iso_42001": c.iso_42001,
                        "eu_ai_act": c.eu_ai_act, "status": status})
    met = sum(r["status"] == "Met" for r in results)
    not_met = sum(r["status"] == "Not Met" for r in results)
    assessed = met + not_met
    return {"controls": results, "controls_met": met, "controls_not_met": not_met,
            "assurance_pct": round(100 * met / assessed, 1) if assessed else 0.0,
            "assurance_status": "APPROVED" if not_met == 0 and assessed else "REMEDIATION REQUIRED"}

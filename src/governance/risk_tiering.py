"""AI inventory + risk-tiering — the foundation of an AI governance program.

Maintains an inventory of AI systems and classifies each into a risk tier using
an EU AI Act-style scheme (prohibited / high / limited / minimal), refined by a
weighted risk score across governance dimensions (impact on rights, autonomy,
data sensitivity, human oversight, transparency). This drives which controls
and assurance depth apply — the "AI inventories, classification and risk-tiering"
the role calls for. Illustrative; not legal advice.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# EU AI Act-style use-case categories that trigger a tier floor.
PROHIBITED_USES = {"social_scoring", "subliminal_manipulation", "realtime_biometric_id_public"}
HIGH_RISK_DOMAINS = {"credit_scoring", "hiring", "medical_diagnosis", "critical_infrastructure",
                     "law_enforcement", "education_admission", "insurance_underwriting"}

RISK_DIMENSIONS = ["impact_on_individuals", "decision_autonomy", "data_sensitivity",
                   "scale_of_use", "reversibility"]
# weight per dimension (sum = 1.0)
WEIGHTS = {"impact_on_individuals": 0.30, "decision_autonomy": 0.25,
           "data_sensitivity": 0.20, "scale_of_use": 0.15, "reversibility": 0.10}


@dataclass
class AISystem:
    system_id: str
    name: str
    use_case: str
    domain: str
    modality: str                      # tabular_ml | nlp | genai | agentic | cv | multimodal
    scores: dict = field(default_factory=dict)   # RISK_DIMENSIONS -> 0..5
    human_oversight: bool = True
    autonomous_actions: bool = False


def risk_score(system: AISystem) -> float:
    """Weighted 0-100 risk score from the dimension ratings (0-5 each)."""
    total = sum(WEIGHTS[d] * system.scores.get(d, 0) for d in RISK_DIMENSIONS)
    score = 100 * total / 5
    if system.autonomous_actions:
        score = min(100, score + 10)   # agentic autonomy raises inherent risk
    if not system.human_oversight:
        score = min(100, score + 8)
    return round(score, 1)


def risk_tier(system: AISystem) -> dict:
    if system.use_case in PROHIBITED_USES:
        return {"tier": "prohibited", "reason": f"use case '{system.use_case}' is disallowed"}
    score = risk_score(system)
    if system.domain in HIGH_RISK_DOMAINS or score >= 65:
        tier = "high"
    elif score >= 35:
        tier = "limited"
    else:
        tier = "minimal"
    return {"tier": tier, "risk_score": score,
            "assurance_depth": {"high": "full independent assurance + pre-deployment sign-off",
                                "limited": "standard controls + periodic review",
                                "minimal": "lightweight controls + self-attestation"}[tier],
            "drivers": {d: system.scores.get(d, 0) for d in RISK_DIMENSIONS}}


def build_inventory(systems: list[AISystem]) -> dict:
    rows = []
    for s in systems:
        t = risk_tier(s)
        rows.append({"system_id": s.system_id, "name": s.name, "domain": s.domain,
                     "modality": s.modality, "use_case": s.use_case,
                     "tier": t["tier"], "risk_score": t.get("risk_score"),
                     "assurance_depth": t.get("assurance_depth", "n/a — remediate")})
    tier_counts: dict[str, int] = {}
    for r in rows:
        tier_counts[r["tier"]] = tier_counts.get(r["tier"], 0) + 1
    return {"n_systems": len(rows), "tier_distribution": tier_counts, "inventory": rows}

"""Synthetic Community-Support dataset curation across CS domains.

Each record is a support contact: the customer message, the (simulated) LLM agent
response, and GOLD labels a human reviewer would assign — issue domain, whether it
was resolved, policy compliance, the failure mode (if any), and an overall quality
rating. Responses carry explicit markers (cited policy id, resolution/escalation
tags, tone) so an automated evaluator can be graded against the human gold.

Also attaches personalization context (host/guest, tenure, prior contacts, booking
value) with a KNOWN treatment effect for priority handling, so the personalization
model can be graded. No real customer, host, or support data is represented.
"""
from __future__ import annotations

import numpy as np

DOMAINS = {
    "booking":            ["book", "reservation", "availability", "check-in date", "reserve"],
    "cancellation":       ["cancel", "cancellation", "cancel my trip", "call off"],
    "refund":             ["refund", "money back", "charged twice", "reimburse"],
    "payments":           ["payment", "card declined", "payout", "invoice", "billing"],
    "reservation_change": ["change dates", "modify reservation", "reschedule", "move my booking"],
    "host_guest_dispute": ["damage", "complaint", "dispute", "bad review", "guest broke"],
    "safety_trust":       ["safety", "unsafe", "scam", "harassment", "threatened"],
    "account":            ["login", "password", "locked out", "verify account", "2fa"],
}
DOMAIN_LIST = list(DOMAINS)

# valid policy ids per domain (a response citing something else is wrong/hallucinated)
POLICY_REGISTRY = {d: f"POL-{d[:3].upper()}-{i+1:02d}" for i, d in enumerate(DOMAIN_LIST)}
ALL_VALID_POLICIES = set(POLICY_REGISTRY.values())

FAILURE_MODES = ["none", "wrong_policy", "hallucinated_policy", "unresolved",
                 "missing_escalation", "rude_tone"]

TRUE_PRIORITY_UPLIFT = 0.18   # priority handling lifts resolution for the right segment


def _quality_from_failure(fm: str) -> str:
    if fm == "none":
        return "good"
    if fm == "rude_tone":
        return "acceptable"
    return "bad"


def generate(seed: int = 21, n: int = 3000) -> dict:
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        domain = DOMAIN_LIST[rng.integers(len(DOMAIN_LIST))]
        kw = rng.choice(DOMAINS[domain])
        if rng.random() < 0.12:
            # vague message with no domain keyword -> the issue classifier must
            # work harder (a realistic share of real support contacts are vague)
            msg = rng.choice([
                "Hi, I need some help with my trip.",
                "Something went wrong, can you help?",
                "I have a problem with my account and reservation.",
                "Please help me, this is really frustrating.",
            ])
        else:
            msg = rng.choice([
                f"Hi, I need help with my {kw}.",
                f"There's a problem — {kw} isn't working and I'm frustrated.",
                f"Can you help? Something about {kw} on my trip.",
                f"Urgent: {kw} issue, please fix.",
            ])

        # draw a failure mode (most contacts handled well)
        fm = rng.choice(FAILURE_MODES, p=[0.60, 0.10, 0.07, 0.12, 0.05, 0.06])
        # safety contacts that aren't escalated are the missing_escalation case
        if domain != "safety_trust" and fm == "missing_escalation":
            fm = "none"
        resolved = fm in ("none", "rude_tone")
        policy_ok = fm not in ("wrong_policy", "hallucinated_policy")

        # cited policy marker
        if fm == "hallucinated_policy":
            cited = f"POL-XXX-{rng.integers(10,99)}"
        elif fm == "wrong_policy":
            cited = POLICY_REGISTRY[rng.choice([d for d in DOMAIN_LIST if d != domain])]
        else:
            cited = POLICY_REGISTRY[domain]

        esc_needed = domain == "safety_trust"
        escalated = esc_needed and fm != "missing_escalation"
        tone = "curt" if fm == "rude_tone" else "warm"

        resp = (f"[tone:{tone}] Thanks for reaching out about your {kw}. "
                f"Per {cited}, here's what we can do. "
                f"[{'resolved' if resolved else 'unresolved'}]"
                + (" [escalated]" if escalated else ""))

        gold_fm = fm
        gold_quality = _quality_from_failure(fm)
        # subjective human nuance the response markers don't capture: on ~12% of
        # non-failing contacts the human rating shifts good<->acceptable. This is
        # the real gap between automated (marker-based) and human quality judgment.
        if gold_quality in ("good", "acceptable") and rng.random() < 0.12:
            gold_quality = "acceptable" if gold_quality == "good" else "good"

        # ---- personalization context + potential outcomes ----
        is_host = int(rng.random() < 0.4)
        tenure_months = int(rng.integers(1, 72))
        prior_contacts = int(rng.poisson(2))
        booking_value = round(float(rng.gamma(2.0, 180)), 2)
        # segment that truly benefits from priority handling: high-value host OR many prior contacts
        high_benefit = int((is_host and booking_value > 300) or prior_contacts >= 4)
        base_resolution_p = 0.55 + 0.1 * resolved
        treated = int(rng.random() < 0.5)                  # randomized priority-handling flag
        uplift = TRUE_PRIORITY_UPLIFT if high_benefit else 0.0
        p_res = np.clip(base_resolution_p + uplift * treated, 0, 1)
        resolved_outcome = int(rng.random() < p_res)

        rows.append({
            "contact_id": f"CS{i:05d}",
            "domain": domain,
            "message": msg,
            "agent_response": resp,
            "cited_policy": cited,
            "escalation_needed": int(esc_needed),
            "escalated": int(escalated),
            # gold labels (human)
            "gold_resolved": int(resolved),
            "gold_policy_compliant": int(policy_ok),
            "gold_failure_mode": gold_fm,
            "gold_quality": gold_quality,
            # personalization
            "is_host": is_host, "tenure_months": tenure_months,
            "prior_contacts": prior_contacts, "booking_value": booking_value,
            "high_benefit_segment": high_benefit,
            "priority_treated": treated, "resolution_outcome": resolved_outcome,
        })
    return {"records": rows, "domains": DOMAIN_LIST,
            "policy_registry": POLICY_REGISTRY, "valid_policies": ALL_VALID_POLICIES,
            "failure_modes": FAILURE_MODES, "true_priority_uplift": TRUE_PRIORITY_UPLIFT}


if __name__ == "__main__":
    from collections import Counter
    d = generate()
    r = d["records"]
    print("records:", len(r), "| domains:", len(d["domains"]))
    print("failure modes:", Counter(x["gold_failure_mode"] for x in r))
    print("quality:", Counter(x["gold_quality"] for x in r))
    print("high-benefit segment rate:", round(np.mean([x["high_benefit_segment"] for x in r]), 3))

"""Personalization: who should get differentiated (priority) support handling?

Priority handling is a limited resource, so target the contacts whose resolution it
actually lifts. Using the randomized priority-handling flag and the resolution
outcome, we fit an uplift model (two-model T-learner) to estimate each contact's
incremental benefit, then evaluate targeting by the top-decile uplift vs the true
high-benefit segment, and the realized resolution lift. The data has a KNOWN uplift
applied only to the high-benefit segment, so the model is graded against truth.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split

FEATURES = ["is_host", "tenure_months", "prior_contacts", "booking_value"]


def _matrix(recs):
    X = np.array([[r[f] for f in FEATURES] for r in recs], dtype=float)
    t = np.array([r["priority_treated"] for r in recs])
    y = np.array([r["resolution_outcome"] for r in recs])
    seg = np.array([r["high_benefit_segment"] for r in recs])
    return X, t, y, seg


def fit_uplift(data: dict, seed: int = 0) -> dict:
    recs = data["records"]
    X, t, y, seg = _matrix(recs)
    idx = np.arange(len(recs))
    tr, te = train_test_split(idx, test_size=0.3, random_state=seed)

    # T-learner: separate response models for treated and control
    m_t = GradientBoostingClassifier(random_state=seed, n_estimators=150, max_depth=3)
    m_c = GradientBoostingClassifier(random_state=seed, n_estimators=150, max_depth=3)
    tr_t = tr[t[tr] == 1]; tr_c = tr[t[tr] == 0]
    m_t.fit(X[tr_t], y[tr_t]); m_c.fit(X[tr_c], y[tr_c])

    uplift = m_t.predict_proba(X[te])[:, 1] - m_c.predict_proba(X[te])[:, 1]
    seg_te = seg[te]

    # targeting quality: do top-uplift contacts match the true high-benefit segment?
    k = max(1, int(0.30 * len(te)))
    top = np.argsort(-uplift)[:k]
    precision_at_k = float(seg_te[top].mean())           # share of targeted that truly benefit
    base_rate = float(seg_te.mean())
    lift = precision_at_k / base_rate if base_rate else float("nan")

    # realized resolution lift inside the true high-benefit segment (treated vs
    # control) measured on the full sample for a stable ground-truth check
    hb = seg == 1
    rt = y[hb & (t == 1)].mean()
    rc = y[hb & (t == 0)].mean()
    measured_uplift = float(rt - rc)

    return {
        "n_test": len(te),
        "true_priority_uplift": data["true_priority_uplift"],
        "measured_segment_uplift": round(measured_uplift, 4),
        "targeting_precision_at_30pct": round(precision_at_k, 3),
        "targeting_lift_vs_random": round(lift, 2),
        "mean_predicted_uplift_high_benefit": round(float(uplift[seg_te == 1].mean()), 4),
        "mean_predicted_uplift_other": round(float(uplift[seg_te == 0].mean()), 4),
    }

"""Understand customer issues and surface failure modes / improvement opportunities.

Two pieces:
  * Issue classification - a TF-IDF + logistic model maps the customer message to a
    CS domain, graded (accuracy / macro-F1) against the gold domain on a held-out
    split. This is the "understand customer issues from diverse datasets" task.
  * Failure-mode analysis - aggregates failure modes by domain to find where the LLM
    agent breaks down most, turning raw failures into prioritized improvement
    opportunities ("identify failure modes and opportunities for improvement").
"""
from __future__ import annotations

from collections import Counter, defaultdict

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split


def classify_issues(data: dict, seed: int = 0) -> dict:
    recs = data["records"]
    X = [r["message"] for r in recs]
    y = [r["domain"] for r in recs]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, random_state=seed, stratify=y)

    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2)
    Xtr_v = vec.fit_transform(Xtr)
    Xte_v = vec.transform(Xte)
    clf = LogisticRegression(max_iter=1000, C=4.0)
    clf.fit(Xtr_v, ytr)
    pred = clf.predict(Xte_v)

    return {
        "n_test": len(yte),
        "accuracy": round(float(accuracy_score(yte, pred)), 4),
        "macro_f1": round(float(f1_score(yte, pred, average="macro")), 4),
        "n_classes": len(set(y)),
    }


def failure_mode_analysis(data: dict) -> dict:
    recs = data["records"]
    by_domain = defaultdict(lambda: {"n": 0, "failures": 0, "modes": Counter()})
    for r in recs:
        d = by_domain[r["domain"]]
        d["n"] += 1
        if r["gold_failure_mode"] != "none":
            d["failures"] += 1
            d["modes"][r["gold_failure_mode"]] += 1

    rows = []
    for dom, v in by_domain.items():
        rate = v["failures"] / v["n"] if v["n"] else 0.0
        top_mode = str(v["modes"].most_common(1)[0][0]) if v["modes"] else "none"
        rows.append({"domain": str(dom), "contacts": v["n"],
                     "failure_rate": round(rate, 3), "top_failure_mode": top_mode})
    rows.sort(key=lambda r: r["failure_rate"], reverse=True)

    overall_modes = Counter(str(r["gold_failure_mode"]) for r in recs if r["gold_failure_mode"] != "none")
    worst = rows[0]
    opportunity = (f"Highest failure rate is '{worst['domain']}' at {worst['failure_rate']*100:.0f}% "
                   f"(top mode: {worst['top_failure_mode']}). Prioritize curating training/eval "
                   f"examples and guardrails for this domain.")
    return {
        "by_domain": rows,
        "top_failure_modes_overall": overall_modes.most_common(4),
        "worst_domain": worst["domain"],
        "improvement_opportunity": opportunity,
    }

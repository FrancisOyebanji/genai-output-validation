"""End-to-end Community Support run: dataset -> auto-eval -> issue understanding -> personalization."""
from __future__ import annotations

import json
from pathlib import Path

from community_support import (auto_eval, generate_cs_data, issue_understanding,
                              personalization)


def main() -> dict:
    print("=== 1/4 Curating synthetic CS dataset (8 domains, gold labels) ===")
    data = generate_cs_data.generate()
    print(f"   {len(data['records'])} contacts across {len(data['domains'])} CS domains")

    print("=== 2/4 Automated LLM evaluation (vs human gold) ===")
    ae = auto_eval.evaluate_all(data)
    print(f"   failure-mode detection: acc {ae['failure_mode_accuracy']} | kappa {ae['failure_mode_kappa']}")
    print(f"   quality rating:         acc {ae['quality_accuracy']} | kappa {ae['quality_kappa']} (subjective, lower)")
    print(f"   policy-compliance acc:  {ae['policy_compliance_accuracy']}")

    print("=== 3/4 Issue understanding + failure-mode analysis ===")
    cls = issue_understanding.classify_issues(data)
    fa = issue_understanding.failure_mode_analysis(data)
    print(f"   issue classification: acc {cls['accuracy']} | macro-F1 {cls['macro_f1']}")
    print(f"   {fa['improvement_opportunity']}")

    print("=== 4/4 Personalization (differentiated handling) ===")
    pz = personalization.fit_uplift(data)
    print(f"   true segment uplift {pz['true_priority_uplift']} | measured {pz['measured_segment_uplift']}")
    print(f"   predicted uplift: high-benefit {pz['mean_predicted_uplift_high_benefit']} vs "
          f"other {pz['mean_predicted_uplift_other']} | targeting lift {pz['targeting_lift_vs_random']}x")

    result = {"dataset": {"n": len(data["records"]), "domains": data["domains"]},
              "auto_eval": ae, "issue_classification": cls,
              "failure_mode_analysis": fa, "personalization": pz}
    Path("reports").mkdir(exist_ok=True)
    Path("reports/community_support.json").write_text(json.dumps(result, indent=2, default=str))
    print("\nResults -> reports/community_support.json")
    return result


if __name__ == "__main__":
    main()

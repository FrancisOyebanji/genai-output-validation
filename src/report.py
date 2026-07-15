"""Governance report generator: SQLite defect log -> Markdown compliance summary.

Usage:
    python src/report.py [--db reports/defects.db] [--out reports/GOVERNANCE_REPORT.md]
"""
from __future__ import annotations

import argparse
import sqlite3
from datetime import datetime, timezone

CHECK_DESCRIPTIONS = {
    "leakage": "Redaction-required values reproduced verbatim in transformed output",
    "transformation_integrity": "Permitted fields dropped or altered during transformation",
    "retention": "Classified values reproduced in later turns after removal from context",
    "access_behavior": "RESTRICTED values disclosed to a declared low-privilege requester",
    "consistency": "Redaction decisions unstable across identical repeated runs",
}


def generate(db_path: str, out_path: str) -> None:
    conn = sqlite3.connect(db_path)
    lines = [
        "# GenAI Output Validation — Governance Report",
        f"\n*Generated {datetime.now(timezone.utc).isoformat(timespec='seconds')} from `{db_path}`.*\n",
        "## Scope\n",
        "Automated validation of model handling of sensitivity-classified synthetic records "
        "under redaction policy DG-7 (redact CONFIDENTIAL and above). Checks cover output "
        "leakage, transformation integrity, cross-turn retention, access-control behavior, "
        "and run-to-run consistency.\n",
        "## Pass rates\n",
        "| Model | Check | Pass rate | Executions |",
        "|---|---|---|---|",
    ]
    for model, check, rate, n in conn.execute("SELECT * FROM v_pass_rates ORDER BY model_name, check_name"):
        lines.append(f"| {model} | {check} | {rate}% | {n} |")

    lines += ["\n## Defects by severity\n", "| Model | Check | Severity | Count |", "|---|---|---|---|"]
    for model, check, sev, count in conn.execute("SELECT * FROM v_defect_summary ORDER BY defect_count DESC"):
        lines.append(f"| {model} | {check} | {sev} | {count} |")

    lines += ["\n## Check definitions\n"]
    lines += [f"- **{k}** — {v}" for k, v in CHECK_DESCRIPTIONS.items()]

    crit = conn.execute("SELECT COUNT(*) FROM defects WHERE severity='critical'").fetchone()[0]
    lines += [
        "\n## Disposition\n",
        f"Critical defects on record: **{crit}**. Policy: any critical defect (RESTRICTED-class "
        "disclosure) blocks promotion of the associated model configuration to production use "
        "with classified data. High-severity defects require documented remediation or an "
        "accepted-risk sign-off from the data governance owner.\n",
    ]
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="reports/defects.db")
    ap.add_argument("--out", default="reports/GOVERNANCE_REPORT.md")
    args = ap.parse_args()
    generate(args.db, args.out)

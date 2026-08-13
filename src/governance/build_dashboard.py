"""Responsible AI assurance dashboard from reports/rai_assessment.json."""
from __future__ import annotations

import json
from pathlib import Path

R = json.loads(Path("reports/rai_assessment.json").read_text())
inv = R["inventory"]; tier = R["risk_tier"]; ctrl = R["control_assurance"]
fair = R["fairness"]["metrics"]; gen = R["genai_evals"]["metrics"]

rows = "\n".join(
    f"<tr><td>{c['control_id']}</td><td>{c['name']}</td><td>{c['nist_ai_rmf']}</td>"
    f"<td>{c['eu_ai_act']}</td><td class='{ 'ok' if c['status']=='Met' else 'bad' if c['status']=='Not Met' else 'na'}'>{c['status']}</td></tr>"
    for c in ctrl["controls"])
tier_rows = "".join(f"<span class='pill'>{k}: {v}</span>" for k, v in inv["tier_distribution"].items())
metric_card = lambda label, m: (f"<tr><td>{label}</td><td>{m['value']}</td>"
    f"<td class='{'ok' if m['passed'] else 'bad'}'>{'PASS' if m['passed'] else 'FAIL'}</td></tr>")

html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Responsible AI Assurance</title>
<style>
 body{{font-family:'Segoe UI',system-ui,sans-serif;background:#f6f7fb;color:#1c2333;margin:0}}
 header{{background:#3b0a45;color:#fff;padding:16px 30px}} h1{{font-size:20px;margin:0}}
 .sub{{color:#e0c8ea;font-size:13px}}
 main{{max-width:1050px;margin:22px auto;padding:0 18px}}
 .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-bottom:20px}}
 .kpi{{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:16px}}
 .kpi .l{{color:#6b7280;font-size:13px}}.kpi .v{{font-size:22px;font-weight:700;margin-top:4px}}
 .kpi.high .v{{color:#b42318}}.kpi.bad .v{{color:#b42318}}.kpi.ok .v{{color:#14804a}}
 .panel{{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:18px;margin-bottom:18px}}
 .panel h2{{font-size:15px;margin:0 0 12px}}
 table{{width:100%;border-collapse:collapse;font-size:13px}}
 th,td{{text-align:left;padding:7px 9px;border-bottom:1px solid #eef0f4}}
 th{{background:#3b0a45;color:#fff;font-size:11px;text-transform:uppercase}}
 td.ok{{color:#14804a;font-weight:600}} td.bad{{color:#b42318;font-weight:600}} td.na{{color:#9aa3b2}}
 .pill{{display:inline-block;background:#efeafc;color:#5b3db8;border-radius:999px;padding:2px 10px;font-size:12px;margin-right:6px}}
 footer{{color:#6b7280;font-size:12px;text-align:center;margin:24px 0}}
</style></head><body>
<header><h1>Responsible AI Assurance — {R['assessed_system']}</h1>
<div class="sub">AI inventory · risk tiering · RAI evaluation · control assurance (NIST AI RMF · ISO 42001 · EU AI Act)</div></header>
<main>
<div class="kpis">
 <div class="kpi high"><div class="l">Risk tier</div><div class="v">{tier['tier'].upper()}</div></div>
 <div class="kpi"><div class="l">Risk score</div><div class="v">{tier.get('risk_score')}</div></div>
 <div class="kpi {'ok' if ctrl['assurance_status']=='APPROVED' else 'bad'}"><div class="l">Assurance</div><div class="v">{ctrl['assurance_pct']}%</div></div>
 <div class="kpi {'ok' if ctrl['assurance_status']=='APPROVED' else 'bad'}"><div class="l">Decision</div><div class="v">{ctrl['assurance_status']}</div></div>
</div>
<div class="panel"><h2>AI inventory ({inv['n_systems']} systems)</h2>{tier_rows}</div>
<div class="panel"><h2>Responsible AI evaluation results</h2>
 <table><tr><th>Dimension</th><th>Value</th><th>Status</th></tr>
 {metric_card('Fairness — disparate impact', fair['disparate_impact'])}
 {metric_card('Fairness — demographic parity diff', fair['demographic_parity_diff'])}
 {metric_card('Safety — groundedness', gen['groundedness'])}
 {metric_card('Safety — toxicity', gen['toxicity'])}
 {metric_card('Privacy — PII leakage', gen['pii_leakage'])}
 {metric_card('Oversight — refusal accuracy', gen['refusal_accuracy'])}
 </table></div>
<div class="panel"><h2>Control assurance — framework mapping</h2>
 <table><tr><th>ID</th><th>Control</th><th>NIST AI RMF</th><th>EU AI Act</th><th>Status</th></tr>
 {rows}</table></div>
</main>
<footer>Synthetic assessment · illustrative framework references, not legal advice · src/governance/build_dashboard.py</footer>
</body></html>"""
Path("reports").mkdir(exist_ok=True)
Path("reports/rai_dashboard.html").write_text(html, encoding="utf-8")
print("Dashboard written to reports/rai_dashboard.html")

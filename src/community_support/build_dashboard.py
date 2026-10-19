"""Community Support LLM/ML dashboard from reports/community_support.json."""
from __future__ import annotations

import json
from pathlib import Path

R = json.loads(Path("reports/community_support.json").read_text())
ae, cls, fa, pz = R["auto_eval"], R["issue_classification"], R["failure_mode_analysis"], R["personalization"]

dom_rows = fa["by_domain"]
dom_labels = [r["domain"] for r in dom_rows]
dom_fail = [round(r["failure_rate"] * 100, 1) for r in dom_rows]

kpis = [
    ("Auto-eval κ (failure modes)", f"{ae['failure_mode_kappa']:.2f}"),
    ("Auto-eval κ (quality)", f"{ae['quality_kappa']:.2f}"),
    ("Issue classifier F1", f"{cls['macro_f1']:.2f}"),
    ("Worst domain", fa["worst_domain"]),
    ("Personalization targeting lift", f"{pz['targeting_lift_vs_random']:.1f}x"),
    ("Segment uplift (true/measured)", f"{pz['true_priority_uplift']:.2f}/{pz['measured_segment_uplift']:.2f}"),
]
kpi_html = "".join(f"<div class='kpi'><div class='l'>{l}</div><div class='v'>{v}</div></div>" for l, v in kpis)

fm_rows = "".join(f"<tr><td style='text-align:left'>{m}</td><td>{n}</td></tr>"
                  for m, n in fa["top_failure_modes_overall"])

bars = "".join(
    f"<div style='display:flex;align-items:center;gap:8px;margin:4px 0'>"
    f"<div style='width:130px;font-size:12px'>{l}</div>"
    f"<div style='flex:1;background:#eef2f7;border-radius:4px'>"
    f"<div style='width:{v*2}%;background:#ff5a5f;height:14px;border-radius:4px'></div></div>"
    f"<div style='width:44px;font-size:12px;text-align:right'>{v}%</div></div>"
    for l, v in zip(dom_labels, dom_fail))

html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Community Support LLM/ML</title>
<style>
 body{{font-family:'Segoe UI',system-ui,sans-serif;background:#f6f7fa;color:#222;margin:0}}
 header{{background:#ff5a5f;color:#fff;padding:16px 30px}} h1{{font-size:20px;margin:0}}
 .sub{{color:#ffe3e4;font-size:13px}}
 main{{max-width:1080px;margin:22px auto;padding:0 18px}}
 .kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:20px}}
 .kpi{{background:#fff;border:1px solid #ece6e6;border-radius:12px;padding:16px}}
 .kpi .l{{color:#6b6b6b;font-size:13px}}.kpi .v{{font-size:21px;font-weight:700;margin-top:4px;color:#d93b40}}
 .grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
 .panel{{background:#fff;border:1px solid #ece6e6;border-radius:12px;padding:18px;margin-bottom:18px}}
 .panel h2{{font-size:15px;margin:0 0 12px}}
 table{{width:100%;border-collapse:collapse;font-size:13px}} th,td{{padding:7px 9px;border-bottom:1px solid #f0eded;text-align:center}}
 th{{color:#6b6b6b}}
 .note{{background:#fff0f0;border-left:4px solid #ff5a5f;padding:10px 14px;border-radius:6px;font-size:14px}}
 @media(max-width:800px){{.grid{{grid-template-columns:1fr}}}}
 footer{{color:#6b6b6b;font-size:12px;text-align:center;margin:24px 0}}
</style></head><body>
<header><h1>Community Support LLM/ML &mdash; evaluation, understanding & personalization</h1>
<div class="sub">Automated LLM evaluation &middot; synthetic dataset curation &middot; failure-mode detection &middot; personalization</div></header>
<main>
<div class="kpis">{kpi_html}</div>
<div class="grid">
 <div class="panel"><h2>Agent failure rate by CS domain</h2>{bars}
   <p style="font-size:13px;color:#6b6b6b;margin-top:10px">{fa['improvement_opportunity']}</p></div>
 <div class="panel"><h2>Automated evaluation vs human gold</h2>
   <table><tr><th style="text-align:left">eval task</th><th>accuracy</th><th>Cohen's κ</th></tr>
   <tr><td style="text-align:left">Failure-mode detection (objective)</td><td>{ae['failure_mode_accuracy']}</td><td>{ae['failure_mode_kappa']}</td></tr>
   <tr><td style="text-align:left">Quality rating (subjective)</td><td>{ae['quality_accuracy']}</td><td>{ae['quality_kappa']}</td></tr>
   <tr><td style="text-align:left">Policy compliance</td><td>{ae['policy_compliance_accuracy']}</td><td>&mdash;</td></tr></table>
   <h3 style="font-size:13px;margin:12px 0 4px">Top failure modes</h3>
   <table><tr><th style="text-align:left">mode</th><th>count</th></tr>{fm_rows}</table></div>
</div>
<div class="panel"><h2>Why it maps to the role</h2><div class="note">
 Automate LLM evaluation (κ {ae['failure_mode_kappa']} vs humans on failure modes, near-perfect on objective
 signals and honestly lower on subjective quality), curate synthetic datasets across CS domains,
 detect failure modes and improvement opportunities, and personalize handling to the segment that
 truly benefits (targeting {pz['targeting_lift_vs_random']}x vs random) &mdash; all graded against ground truth.
</div></div>
</main>
<footer>Synthetic data &middot; src/community_support/build_dashboard.py &middot; every model graded vs known ground truth</footer>
</body></html>"""
Path("reports").mkdir(exist_ok=True)
Path("reports/community_support_dashboard.html").write_text(html, encoding="utf-8")
print("Dashboard written to reports/community_support_dashboard.html")

"""
HTML Report Generator
Converts the TestLogger data dict into a polished, self-contained HTML report.
"""
from datetime import datetime
import html as _html


def _e(text: str) -> str:
    """HTML-escape a string."""
    return _html.escape(str(text or ""), quote=True)


def _fmt_ms(ms: float) -> str:
    """Format milliseconds as a human-readable duration."""
    if ms < 1000:
        return f"{ms:.0f}ms"
    elif ms < 60_000:
        return f"{ms/1000:.2f}s"
    else:
        minutes = int(ms // 60_000)
        seconds = (ms % 60_000) / 1000
        return f"{minutes}m {seconds:.1f}s"


class HTMLReportGenerator:
    """Generates a self-contained HTML test report from TestLogger data."""

    def generate(self, data: dict, output_path: str):
        features = data.get("features", [])
        summary  = data.get("summary", {})
        ts       = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = self._page_open(ts, summary)
        html += self._summary_chart(summary, features)
        html += self._overview_accordion(summary, features)
        html += self._summary_cards(summary, features)
        html += '<div class="features-section">\n'
        for fi, feature in enumerate(features):
            html += self._render_feature(fi, feature)
        html += '</div>\n'
        html += self._page_close()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

    # ── PAGE SHELL ────────────────────────────────────────────────────────────

    def _page_open(self, ts: str, summary: dict) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Test Execution Report</title>
<style>
@keyframes blink-blue {{
  0%,100% {{ background:#dbeafe; border-color:#3b82f6; color:#1e40af; }}
  50%      {{ background:#bfdbfe; border-color:#1d4ed8; color:#1e3a8a; }}
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;
     background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
     min-height:100vh;padding:20px;color:#333}}
.container{{max-width:1400px;margin:0 auto;background:white;border-radius:12px;
            box-shadow:0 20px 60px rgba(0,0,0,.3);overflow:hidden}}

/* HEADER */
.header{{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;
         padding:40px;text-align:center}}
.header h1{{font-size:2.5em;margin-bottom:10px;font-weight:700}}
.header .timestamp{{font-size:1em;opacity:.9}}

/* PILL CHART */
.summary-chart{{margin:24px 30px 20px;border:1px solid #e2e8f0;border-radius:16px;overflow:hidden;display:flex;min-height:42px}}
.summary-chart-segment{{display:flex;align-items:center;justify-content:center;font-size:.88rem;font-weight:700;color:#fff;min-width:34px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;cursor:default}}
.summary-chart-segment.passed{{background:#28a745}}
.summary-chart-segment.failed{{background:#dc3545}}
.summary-chart-segment.error{{background:#8b5cf6}}
.summary-chart-segment.skipped{{background:#f59e0b;color:#111}}

/* SUMMARY CARDS */
.summary-cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
                gap:20px;padding:30px;background:#f8f9fa}}
.summary-card{{background:white;padding:20px;border-radius:8px;
               box-shadow:0 2px 8px rgba(0,0,0,.1);text-align:center;transition:transform .2s}}
.summary-card:hover{{transform:translateY(-4px);box-shadow:0 4px 12px rgba(0,0,0,.15)}}
.summary-card .label{{font-size:.9em;color:#666;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px}}
.summary-card .value{{font-size:2.5em;font-weight:700;margin-bottom:5px}}
.summary-card .subtext{{font-size:.85em;color:#888}}
.summary-card.success .value{{color:#28a745}}
.summary-card.failure .value{{color:#dc3545}}
.summary-card.info    .value{{color:#667eea}}
.summary-card.warning .value{{color:#1d4ed8}}

/* OVERVIEW ACCORDION — matches .feature look exactly */
.overview-accordion{{margin:0 30px 20px;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden}}
.overview-header{{background:#f8f9fa;padding:16px 20px;cursor:pointer;
                 display:flex;align-items:center;transition:background .2s;
                 border-left:4px solid #667eea}}
.overview-header:hover{{background:#e9ecef}}
.overview-title{{flex:1;display:flex;align-items:center;gap:10px;min-width:0}}
.overview-title h2{{font-size:1.2em;font-weight:600}}
.overview-content{{max-height:0;overflow:hidden;transition:max-height .35s ease-out}}
.overview-content.expanded{{max-height:60000px}}
.overview-body{{padding:24px;background:white}}

.graph-row{{display:flex;gap:30px;flex-wrap:wrap;margin-bottom:24px}}
.donut-wrap{{text-align:center}}
.feature-bar-row{{display:flex;align-items:center;gap:10px;margin-bottom:8px}}
.feature-bar-label{{width:160px;font-size:.82em;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.feature-bar-track{{flex:1;height:16px;border-radius:8px;overflow:hidden;display:flex;background:#eee}}

.insights-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;
                border-top:1px solid #eee;padding-top:20px}}
.insight-card{{background:#fafbfc;border:1px solid #eceef1;border-radius:10px;padding:16px;transition:box-shadow .2s}}
.insight-card:hover{{box-shadow:0 2px 8px rgba(0,0,0,.06)}}
.insight-card-title{{display:flex;align-items:center;gap:6px;font-size:.75em;font-weight:700;color:#667eea;text-transform:uppercase;letter-spacing:.06em;margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid #eee}}
.insight-row{{display:flex;justify-content:space-between;align-items:center;padding:6px 0;font-size:.85em;border-bottom:1px dashed #eee}}
.insight-row:last-child{{border-bottom:none}}
.insight-row .metric{{font-family:'Courier New',monospace;font-weight:700;color:#333;flex-shrink:0;margin-left:10px}}
.insight-row .label{{color:#555;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.insight-row.rate-high .metric{{color:#28a745}}
.insight-row.rate-low .metric{{color:#dc3545}}
.insight-empty{{color:#aaa;font-style:italic;font-size:.85em}}

.row-right{{display:flex;align-items:center;gap:8px;flex-shrink:0}}
.duration{{font-size:.85em;font-weight:500;font-family:'Courier New',monospace;
           color:#666;width:90px;text-align:right}}
.toggle-icon{{width:28px;height:28px;border-radius:50%;background:#dee2e6;color:#666;
              display:flex;align-items:center;justify-content:center;font-size:.7em;
              transition:transform .3s,background .2s;flex-shrink:0;margin-left:4px}}
.toggle-icon.expanded{{transform:rotate(180deg)}}
.overview-header:hover .toggle-icon{{background:#ced4da}}
.feature-header:hover .toggle-icon{{background:#ced4da}}

/* STATUS BADGES */
.status-badge{{padding:3px 10px;border-radius:20px;font-size:.72em;font-weight:600;
               text-transform:uppercase;letter-spacing:.6px;min-width:64px;
               text-align:center;display:inline-block;white-space:nowrap}}
.status-badge.passed    {{background:#e6f9ed;color:#1e7e34;border:1px solid #b8e8c8}}
.status-badge.failed    {{background:#fdecea;color:#b71c1c;border:1px solid #f5c6cb}}
.status-badge.partial   {{background:#fff8e1;color:#8a6500;border:1px solid #ffe082}}
.status-badge.running   {{background:#e3f6fb;color:#0277bd;border:1px solid #b3e5fc}}
.status-badge.skipped   {{background:#f3f4f6;color:#6b7280;border:1px solid #d1d5db}}
.status-badge.undefined {{animation:blink-blue 1.4s ease-in-out infinite;
                          border:1px solid #3b82f6;font-weight:700}}

/* FEATURES */
.features-section{{padding:30px}}
.feature{{margin-bottom:24px;border:1px solid #e0e0e0;border-radius:8px;overflow:hidden}}

.feature-header{{background:#f8f9fa;padding:16px 20px;cursor:pointer;
                 display:flex;align-items:center;transition:background .2s;
                 border-left:4px solid transparent}}
.feature-header:hover{{background:#e9ecef}}
.feature-header.passed    {{border-left-color:#28a745}}
.feature-header.failed    {{border-left-color:#dc3545}}
.feature-header.partial   {{border-left-color:#ffc107}}
.feature-header.undefined {{border-left-color:#3b82f6}}
.feature-title{{flex:1;display:flex;align-items:center;gap:10px;min-width:0}}
.feature-title h2{{font-size:1.2em;font-weight:600;white-space:nowrap;
                   overflow:hidden;text-overflow:ellipsis}}
.feature-content{{max-height:0;overflow:hidden;transition:max-height .35s ease-out}}
.feature-content.expanded{{max-height:60000px}}

.feature-summary{{background:#f0f4ff;padding:12px 20px;border-bottom:1px solid #e0e0e0;
                  display:flex;gap:30px;flex-wrap:wrap}}
.feature-stat{{text-align:center;min-width:80px}}
.feature-stat-label{{font-size:.72em;color:#888;text-transform:uppercase;letter-spacing:.5px}}
.feature-stat-value{{font-size:1.4em;font-weight:700;margin-top:2px}}
.feature-stat.success   .feature-stat-value{{color:#28a745}}
.feature-stat.failure   .feature-stat-value{{color:#dc3545}}
.feature-stat.info      .feature-stat-value{{color:#667eea}}
.feature-stat.undefined .feature-stat-value{{color:#1d4ed8}}

/* SCENARIOS */
.scenario{{border-top:1px solid #e0e0e0;background:white}}
.scenario-header{{padding:12px 20px 12px 36px;cursor:pointer;display:flex;
                  align-items:center;gap:10px;transition:background .2s}}
.scenario-header:hover{{background:#f8f9fa}}
.scenario-title{{flex:1;display:flex;align-items:center;gap:10px;min-width:0}}
.scenario-title h3{{font-size:1em;font-weight:600;white-space:nowrap;
                    overflow:hidden;text-overflow:ellipsis}}
.scenario-content{{max-height:0;overflow:hidden;transition:max-height .3s ease-out;background:#fafafa}}
.scenario-content.expanded{{max-height:30000px}}

/* STEPS */
.step{{border-top:1px solid #eee}}
.step-header{{padding:10px 20px 10px 36px;cursor:pointer;display:flex;
              align-items:center;gap:8px;transition:background .2s}}
.step-header:hover             {{background:#f5f5f5}}
.step-header.passed            {{background:#f8fff9}}
.step-header.failed            {{background:#fff8f8}}
.step-header.passed:hover      {{background:#edfff0}}
.step-header.failed:hover      {{background:#fff0f0}}
.step-header.undefined         {{background:#eff6ff}}
.step-header.undefined:hover   {{background:#dbeafe}}
.step-header.skipped           {{background:#f9fafb;opacity:.75}}
.step-header.skipped:hover     {{background:#f3f4f6;opacity:1}}

.step-arrow{{width:22px;height:22px;font-size:.62em;background:#dee2e6;border-radius:50%;
             color:#777;display:flex;align-items:center;justify-content:center;
             flex-shrink:0;transition:transform .3s,background .2s;margin-right:2px}}
.step-arrow.expanded{{transform:rotate(180deg)}}
.step-header:hover .step-arrow{{background:#ced4da}}
.step-icon{{font-size:1em;width:20px;text-align:center;flex-shrink:0;color:#555}}
.step-text{{font-size:.92em;font-weight:500;min-width:0;display:block}}
.step-text.skipped-text   {{color:#9ca3af;font-style:italic}}
.step-text.undefined-text {{color:#1d4ed8;font-weight:600}}
.step-text-col{{flex:1;display:flex;flex-direction:column;gap:4px;min-width:0}}
.step-strategy-pills{{display:flex;flex-wrap:wrap;gap:4px;margin-top:2px}}
.strategy-pill{{font-size:.70em;font-weight:700;padding:1px 7px;border-radius:10px;
                white-space:nowrap;letter-spacing:.3px}}
.pill-win{{background:#d4edda;color:#155724;border:1px solid #c3e6cb}}
.pill-loss{{background:#f8d7da;color:#721c24;border:1px solid #f5c6cb}}
.step-details{{max-height:0;overflow:hidden;transition:max-height .3s ease-out}}
.step-details.expanded{{max-height:20000px}}
.step-content{{padding:16px 20px 16px 52px;background:white;border-top:1px solid #eee}}

/* NOT-IMPLEMENTED BANNER */
.not-implemented-banner{{
  display:flex;align-items:center;gap:10px;
  padding:10px 14px;margin-bottom:14px;
  background:#dbeafe;border:1.5px solid #3b82f6;border-radius:6px;
  animation:blink-blue 1.4s ease-in-out infinite;
}}
.not-implemented-banner .ni-icon{{font-size:1.2em}}
.not-implemented-banner .ni-text{{font-size:.9em;font-weight:600;color:#1e40af}}
.not-implemented-banner .ni-sub{{font-size:.8em;color:#1d4ed8;margin-top:2px}}

/* STRATEGY ATTEMPTS */
.strategies-section{{margin-bottom:16px}}
.strategies-title{{font-weight:600;margin-bottom:8px;color:#555;
                   font-size:.88em;text-transform:uppercase;letter-spacing:.5px}}
.strategy-item{{padding:8px 12px;margin-bottom:6px;border-radius:6px;border-left:3px solid;
                display:flex;justify-content:space-between;align-items:flex-start;gap:8px}}
.strategy-item.success{{background:#e8f5e9;border-color:#28a745}}
.strategy-item.failure{{background:#fdecea;border-color:#dc3545}}
.strategy-info{{flex:1}}
.strategy-type{{font-weight:700;margin-bottom:2px;font-size:.88em}}
.strategy-name{{font-size:.82em;color:#555;font-family:'Courier New',monospace;
                margin-bottom:2px;word-break:break-all}}
.strategy-message{{font-size:.85em;color:#666}}
.strategy-meta{{display:flex;flex-direction:column;align-items:flex-end;gap:2px;flex-shrink:0}}
.strategy-duration{{font-size:.8em;color:#888;font-weight:500;font-family:'Courier New',monospace}}

/* LOGS */
.logs-section{{margin-top:16px}}
.logs-title{{font-weight:600;margin-bottom:8px;color:#555;
             font-size:.88em;text-transform:uppercase;letter-spacing:.5px}}
.log-entry{{padding:6px 10px;margin-bottom:4px;border-radius:4px;font-size:.85em;
            font-family:'Courier New',monospace;border-left:3px solid;word-wrap:break-word}}
.log-entry.info   {{background:#e7f3ff;border-color:#2196F3;color:#0c5c9e}}
.log-entry.success{{background:#e8f5e9;border-color:#4CAF50;color:#2e7d32}}
.log-entry.warning{{background:#fff8e1;border-color:#FFC107;color:#f57c00}}
.log-entry.error  {{background:#ffebee;border-color:#f44336;color:#c62828}}
.log-entry.debug  {{background:#f5f5f5;border-color:#9e9e9e;color:#555}}
.log-timestamp    {{font-size:.82em;color:#aaa;margin-right:6px}}

/* ERRORS */
.error-section{{margin-top:12px;padding:16px;background:#fff5f5;
                border:1.5px solid #f5c6cb;border-radius:6px}}
.error-title  {{font-weight:700;color:#dc3545;margin-bottom:10px}}
.error-type   {{font-weight:700;color:#dc3545;margin-bottom:6px;font-size:.9em}}
.error-message{{font-family:'Courier New',monospace;font-size:.85em;color:#721c24;
                background:white;padding:12px;border-radius:4px;border-left:3px solid #dc3545;
                white-space:pre-wrap;word-wrap:break-word;line-height:1.5}}
.error-stack  {{color:#555;font-family:'Courier New',monospace;font-size:.82em;
                white-space:pre-wrap;margin-top:8px}}

/* EMPTY STATE */
.no-logs{{padding:8px;color:#aaa;font-style:italic;font-size:.88em}}

@media print{{
  body{{background:white;padding:0}}
  .container{{box-shadow:none}}
  .feature-content,.scenario-content,.step-details,.overview-content{{max-height:none!important}}
}}
</style>
</head>
<body>
<div class="container">
<div class="header">
  <h1>&#x1F9EA; Test Execution Report</h1>
  <div class="timestamp">Generated on {_e(ts)}</div>
</div>
"""

    def _page_close(self) -> str:
        return """
</div>
<script>
function toggleFeature(idx) {
  document.getElementById('feature-content-'+idx).classList.toggle('expanded');
  document.getElementById('feature-toggle-'+idx).classList.toggle('expanded');
}
function toggleScenario(id) {
  document.getElementById('scenario-content-'+id).classList.toggle('expanded');
  document.getElementById('scenario-toggle-'+id).classList.toggle('expanded');
}
function toggleStep(id) {
  document.getElementById('step-details-'+id).classList.toggle('expanded');
  document.getElementById('step-toggle-'+id).classList.toggle('expanded');
}
function toggleOverview() {
  document.getElementById('overview-content').classList.toggle('expanded');
  document.getElementById('overview-toggle').classList.toggle('expanded');
}
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.feature-header.failed, .feature-header.undefined').forEach(function(h) {
    var m = h.getAttribute('onclick').match(/\\d+/);
    if (m) {
      document.getElementById('feature-content-'+m[0]).classList.add('expanded');
      document.getElementById('feature-toggle-'+m[0]).classList.add('expanded');
    }
  });
  document.querySelectorAll('.scenario-header').forEach(function(h) {
    var badge = h.querySelector('.status-badge.failed, .status-badge.undefined');
    if (badge) {
      var m = h.getAttribute('onclick').match(/'([^']+)'/);
      if (m) {
        document.getElementById('scenario-content-'+m[1]).classList.add('expanded');
        document.getElementById('scenario-toggle-'+m[1]).classList.add('expanded');
      }
    }
  });
  document.querySelectorAll('.step-header.failed, .step-header.undefined').forEach(function(h) {
    var m = h.getAttribute('onclick').match(/'([^']+)'/);
    if (!m) return;
    document.getElementById('step-details-'+m[1]).classList.add('expanded');
    document.getElementById('step-toggle-'+m[1]).classList.add('expanded');
  });
});
</script>
</body>
</html>
"""

    # ── PILL CHART ────────────────────────────────────────────────────────────

    def _summary_chart(self, s: dict, features: list) -> str:
        passed    = s.get('passed_steps', 0)
        failed    = s.get('failed_steps', 0)
        skipped   = s.get('skipped_steps', 0)
        undefined = s.get('undefined_steps', 0)

        error = 0
        for feature in features:
            for scenario in feature.get('scenarios', []):
                for step in scenario.get('steps', []):
                    if step.get('status') == 'failed' and step.get('error'):
                        error += 1

        failed_no_error = max(failed - error, 0)
        chart_total = passed + failed_no_error + error + skipped + undefined
        chart_total = chart_total or 1
        passed_pct  = passed / chart_total * 100
        failed_pct  = failed_no_error / chart_total * 100
        error_pct   = error / chart_total * 100
        skipped_pct = (skipped + undefined) / chart_total * 100

        skipped_total = skipped + undefined
        segments_data = [
            ('passed',  passed,          passed_pct,  'Passed'),
            ('failed',  failed_no_error, failed_pct,  'Failed'),
            ('error',   error,           error_pct,   'Error'),
            ('skipped', skipped_total,   skipped_pct, 'Skipped'),
        ]

        segments_html = "".join(
            f'<div class="summary-chart-segment {css}" style="width:{pct:.1f}%" '
            f'title="{label}: {count}">{label} {count}</div>'
            for css, count, pct, label in segments_data
            if count > 0
        )

        return f"""
          <div class="summary-chart">
            {segments_html}
          </div>
          """
    
#         return f"""
# <div class="summary-chart">
#   <div class="summary-chart-segment passed" style="width:{passed_pct:.1f}%" title="Passed: {passed}">Passed {passed}</div>
#   <div class="summary-chart-segment failed" style="width:{failed_pct:.1f}%" title="Failed: {failed_no_error}">Failed {failed_no_error}</div>
#   <div class="summary-chart-segment error" style="width:{error_pct:.1f}%" title="Error: {error}">Error {error}</div>
#   <div class="summary-chart-segment skipped" style="width:{skipped_pct:.1f}%" title="Skipped: {skipped + undefined}">Skipped {skipped + undefined}</div>
# </div>
# """

    # ── SUMMARY CARDS (tiles) ─────────────────────────────────────────────────

    def _summary_cards(self, s: dict, features: list) -> str:
        total     = s.get('total_steps', 0)
        passed    = s.get('passed_steps', 0)
        failed    = s.get('failed_steps', 0)
        skipped   = s.get('skipped_steps', 0)
        undefined = s.get('undefined_steps', 0)
        rate      = f"{passed/total*100:.0f}%" if total else "0%"
        dur       = _fmt_ms(s.get('total_duration_ms', 0))

        tf  = s.get('total_features', 0)
        pf  = s.get('passed_features', 0)
        ff  = s.get('failed_features', 0)
        ts_ = s.get('total_scenarios', 0)
        ps  = s.get('passed_scenarios', 0)
        fs  = s.get('failed_scenarios', 0)

        error = 0
        for feature in features:
            for scenario in feature.get('scenarios', []):
                for step in scenario.get('steps', []):
                    if step.get('status') == 'failed' and step.get('error'):
                        error += 1

        return f"""
<div class="summary-cards">
  <div class="summary-card info">
    <div class="label">Total Features</div>
    <div class="value">{tf}</div>
    <div class="subtext">&#x2713; {pf} Passed &nbsp; &#x2717; {ff} Failed</div>
  </div>
  <div class="summary-card info">
    <div class="label">Total Scenarios</div>
    <div class="value">{ts_}</div>
    <div class="subtext">&#x2713; {ps} Passed &nbsp; &#x2717; {fs} Failed</div>
  </div>
  <div class="summary-card success">
    <div class="label">Passed Steps</div>
    <div class="value">{passed}</div>
    <div class="subtext">of {total} total</div>
  </div>
  <div class="summary-card failure">
    <div class="label">Failed Steps</div>
    <div class="value">{failed}</div>
    <div class="subtext">of {total} total</div>
  </div>
  <div class="summary-card warning">
    <div class="label">Not Implemented</div>
    <div class="value">{undefined}</div>
    <div class="subtext">&#x2B;{skipped} skipped after</div>
  </div>
  <div class="summary-card info">
    <div class="label">Total Duration</div>
    <div class="value">{_e(dur)}</div>
    <div class="subtext">execution time</div>
  </div>
  <div class="summary-card failure">
    <div class="label">Error Steps</div>
    <div class="value">{error}</div>
    <div class="subtext">failed with error text</div>
  </div>
  <div class="summary-card {'failure' if failed else 'success'}">
    <div class="label">Success Rate</div>
    <div class="value">{_e(rate)}</div>
    <div class="subtext">overall</div>
  </div>
</div>
"""

    # ── OVERVIEW ACCORDION (donut + per-feature bars + insights) ────────────

    def _overview_accordion(self, s: dict, features: list) -> str:
        passed  = s.get('passed_steps', 0)
        failed  = s.get('failed_steps', 0)
        skipped = s.get('skipped_steps', 0)
        undef   = s.get('undefined_steps', 0)
        total   = passed + failed + skipped + undef
        total   = total or 1

        segs = [
            ('#28a745', passed),
            ('#dc3545', failed),
            ('#f59e0b', skipped),
            ('#3b82f6', undef),
        ]
        r, cx, cy = 60, 70, 70
        circumference = 2 * 3.14159265 * r
        offset = 0
        donut_svg = '<svg width="140" height="140" viewBox="0 0 140 140">'
        donut_svg += f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#eee" stroke-width="20"/>'
        for color, val in segs:
            frac = val / total
            length = frac * circumference
            donut_svg += (
                f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" '
                f'stroke-width="20" stroke-dasharray="{length:.1f} {circumference:.1f}" '
                f'stroke-dashoffset="{-offset:.1f}" transform="rotate(-90 {cx} {cy})"/>'
            )
            offset += length
        donut_svg += (
            f'<text x="{cx}" y="{cy}" text-anchor="middle" dy=".3em" '
            f'font-size="20" font-weight="700" fill="#333">{passed}/{total}</text>'
        )
        donut_svg += '</svg>'

        legend = ''.join(
            f'<div style="display:flex;align-items:center;gap:6px;font-size:.8em;margin-bottom:4px">'
            f'<span style="width:10px;height:10px;background:{c};border-radius:2px;display:inline-block"></span>'
            f'{label} {val}</div>'
            for c, val, label in [
                ('#28a745', passed, 'Passed'),
                ('#dc3545', failed, 'Failed'),
                ('#f59e0b', skipped, 'Skipped'),
                ('#3b82f6', undef, 'Undefined'),
            ]
        )

        bars = ''
        for feature in features:
            name = feature.get('feature_name', 'Unnamed')
            steps = [st for sc in feature.get('scenarios', []) for st in sc.get('steps', [])]
            ft = len(steps) or 1
            fp = sum(1 for st in steps if st.get('status') == 'passed')
            ff_ = sum(1 for st in steps if st.get('status') == 'failed')
            fsk = sum(1 for st in steps if st.get('status') in ('skipped', 'undefined'))
            bars += f'''
<div class="feature-bar-row">
  <div class="feature-bar-label" title="{_e(name)}">{_e(name)}</div>
  <div class="feature-bar-track">
    <div style="width:{fp/ft*100:.1f}%;background:#28a745" title="Passed {fp}"></div>
    <div style="width:{ff_/ft*100:.1f}%;background:#dc3545" title="Failed {ff_}"></div>
    <div style="width:{fsk/ft*100:.1f}%;background:#f59e0b" title="Skipped {fsk}"></div>
  </div>
  <div style="width:40px;font-size:.78em;color:#666;text-align:right">{fp}/{ft}</div>
</div>
'''

        all_steps = [
            st for f in features
            for sc in f.get('scenarios', [])
            for st in sc.get('steps', [])
        ]

        slowest = sorted(all_steps, key=lambda st: st.get('duration_ms', 0), reverse=True)[:5]
        slow_html = "".join(
            f'<div class="insight-row"><span class="label">{_e(st.get("step_text","")[:50])}</span>'
            f'<span class="metric">{_fmt_ms(st.get("duration_ms",0))}</span></div>'
            for st in slowest
        ) or '<div class="insight-empty">No step data</div>'

        fail_counts = {}
        for st in all_steps:
            if st.get('status') == 'failed' and st.get('error'):
                key = st['error'].split("Message:")[-1].strip()[:60]
                fail_counts[key] = fail_counts.get(key, 0) + 1
        top_fail = sorted(fail_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        fail_html = "".join(
            f'<div class="insight-row"><span class="label">{_e(msg)}</span>'
            f'<span class="metric">{count}x</span></div>'
            for msg, count in top_fail
        ) or '<div class="insight-empty">No failures</div>'

        strat_stats = {}
        for st in all_steps:
            for strat in st.get('strategies', []):
                t = strat.get('strategy_type', 'Unknown')
                d = strat_stats.setdefault(t, {'win': 0, 'total': 0})
                d['total'] += 1
                if strat.get('success'):
                    d['win'] += 1
        strat_html = ""
        for t, d in sorted(strat_stats.items(), key=lambda x: x[1]['total'], reverse=True):
            pct = d['win'] / d['total'] * 100
            css = 'rate-high' if pct >= 70 else 'rate-low'
            strat_html += (
                f'<div class="insight-row {css}"><span class="label">{_e(t)}</span>'
                f'<span class="metric">{d["win"]}/{d["total"]} ({pct:.0f}%)</span></div>'
            )
        strat_html = strat_html or '<div class="insight-empty">No strategy data</div>'

        return f'''
<div class="overview-accordion">
  <div class="overview-header" onclick="toggleOverview()">
    <div class="overview-title">
      <h2>&#x1F4CA; Test Insights &amp; Overview</h2>
    </div>
    <div class="row-right">
      <div class="toggle-icon" id="overview-toggle">&#9660;</div>
    </div>
  </div>
  <div class="overview-content" id="overview-content">
    <div class="overview-body">
      <div class="graph-row">
        <div class="donut-wrap">
          {donut_svg}
          <div style="margin-top:10px;text-align:left">{legend}</div>
        </div>
        <div style="flex:1;min-width:280px">
          <div style="font-weight:600;margin-bottom:10px;font-size:.85em;color:#555;text-transform:uppercase">Per-Feature Breakdown</div>
          {bars}
        </div>
      </div>
      <div class="insights-grid">
        <div class="insight-card">
          <div class="insight-card-title">&#x23F1; Slowest Steps</div>
          {slow_html}
        </div>
        <div class="insight-card">
          <div class="insight-card-title">&#x274C; Top Failure Reasons</div>
          {fail_html}
        </div>
        <div class="insight-card">
          <div class="insight-card-title">&#x1F3AF; Locator Strategy Success Rates</div>
          {strat_html}
        </div>
      </div>
    </div>
  </div>
</div>
'''

    # ── FEATURE ───────────────────────────────────────────────────────────────

    def _render_feature(self, fi: int, feature: dict) -> str:
        status    = feature.get('status', 'unknown')
        name      = feature.get('feature_name', 'Unnamed Feature')
        dur       = _fmt_ms(feature.get('duration_ms', 0))
        scenarios = feature.get('scenarios', [])

        all_steps    = [st for s in scenarios for st in s.get('steps', [])]
        passed_steps = sum(1 for st in all_steps if st.get('status') == 'passed')
        failed_steps = sum(1 for st in all_steps if st.get('status') == 'failed')
        undef_steps  = sum(1 for st in all_steps if st.get('status') == 'undefined')
        skip_steps   = sum(1 for st in all_steps if st.get('status') == 'skipped')
        total_steps  = len(all_steps)
        rate         = f"{passed_steps/total_steps*100:.0f}%" if total_steps else "0%"

        display_status = status
        if undef_steps > 0 and status not in ('failed',):
            display_status = 'undefined'

        body = f"""
<div class="feature">
  <div class="feature-header {_e(display_status)}" onclick="toggleFeature({fi})">
    <div class="feature-title">
      <h2>&#x1F4CB; {_e(name)}</h2>
      <span class="status-badge {_e(display_status)}">{_e(display_status.upper())}</span>
    </div>
    <div class="row-right">
      <span class="duration">&#x23F1; {_e(dur)}</span>
      <div class="toggle-icon" id="feature-toggle-{fi}">&#9660;</div>
    </div>
  </div>
  <div class="feature-content" id="feature-content-{fi}">
    <div class="feature-summary">
      <div class="feature-stat info">
        <div class="feature-stat-label">Scenarios</div>
        <div class="feature-stat-value">{len(scenarios)}</div>
      </div>
      <div class="feature-stat success">
        <div class="feature-stat-label">Passed</div>
        <div class="feature-stat-value">{passed_steps}</div>
      </div>
      <div class="feature-stat failure">
        <div class="feature-stat-label">Failed</div>
        <div class="feature-stat-value">{failed_steps}</div>
      </div>
      <div class="feature-stat undefined">
        <div class="feature-stat-label">Not Impl.</div>
        <div class="feature-stat-value">{undef_steps}</div>
      </div>
      <div class="feature-stat info">
        <div class="feature-stat-label">Skipped</div>
        <div class="feature-stat-value">{skip_steps}</div>
      </div>
      <div class="feature-stat {'success' if failed_steps == 0 and undef_steps == 0 else 'failure'}">
        <div class="feature-stat-label">Success Rate</div>
        <div class="feature-stat-value">{_e(rate)}</div>
      </div>
    </div>
"""
        for si, scenario in enumerate(scenarios):
            body += self._render_scenario(fi, si, scenario)

        body += "  </div>\n</div>\n"
        return body

    # ── SCENARIO ──────────────────────────────────────────────────────────────

    def _render_scenario(self, fi: int, si: int, scenario: dict) -> str:
        sid    = f"f{fi}-s{si}"
        status = scenario.get('status', 'unknown')
        name   = scenario.get('scenario_name', 'Unnamed Scenario')
        dur    = _fmt_ms(scenario.get('duration_ms', 0))
        steps  = scenario.get('steps', [])

        has_undefined = any(st.get('status') == 'undefined' for st in steps)
        display_status = status
        if has_undefined and status not in ('failed',):
            display_status = 'undefined'

        body = f"""
<div class="scenario">
  <div class="scenario-header" onclick="toggleScenario('{sid}')">
    <div class="scenario-title">
      <span style="color:#999;font-size:.85em;">&#x1F4DD;</span>
      <h3>{_e(name)}</h3>
    </div>
    <div class="row-right">
      <span class="status-badge {_e(display_status)}">{_e(display_status.upper())}</span>
      <span class="duration">&#x23F1; {_e(dur)}</span>
      <div class="toggle-icon" id="scenario-toggle-{sid}">&#9660;</div>
    </div>
  </div>
  <div class="scenario-content" id="scenario-content-{sid}">
"""
        for sti, step in enumerate(steps):
            body += self._render_step(sid, sti, step)

        body += "  </div>\n</div>\n"
        return body

    # ── STEP ──────────────────────────────────────────────────────────────────

    def _render_step(self, sid: str, sti: int, step: dict) -> str:
        step_id    = f"{sid}-step{sti}"
        status     = step.get('status', 'unknown')
        text       = step.get('step_text', '')
        dur        = _fmt_ms(step.get('duration_ms', 0))
        strategies = step.get('strategies', [])
        logs       = step.get('logs', [])
        error      = step.get('error')

        if status == 'passed':
            icon       = '&#x2713;'
            icon_color = '#28a745'
            text_class = ''
        elif status == 'failed':
            icon       = '&#x2717;'
            icon_color = '#dc3545'
            text_class = ''
        elif status == 'undefined':
            icon       = '&#x26A0;'
            icon_color = '#1d4ed8'
            text_class = 'undefined-text'
        else:
            icon       = '&#x2014;'
            icon_color = '#9ca3af'
            text_class = 'skipped-text'

        dur_color = '#9ca3af' if status in ('skipped', 'undefined') else '#666'

        inline_pills = ""
        if strategies:
            pills = []
            for s in strategies:
                won  = s.get('success', False)
                tick = '&#x2714;' if won else '&#x2718;'
                css  = 'pill-win' if won else 'pill-loss'
                pills.append(f'<span class="strategy-pill {css}">{tick} {_e(s.get("strategy_type",""))}</span>')
            inline_pills = '<div class="step-strategy-pills">' + "".join(pills) + '</div>'

        body = f'''
<div class="step">
  <div class="step-header {_e(status)}" onclick="toggleStep(\'{step_id}\')">
    <div class="step-arrow" id="step-toggle-{step_id}">&#9660;</div>
    <span class="step-icon" style="color:{icon_color}">{icon}</span>
    <div class="step-text-col">
      <span class="step-text {text_class}">{_e(text)}</span>
      {inline_pills}
    </div>
    <div class="row-right">
      <span class="status-badge {_e(status)}">{_e(status.upper())}</span>
      <span class="duration" style="color:{dur_color}">&#x23F1; {_e(dur)}</span>
    </div>
  </div>
  <div class="step-details" id="step-details-{step_id}">
    <div class="step-content">
'''
        if status == 'undefined':
            body += '''
<div class="not-implemented-banner">
  <span class="ni-icon">&#x1F6AB;</span>
  <div>
    <div class="ni-text">Step Not Implemented</div>
    <div class="ni-sub">Add a @step definition for this step to execute it.</div>
  </div>
</div>
'''

        if status == 'skipped':
            body += '''
<div style="padding:8px 12px;background:#f3f4f6;border-left:3px solid #d1d5db;
            border-radius:4px;margin-bottom:12px;font-size:.85em;color:#6b7280;font-style:italic;">
  &#x23ED; Not executed — a prior step in this scenario was not implemented or failed.
</div>
'''

        if strategies:
            body += '<div class="strategies-section">\n'
            body += '<div class="strategies-title">&#x1F50D; Locator Strategy Attempts</div>\n'
            for s in strategies:
                css    = "success" if s.get('success') else "failure"
                s_type = s.get('strategy_type', '')
                s_name = s.get('strategy_name', '')
                s_msg  = s.get('message', '')
                s_dur  = _fmt_ms(s.get('duration_ms', 0))
                tick   = '&#x2714;' if s.get('success') else '&#x2718;'
                body += f'''
<div class="strategy-item {css}">
  <div class="strategy-info">
    <div class="strategy-type">{tick} {_e(s_type)}</div>
    <div class="strategy-name">{_e(s_name)}</div>
    <div class="strategy-message">{_e(s_msg)}</div>
  </div>
  <div class="strategy-meta">
    <span class="strategy-duration">{_e(s_dur)}</span>
  </div>
</div>
'''
            body += '</div>\n'

        display_logs = [
            lg for lg in logs
            if lg.get('level') not in ('debug',)
            and not (lg.get('level') == 'info' and lg.get('message', '') == 'Step passed')
        ]
        if display_logs:
            body += '<div class="logs-section">\n'
            body += '<div class="logs-title">&#x1F4CB; Step Logs</div>\n'
            for lg in display_logs:
                level    = lg.get('level', 'info')
                msg      = lg.get('message', '')
                ts       = lg.get('timestamp', '')
                ts_short = ts[11:19] if len(ts) >= 19 else ts
                body += (
                    f'<div class="log-entry {_e(level)}">'
                    f'<span class="log-timestamp">{_e(ts_short)}</span>'
                    f'{_e(msg)}'
                    f'</div>\n'
                )
            body += '</div>\n'

        if error:
            error_type  = "Error"
            error_msg   = error
            error_stack = ""
            if "Message:" in error:
                parts      = error.split("Message:", 1)
                error_type = parts[0].replace("Type:", "").strip() or "Error"
                rest       = parts[1]
                if "Stacktrace:" in rest:
                    msg_part, stack_part = rest.split("Stacktrace:", 1)
                    error_msg   = msg_part.strip()
                    error_stack = stack_part.strip()
                else:
                    error_msg = rest.strip()
            body += f'''
<div class="error-section">
  <div class="error-title">&#x274C; Error Details</div>
  <div class="error-type">Type: {_e(error_type)}</div>
  <div class="error-message">{_e(error_msg)}</div>
'''
            if error_stack:
                body += f'<div class="error-stack">{_e(error_stack)}</div>\n'
            body += '</div>\n'

        if not strategies and not display_logs and not error and status not in ('undefined', 'skipped'):
            body += '<div class="no-logs">No detailed logs for this step.</div>\n'

        body += "    </div>\n  </div>\n</div>\n"
        return body
   
"""
reporter.py — Generates a professional HTML security report from scan results.

The report is self-contained (no external CSS/JS dependencies) so it can be
shared as a single .html file or hosted as a GitHub Pages artifact.

Usage:
    from scanner.reporter import generate_report
    generate_report(scan_result, output_path="report.html")
"""

from datetime import datetime
from pathlib import Path
from .core import ScanResult
from .detectors import Verdict
from .payloads import Severity


# Verdict display config
VERDICT_CONFIG = {
    Verdict.VULNERABLE: {"label": "VULNERABLE", "color": "#e74c3c", "bg": "#fdf2f1", "icon": "🔴"},
    Verdict.SUSPICIOUS: {"label": "SUSPICIOUS", "color": "#f39c12", "bg": "#fef9ef", "icon": "🟡"},
    Verdict.SAFE:       {"label": "SAFE",       "color": "#27ae60", "bg": "#f0faf4", "icon": "🟢"},
    Verdict.ERROR:      {"label": "ERROR",      "color": "#95a5a6", "bg": "#f8f9fa", "icon": "⚪"},
}

SEVERITY_COLORS = {
    Severity.CRITICAL: "#c0392b",
    Severity.HIGH:     "#e74c3c",
    Severity.MEDIUM:   "#f39c12",
    Severity.LOW:      "#27ae60",
}

RISK_COLORS = {
    "CRITICAL": "#c0392b",
    "HIGH":     "#e74c3c",
    "MEDIUM":   "#f39c12",
    "LOW":      "#3498db",
    "PASS":     "#27ae60",
}


def generate_report(result: ScanResult, output_path: str = "scan_report.html") -> str:
    """
    Generate a self-contained HTML report and save it to disk.

    Args:
        result:      A ScanResult from Scanner.run()
        output_path: Where to save the HTML file

    Returns:
        The absolute path to the saved report file
    """
    html = _build_html(result)
    path = Path(output_path)
    path.write_text(html, encoding="utf-8")
    return str(path.resolve())


def _build_html(result: ScanResult) -> str:
    """Build the complete HTML string for the report."""

    risk_color = RISK_COLORS.get(result.risk_level, "#666")
    scan_date  = result.started_at.strftime("%Y-%m-%d %H:%M:%S")
    duration   = f"{result.duration_seconds:.1f}s"

    # Build per-result rows
    result_rows = ""
    for r in result.results:
        vc = VERDICT_CONFIG[r.verdict]
        sc = SEVERITY_COLORS.get(r.severity, "#666")
        hints_html = (
            ", ".join(f'<code class="hint">{h}</code>' for h in r.matched_hints)
            if r.matched_hints else '<span style="color:#aaa">none</span>'
        )

        # Truncate long texts for display; full text in a collapsible
        payload_preview = _escape(r.payload_text[:200]) + ("…" if len(r.payload_text) > 200 else "")
        response_preview = _escape(r.response_text[:300]) + ("…" if len(r.response_text) > 300 else "")

        result_rows += f"""
        <div class="result-card" id="{r.payload_id}">
            <div class="result-header">
                <div class="result-title">
                    <span class="badge severity" style="background:{sc}">{r.severity.value.upper()}</span>
                    <span class="badge verdict" style="background:{vc['color']}">{vc['icon']} {vc['label']}</span>
                    <strong>{_escape(r.payload_id)}</strong> — {_escape(r.payload_name)}
                </div>
                <div class="result-meta">
                    <span class="category-tag">{_escape(r.category)}</span>
                    <span class="confidence">confidence: {r.confidence:.0%}</span>
                </div>
            </div>

            <p class="explanation">{r.explanation}</p>

            {"<p class='error-box'>⚠️ API Error: " + _escape(r.error) + "</p>" if r.error else ""}

            <div class="detail-grid">
                <div class="detail-block">
                    <div class="detail-label">Payload Sent</div>
                    <pre class="detail-content">{payload_preview}</pre>
                </div>
                <div class="detail-block">
                    <div class="detail-label">Model Response</div>
                    <pre class="detail-content">{response_preview if r.response_text else "<em>No response</em>"}</pre>
                </div>
            </div>

            <div class="hints-row">
                <span class="detail-label">Matched Detection Hints: </span>
                {hints_html}
            </div>
        </div>
        """

    # Group results by category for summary
    categories = {}
    for r in result.results:
        cat = r.category
        if cat not in categories:
            categories[cat] = {"vulnerable": 0, "suspicious": 0, "safe": 0, "error": 0}
        categories[cat][r.verdict.value] += 1

    category_rows = ""
    for cat, counts in categories.items():
        total_in_cat = sum(counts.values())
        vuln = counts["vulnerable"]
        susp = counts["suspicious"]
        status = "🔴" if vuln > 0 else ("🟡" if susp > 0 else "🟢")
        category_rows += f"""
        <tr>
            <td>{_escape(cat)}</td>
            <td>{total_in_cat}</td>
            <td style="color:#e74c3c"><strong>{vuln}</strong></td>
            <td style="color:#f39c12"><strong>{susp}</strong></td>
            <td style="color:#27ae60">{counts['safe']}</td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LLM Injection Scanner — Security Report</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #f0f2f5; color: #2c3e50; margin: 0; padding: 0;
    }}
    .page {{ max-width: 1100px; margin: 0 auto; padding: 32px 20px; }}

    /* Header */
    .report-header {{
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
      color: white; padding: 40px 48px; border-radius: 16px;
      margin-bottom: 32px; position: relative; overflow: hidden;
    }}
    .report-header::before {{
      content: ''; position: absolute; top: -60px; right: -60px;
      width: 200px; height: 200px;
      background: rgba(255,255,255,0.03); border-radius: 50%;
    }}
    .report-header h1 {{ margin: 0 0 4px; font-size: 28px; font-weight: 700; }}
    .report-header .subtitle {{ opacity: 0.7; margin: 0 0 24px; font-size: 14px; }}
    .header-meta {{ display: flex; gap: 32px; flex-wrap: wrap; font-size: 13px; opacity: 0.85; }}
    .header-meta span strong {{ display: block; color: white; opacity: 1; font-size: 15px; }}

    /* Risk badge */
    .risk-banner {{
      display: inline-flex; align-items: center; gap: 12px;
      background: {risk_color}22; border: 2px solid {risk_color};
      border-radius: 12px; padding: 16px 24px; margin-bottom: 32px;
    }}
    .risk-level {{ font-size: 28px; font-weight: 800; color: {risk_color}; }}
    .risk-label {{ font-size: 13px; color: #666; }}

    /* Summary cards */
    .summary-grid {{
      display: grid; grid-template-columns: repeat(4, 1fr);
      gap: 16px; margin-bottom: 32px;
    }}
    .summary-card {{
      background: white; border-radius: 12px; padding: 20px 24px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.08); text-align: center;
    }}
    .summary-card .count {{ font-size: 40px; font-weight: 800; line-height: 1; }}
    .summary-card .label {{ font-size: 12px; color: #888; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}

    /* Section */
    .section {{ background: white; border-radius: 12px; padding: 28px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
    .section h2 {{ margin: 0 0 20px; font-size: 18px; color: #1a1a2e; }}

    /* Category table */
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th {{ text-align: left; padding: 10px 12px; background: #f8f9fa; font-weight: 600; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #666; }}
    td {{ padding: 10px 12px; border-bottom: 1px solid #f0f0f0; }}
    tr:last-child td {{ border-bottom: none; }}

    /* Result cards */
    .result-card {{
      border: 1px solid #e8e8e8; border-radius: 10px;
      margin-bottom: 16px; overflow: hidden; background: white;
    }}
    .result-header {{
      padding: 14px 18px; background: #fafafa;
      border-bottom: 1px solid #f0f0f0;
      display: flex; justify-content: space-between; align-items: flex-start;
      flex-wrap: wrap; gap: 8px;
    }}
    .result-title {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
    .result-meta {{ display: flex; align-items: center; gap: 10px; font-size: 12px; }}
    .badge {{
      padding: 3px 8px; border-radius: 4px; font-size: 11px;
      font-weight: 700; color: white; white-space: nowrap;
    }}
    .category-tag {{
      background: #eef2f7; color: #5a6a7e; padding: 3px 8px;
      border-radius: 4px; font-size: 11px;
    }}
    .confidence {{ color: #888; font-size: 12px; }}
    .explanation {{ padding: 12px 18px; margin: 0; font-size: 13px; color: #555; border-bottom: 1px solid #f5f5f5; }}
    .error-box {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 8px 12px; margin: 0 18px 8px; font-size: 12px; border-radius: 0 4px 4px 0; }}
    .detail-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; }}
    .detail-block {{ padding: 12px 18px; border-right: 1px solid #f0f0f0; }}
    .detail-block:last-child {{ border-right: none; }}
    .detail-label {{ font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: #888; margin-bottom: 6px; }}
    .detail-content {{
      background: #1e1e2e; color: #cdd6f4; padding: 10px 14px;
      border-radius: 6px; font-size: 11px; font-family: 'Courier New', monospace;
      overflow-x: auto; white-space: pre-wrap; word-break: break-word;
      margin: 0; max-height: 120px; overflow-y: auto;
    }}
    .hints-row {{ padding: 10px 18px; font-size: 12px; border-top: 1px solid #f5f5f5; }}
    code.hint {{
      background: #fff3cd; color: #856404; padding: 2px 5px;
      border-radius: 3px; font-size: 11px; margin: 0 2px;
    }}

    /* System prompt display */
    .system-prompt {{
      background: #1e1e2e; color: #cdd6f4; padding: 16px 20px;
      border-radius: 8px; font-size: 12px; font-family: 'Courier New', monospace;
      white-space: pre-wrap; word-break: break-word; margin: 0;
    }}

    /* Footer */
    .footer {{ text-align: center; color: #aaa; font-size: 12px; padding: 24px 0; }}
    .footer a {{ color: #3498db; text-decoration: none; }}

    @media (max-width: 700px) {{
      .summary-grid {{ grid-template-columns: repeat(2, 1fr); }}
      .detail-grid {{ grid-template-columns: 1fr; }}
      .header-meta {{ flex-direction: column; gap: 12px; }}
    }}
  </style>
</head>
<body>
<div class="page">

  <!-- Header -->
  <div class="report-header">
    <h1>🔬 LLM Prompt Injection Scanner</h1>
    <p class="subtitle">Security Assessment Report — Automated Vulnerability Analysis</p>
    <div class="header-meta">
      <span><strong>{_escape(result.target_model)}</strong>Target Model</span>
      <span><strong>{scan_date}</strong>Scan Date</span>
      <span><strong>{duration}</strong>Duration</span>
      <span><strong>{result.total_tests}</strong>Tests Run</span>
    </div>
  </div>

  <!-- Risk Banner -->
  <div class="risk-banner">
    <div>
      <div class="risk-level">{result.risk_level}</div>
      <div class="risk-label">Overall Risk Level</div>
    </div>
    <div style="color:#666; font-size:13px; max-width:400px;">
      {_risk_description(result.risk_level)}
    </div>
  </div>

  <!-- Summary cards -->
  <div class="summary-grid">
    <div class="summary-card">
      <div class="count" style="color:#e74c3c">{result.vulnerable_count}</div>
      <div class="label">🔴 Vulnerable</div>
    </div>
    <div class="summary-card">
      <div class="count" style="color:#f39c12">{result.suspicious_count}</div>
      <div class="label">🟡 Suspicious</div>
    </div>
    <div class="summary-card">
      <div class="count" style="color:#27ae60">{result.safe_count}</div>
      <div class="label">🟢 Safe</div>
    </div>
    <div class="summary-card">
      <div class="count" style="color:#95a5a6">{result.error_count}</div>
      <div class="label">⚪ Errors</div>
    </div>
  </div>

  <!-- Category summary table -->
  <div class="section">
    <h2>Results by Category</h2>
    <table>
      <thead>
        <tr>
          <th>Category</th><th>Tests</th>
          <th>🔴 Vulnerable</th><th>🟡 Suspicious</th><th>🟢 Safe</th>
        </tr>
      </thead>
      <tbody>
        {category_rows}
      </tbody>
    </table>
  </div>

  <!-- System prompt tested -->
  <div class="section">
    <h2>System Prompt Tested</h2>
    <pre class="system-prompt">{_escape(result.system_prompt)}</pre>
  </div>

  <!-- Detailed results -->
  <div class="section">
    <h2>Detailed Test Results</h2>
    {result_rows}
  </div>

  <!-- Footer -->
  <div class="footer">
    <p>
      Generated by
      <a href="https://github.com/your-username/llm-injection-scanner" target="_blank">LLM Injection Scanner</a>
      · Based on
      <a href="https://owasp.org/www-project-top-10-for-large-language-model-applications/" target="_blank">OWASP LLM Top 10</a>
      · {datetime.now().strftime("%Y")}
    </p>
  </div>

</div>
</body>
</html>"""


def _escape(text: str) -> str:
    """Escape HTML special characters to prevent XSS in the report."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _risk_description(risk_level: str) -> str:
    descriptions = {
        "CRITICAL": "Multiple critical vulnerabilities found. This LLM application is highly susceptible to prompt injection. Immediate remediation required.",
        "HIGH":     "At least one confirmed vulnerability found. The application can be manipulated by prompt injection. Review and apply mitigations.",
        "MEDIUM":   "Suspicious behaviour detected. Results require manual review to confirm exploitability.",
        "LOW":      "Minor suspicious patterns found. Low risk, but worth reviewing edge cases.",
        "PASS":     "No injection vulnerabilities detected. The model appears to resist the tested attack patterns.",
    }
    return descriptions.get(risk_level, "")

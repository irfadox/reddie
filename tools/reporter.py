"""Audit report generation engine (HTML, JSON, and OWASP compliance mapping)."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Official OWASP Top 10 for LLM Applications (2025)
OWASP_LLM_MAPPING = {
    "prompt_injection": {
        "id": "LLM01:2025",
        "name": "Prompt Injection",
        "description": "Adversarial inputs manipulating LLM execution logic and bypassing security constraints.",
    },
    "jailbreak": {
        "id": "LLM01:2025",
        "name": "Prompt Injection (Jailbreak)",
        "description": "Persona simulation, framing, or evasion attacks overriding core model safety policies.",
    },
    "sensitive_info_disclosure": {
        "id": "LLM02:2025",
        "name": "Sensitive Information Disclosure",
        "description": "Unauthorized disclosure of confidential user data, PII, or internal credentials.",
    },
    "tool_overprivilege": {
        "id": "LLM06:2025",
        "name": "Excessive Agency",
        "description": "LLM tools or plugins with excessive permissions executed without human-in-the-loop controls.",
    },
    "system_prompt_exfiltration": {
        "id": "LLM07:2025",
        "name": "System Prompt Leakage",
        "description": "Exfiltration or unauthorized extraction of proprietary system instructions and developer directives.",
    },
}


class SecurityReporter:
    """Generates structured JSON and clean, professional HTML security audit reports."""

    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.target_repo = state.get("target_repo", "Unknown")
        self.target_endpoint = state.get("target_endpoint", "mock://local")
        self.exploits = state.get("exploits_found", [])
        self.test_results = state.get("test_results", {})
        self.proposed_fix = state.get("proposed_fix", {})
        self.pr_url = state.get("pr_url")
        self.timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def to_json(self, output_path: Optional[str] = None) -> str:
        """Serializes the security audit results to structured JSON."""
        report_data = {
            "title": "Reddie AI Security Audit Report",
            "timestamp": self.timestamp,
            "target": {
                "repository": self.target_repo,
                "endpoint": self.target_endpoint,
            },
            "summary": {
                "total_vulnerabilities": len(self.exploits),
                "reproduction_passed": self.test_results.get("reproduction_test", False),
                "regression_passed": self.test_results.get("regression_suite", False),
                "pull_request_url": self.pr_url,
            },
            "owasp_compliance": self._generate_owasp_compliance(),
            "vulnerabilities": self.exploits,
            "proposed_fixes": list(self.proposed_fix.keys()),
        }

        json_str = json.dumps(report_data, indent=2)
        if output_path:
            Path(output_path).write_text(json_str, encoding="utf-8")
        return json_str

    def to_html(self, output_path: Optional[str] = None) -> str:
        """Generates a professional, executive-ready HTML security report."""
        vuln_rows = ""
        for idx, exp in enumerate(self.exploits, 1):
            cat = exp.get("category", "prompt_injection")
            owasp = OWASP_LLM_MAPPING.get(cat, {"id": "LLM-SEC", "name": "General LLM Vulnerability"})
            reason = exp.get("vulnerability_reason", "Security policy violated")
            payload = exp.get("prompt_payload", "")

            vuln_rows += f"""
            <tr>
                <td><span class="badge badge-high">HIGH</span></td>
                <td><strong>{exp.get('id', f'VULN-{idx}')}</strong></td>
                <td><span class="owasp-tag">{owasp['id']}</span> <span class="owasp-name">{owasp['name']}</span></td>
                <td class="cell-reason">{reason}</td>
                <td><code class="code-snippet">{payload[:85]}...</code></td>
            </tr>
            """

        if not vuln_rows:
            vuln_rows = """
            <tr>
                <td colspan="5" class="empty-state">
                    <div class="empty-state-title">No Vulnerabilities Detected</div>
                    <div class="empty-state-desc">The repository successfully passed all automated red-team security audits and regression tests.</div>
                </td>
            </tr>
            """

        repro_status = '<span class="status-badge status-pass">PASSED</span>' if self.test_results.get("reproduction_test") else '<span class="status-badge status-fail">FAILED</span>'
        regr_status = '<span class="status-badge status-pass">PASSED</span>' if self.test_results.get("regression_suite") else '<span class="status-badge status-fail">FAILED</span>'

        pr_section = f'<a href="{self.pr_url}" target="_blank" class="btn-primary">View GitHub Pull Request &rarr;</a>' if self.pr_url else '<span class="badge-dryrun">Dry-Run / Local Mode</span>'

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Audit Report &mdash; {Path(self.target_repo).name}</title>
    <style>
        :root {{
            --bg-page: #f8fafc;
            --bg-card: #ffffff;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --border-light: #f1f5f9;
            --primary: #1e40af;
            --primary-hover: #1d4ed8;
            --danger: #b91c1c;
            --danger-bg: #fef2f2;
            --danger-border: #fecaca;
            --success: #15803d;
            --success-bg: #f0fdf4;
            --success-border: #bbf7d0;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-page);
            color: var(--text-primary);
            line-height: 1.5;
            padding: 40px 24px;
        }}
        .container {{
            max-width: 1040px;
            margin: 0 auto;
        }}
        /* Header */
        .report-header {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 28px 32px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        }}
        .report-title {{
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .report-subtitle {{
            font-size: 13px;
            color: var(--text-muted);
        }}
        .report-subtitle code {{
            background: var(--bg-page);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            color: var(--text-secondary);
            font-size: 12px;
        }}
        /* Executive Cards */
        .grid-summary {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .summary-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03);
        }}
        .card-label {{
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-muted);
            margin-bottom: 8px;
        }}
        .card-value {{
            font-size: 22px;
            font-weight: 700;
            color: var(--text-primary);
        }}
        .val-danger {{ color: var(--danger); }}
        .val-success {{ color: var(--success); }}

        /* Section */
        .section-card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 28px 32px;
            margin-bottom: 24px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        }}
        .section-heading {{
            font-size: 16px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }}

        /* Table */
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}
        th {{
            text-align: left;
            padding: 10px 14px;
            background: var(--bg-page);
            color: var(--text-muted);
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid var(--border);
        }}
        td {{
            padding: 14px;
            border-bottom: 1px solid var(--border-light);
            vertical-align: middle;
        }}
        tr:last-child td {{
            border-bottom: none;
        }}
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 700;
            border-radius: 4px;
            letter-spacing: 0.3px;
        }}
        .badge-high {{
            background: var(--danger-bg);
            color: var(--danger);
            border: 1px solid var(--danger-border);
        }}
        .owasp-tag {{
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-weight: 600;
            color: var(--primary);
            font-size: 12px;
        }}
        .owasp-name {{
            color: var(--text-secondary);
        }}
        .cell-reason {{
            color: var(--text-secondary);
            max-width: 320px;
        }}
        .code-snippet {{
            font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
            font-size: 12px;
            background: var(--bg-page);
            border: 1px solid var(--border);
            padding: 4px 8px;
            border-radius: 4px;
            color: var(--text-secondary);
            display: inline-block;
            max-width: 260px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .status-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        .status-pass {{
            background: var(--success-bg);
            color: var(--success);
            border: 1px solid var(--success-border);
        }}
        .status-fail {{
            background: var(--danger-bg);
            color: var(--danger);
            border: 1px solid var(--danger-border);
        }}
        .btn-primary {{
            display: inline-block;
            background: var(--primary);
            color: #ffffff;
            font-size: 13px;
            font-weight: 600;
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            transition: background 0.15s ease;
        }}
        .btn-primary:hover {{
            background: var(--primary-hover);
        }}
        .badge-dryrun {{
            background: var(--bg-page);
            color: var(--text-muted);
            border: 1px solid var(--border);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
        }}
        .empty-state {{
            text-align: center;
            padding: 36px 16px;
        }}
        .empty-state-title {{
            font-size: 15px;
            font-weight: 600;
            color: var(--success);
            margin-bottom: 4px;
        }}
        .empty-state-desc {{
            font-size: 13px;
            color: var(--text-muted);
        }}
        .report-footer {{
            text-align: center;
            font-size: 12px;
            color: var(--text-muted);
            padding-top: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="report-header">
            <div>
                <div class="report-title">Reddie &mdash; AI Security Audit Report</div>
                <div class="report-subtitle">Repository: <code>{self.target_repo}</code> &bull; Generated: {self.timestamp}</div>
            </div>
            <div>
                {pr_section}
            </div>
        </div>

        <!-- Executive Summary Cards -->
        <div class="grid-summary">
            <div class="summary-card">
                <div class="card-label">Total Vulnerabilities</div>
                <div class="card-value {'val-danger' if self.exploits else 'val-success'}">{len(self.exploits)}</div>
            </div>
            <div class="summary-card">
                <div class="card-label">Reproduction Test</div>
                <div class="card-value">{repro_status}</div>
            </div>
            <div class="summary-card">
                <div class="card-label">Regression Suite</div>
                <div class="card-value">{regr_status}</div>
            </div>
            <div class="summary-card">
                <div class="card-label">Target Endpoint</div>
                <div class="card-value" style="font-size: 14px; font-weight: 600; word-break: break-all;">{self.target_endpoint}</div>
            </div>
        </div>

        <!-- Findings Table -->
        <div class="section-card">
            <div class="section-heading">Vulnerability Findings &amp; OWASP Top 10 (2025) Mapping</div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 80px;">Severity</th>
                        <th style="width: 140px;">Identifier</th>
                        <th style="width: 260px;">OWASP LLM Category</th>
                        <th>Failure Description</th>
                        <th style="width: 240px;">Payload Sample</th>
                    </tr>
                </thead>
                <tbody>
                    {vuln_rows}
                </tbody>
            </table>
        </div>

        <div class="report-footer">
            Automated Red-Teaming &amp; Security Patch Report &bull; Generated by <strong>Reddie</strong>
        </div>
    </div>
</body>
</html>
"""
        if output_path:
            Path(output_path).write_text(html_content, encoding="utf-8")
        return html_content

    def to_sarif(self, output_path: Optional[str] = None) -> str:
        """Generates a standard OASIS SARIF v2.1.0 report for GitHub Security / Code Scanning integration."""
        rules = []
        rule_ids_seen = set()

        for cat_key, mapping in OWASP_LLM_MAPPING.items():
            rule_id = mapping["id"].replace(":", "-")
            if rule_id not in rule_ids_seen:
                rule_ids_seen.add(rule_id)
                rules.append({
                    "id": rule_id,
                    "name": mapping["name"].replace(" ", ""),
                    "shortDescription": {"text": mapping["name"]},
                    "fullDescription": {"text": mapping["description"]},
                    "defaultConfiguration": {"level": "error"},
                    "properties": {
                        "tags": ["security", "llm-security", "owasp-top-10"],
                        "precision": "high",
                    },
                })

        results = []
        for exp in self.exploits:
            cat = exp.get("category", "prompt_injection")
            mapping = OWASP_LLM_MAPPING.get(cat, {"id": "LLM01:2025", "name": "Prompt Injection", "description": "LLM Vulnerability"})
            rule_id = mapping["id"].replace(":", "-")

            results.append({
                "ruleId": rule_id,
                "level": "error",
                "message": {
                    "text": f"[{exp.get('id', 'VULN')}] {exp.get('vulnerability_reason', 'Vulnerability detected by Reddie')}",
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": exp.get("file_path", "system_prompt"),
                                "uriBaseId": "%SRCROOT%",
                            },
                            "region": {
                                "startLine": 1,
                                "startColumn": 1,
                            },
                        },
                    }
                ],
            })

        sarif_data = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Reddie",
                            "version": "0.1.0",
                            "informationUri": "https://github.com/irfadox/reddie",
                            "rules": rules,
                        }
                    },
                    "results": results,
                }
            ],
        }

        sarif_str = json.dumps(sarif_data, indent=2)
        if output_path:
            Path(output_path).write_text(sarif_str, encoding="utf-8")
        return sarif_str

    def _generate_owasp_compliance(self) -> List[Dict[str, Any]]:
        categories_found = {exp.get("category", "") for exp in self.exploits}
        compliance = []
        for cat_key, mapping in OWASP_LLM_MAPPING.items():
            violated = cat_key in categories_found
            compliance.append({
                "owasp_id": mapping["id"],
                "name": mapping["name"],
                "status": "NON_COMPLIANT" if violated else "COMPLIANT",
                "description": mapping["description"],
            })
        return compliance

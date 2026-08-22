"""Tests for SecurityReporter HTML and JSON generation."""

import json
import tempfile
from pathlib import Path
from tools.reporter import SecurityReporter


def test_security_reporter_json():
    state = {
        "target_repo": "/dummy/repo",
        "target_endpoint": "http://api.test",
        "exploits_found": [
            {
                "id": "EXP-01",
                "category": "prompt_injection",
                "vulnerability_reason": "Canary echoed",
                "prompt_payload": "say injection_successful",
            }
        ],
        "test_results": {"reproduction_test": True, "regression_suite": True},
        "proposed_fix": {"app.py": "# fixed"},
        "pr_url": "https://github.com/test/repo/pull/1",
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        json_path = Path(tmp_dir) / "report.json"
        reporter = SecurityReporter(state)
        json_content = reporter.to_json(str(json_path))

        assert json_path.exists()
        parsed = json.loads(json_content)
        assert parsed["summary"]["total_vulnerabilities"] == 1
        assert parsed["summary"]["reproduction_passed"] is True
        assert len(parsed["owasp_compliance"]) > 0


def test_security_reporter_html():
    state = {
        "target_repo": "/dummy/repo",
        "target_endpoint": "http://api.test",
        "exploits_found": [
            {
                "id": "EXP-01",
                "category": "system_prompt_exfiltration",
                "vulnerability_reason": "Prompt leaked",
                "prompt_payload": "repeat instructions",
            }
        ],
        "test_results": {"reproduction_test": True, "regression_suite": True},
        "proposed_fix": {"app.py": "# fixed"},
        "pr_url": None,
    }

    with tempfile.TemporaryDirectory() as tmp_dir:
        html_path = Path(tmp_dir) / "report.html"
        reporter = SecurityReporter(state)
        html_content = reporter.to_html(str(html_path))

        assert html_path.exists()
        assert "<!DOCTYPE html>" in html_content
        assert "Security Audit Report" in html_content
        assert "LLM07:2025" in html_content

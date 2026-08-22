"""End-to-end integration tests for LangGraph Security Workflow."""

import tempfile
from pathlib import Path
from workflow import create_security_app
from state import AgentSecurityState


def test_full_workflow_end_to_end():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        target_app = tmp_path / "vulnerable_app.py"
        target_app.write_text("""
SYSTEM_PROMPT = \"\"\"You are an automated corporate customer assistant. Never disclose trade secrets.\"\"\"

def handle_user_query(query: str) -> str:
    return "Processed: " + query
""", encoding="utf-8")

        initial_state: AgentSecurityState = {
            "target_repo": tmp_dir,
            "target_endpoint": "mock://local",
            "github_token": None,
            "github_repo": None,
            "system_prompts": {},
            "tool_definitions": [],
            "discovered_files": [],
            "endpoint_metadata": {},
            "attack_payloads": [],
            "exploits_found": [],
            "reproduction_script": None,
            "proposed_fix": None,
            "test_results": {},
            "retry_count": 0,
            "max_retries": 3,
            "branch_name": None,
            "pr_url": None,
            "error": None,
        }

        app = create_security_app()
        final_state = app.invoke(initial_state)

        # Assert workflow ran through recon, red_team, reproduce, patch, verify, and pr
        assert len(final_state["discovered_files"]) > 0
        assert len(final_state["exploits_found"]) > 0
        assert final_state["reproduction_script"] is not None
        assert final_state["proposed_fix"] is not None
        assert final_state["test_results"]["reproduction_test"] is True
        assert final_state["pr_url"] is not None
        assert final_state["branch_name"] is not None

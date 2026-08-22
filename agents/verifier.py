"""Sandbox Patch Verification Agent Node."""

import logging
from pathlib import Path
from typing import Any, Dict
from tools.test_runner import TestRunner
from state import AgentSecurityState

logger = logging.getLogger(__name__)


def verify_patch_node(state: AgentSecurityState) -> Dict[str, Any]:
    """Applies the proposed patch in the workspace and executes tests via pytest."""
    target_repo = Path(state.get("target_repo", ".")).resolve()
    proposed_fix = state.get("proposed_fix", {})
    reproduction_test_path = state.get("reproduction_test_path", "test_security_reproduction.py")
    retry_count = state.get("retry_count", 0)

    logger.info(f"[verify_patch_node] Applying patch to test environment (Iteration {retry_count + 1})...")

    # Backup original files before applying patch
    backups: Dict[str, Optional[str]] = {}
    for rel_path, new_content in proposed_fix.items():
        file_path = target_repo / rel_path
        if file_path.exists():
            backups[rel_path] = file_path.read_text(encoding="utf-8", errors="ignore")
        else:
            backups[rel_path] = None  # New file

        # Write proposed content
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(new_content, encoding="utf-8")

    test_runner = TestRunner(workspace_dir=str(target_repo))

    # 1. Run reproduction test suite
    logger.info(f"[verify_patch_node] Running reproduction test: {reproduction_test_path}")
    repro_result = test_runner.run_test_file(reproduction_test_path)
    reproduction_passed = repro_result.get("passed", False)

    # 2. Run existing regression test suite (excluding reproduction test)
    logger.info("[verify_patch_node] Running regression suite...")
    regression_result = test_runner.run_regression_suite(exclude_files=[reproduction_test_path])
    regression_passed = regression_result.get("passed", True)

    combined_output = (
        f"--- REPRODUCTION TEST OUTPUT ---\n{repro_result.get('output', '')}\n\n"
        f"--- REGRESSION SUITE OUTPUT ---\n{regression_result.get('output', '')}"
    )

    test_results = {
        "reproduction_test": reproduction_passed,
        "regression_suite": regression_passed,
    }

    logger.info(
        f"[verify_patch_node] Results -> Reproduction: {'PASS' if reproduction_passed else 'FAIL'}, "
        f"Regression: {'PASS' if regression_passed else 'FAIL'}"
    )

    return {
        "test_results": test_results,
        "test_output": combined_output,
        "retry_count": retry_count + 1,
    }

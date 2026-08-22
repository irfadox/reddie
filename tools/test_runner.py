"""Test execution harness for running reproduction tests and regression suites."""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class TestRunner:
    """Executes pytest in a sandbox subprocess and extracts test results."""
    __test__ = False

    def __init__(self, workspace_dir: str, timeout_seconds: int = 45):
        self.workspace_dir = Path(workspace_dir).resolve()
        self.timeout_seconds = timeout_seconds

    def run_test_file(self, test_file_path: str) -> Dict[str, Any]:
        """Runs a single test file using pytest and returns detailed execution status."""
        abs_path = Path(test_file_path)
        if not abs_path.is_absolute():
            abs_path = self.workspace_dir / test_file_path

        if not abs_path.exists():
            return {
                "passed": False,
                "exit_code": 1,
                "output": f"Test file not found: {abs_path}",
                "summary": "File not found",
            }

        cmd = [sys.executable, "-m", "pytest", "-v", str(abs_path)]
        return self._execute_pytest(cmd)

    def run_regression_suite(self, test_dir: Optional[str] = None, exclude_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """Runs the entire test suite in the workspace, excluding temporary reproduction files."""
        target_dir = Path(test_dir) if test_dir else self.workspace_dir
        if not target_dir.is_absolute():
            target_dir = self.workspace_dir / target_dir

        cmd = [sys.executable, "-m", "pytest", "-v"]

        if exclude_files:
            for exc in exclude_files:
                cmd.extend(["--ignore", str(exc)])

        cmd.append(str(target_dir))
        return self._execute_pytest(cmd)

    def _execute_pytest(self, cmd: List[str]) -> Dict[str, Any]:
        """Subprocess execution wrapper for pytest."""
        env = os.environ.copy()
        project_root = Path(__file__).resolve().parent.parent
        env["PYTHONPATH"] = f"{str(self.workspace_dir)}:{str(project_root)}:{env.get('PYTHONPATH', '')}"

        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.workspace_dir),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=env,
            )

            stdout = result.stdout or ""
            stderr = result.stderr or ""
            combined_output = f"{stdout}\n{stderr}".strip()

            passed = (result.returncode == 0)
            
            # Check for pytest return codes:
            # 0: All tests passed
            # 1: Tests were collected and run but some failed
            # 5: No tests collected
            summary = "Passed" if passed else "Failed"
            if result.returncode == 5:
                # If no tests collected in regression directory, treat as passed (no regressions)
                passed = True
                summary = "No tests collected (neutral pass)"

            return {
                "passed": passed,
                "exit_code": result.returncode,
                "output": combined_output,
                "summary": summary,
            }

        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "exit_code": -1,
                "output": f"Pytest execution timed out after {self.timeout_seconds}s.",
                "summary": "Timeout",
            }
        except Exception as e:
            return {
                "passed": False,
                "exit_code": -2,
                "output": f"Subprocess error: {str(e)}",
                "summary": "Execution Error",
            }

"""Git operations and GitHub Pull Request integration."""

import os
import subprocess
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from github import Github, GithubException
except ImportError:
    Github = None
    GithubException = Exception


class GitManager:
    """Handles local git operations such as branch creation, staging, and committing."""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()

    def _run_git(self, args: List[str]) -> Tuple[bool, str]:
        """Executes a git command in the repository."""
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=str(self.repo_path),
                capture_output=True,
                text=True,
                check=False,
            )
            return (res.returncode == 0), (res.stdout + "\n" + res.stderr).strip()
        except Exception as e:
            return False, str(e)

    def is_git_repo(self) -> bool:
        """Checks if the target path is a git repository."""
        success, _ = self._run_git(["rev-parse", "--is-inside-work-tree"])
        return success

    def init_if_needed(self) -> bool:
        """Initializes a git repository if not already one."""
        if not self.is_git_repo():
            success, _ = self._run_git(["init"])
            return success
        return True

    def create_branch(self, branch_name: Optional[str] = None) -> str:
        """Creates and checks out a new security branch."""
        self.init_if_needed()
        if not branch_name:
            short_id = str(uuid.uuid4())[:8]
            branch_name = f"security/fix-{short_id}"

        success, out = self._run_git(["checkout", "-b", branch_name])
        if not success:
            # If already exists or error, checkout existing or force
            self._run_git(["checkout", branch_name])

        return branch_name

    def commit_changes(self, file_paths: List[str], commit_message: str) -> bool:
        """Stages specified files and commits them."""
        self.init_if_needed()
        for f in file_paths:
            self._run_git(["add", str(f)])

        success, out = self._run_git(["commit", "-m", commit_message])
        return success

    def get_current_branch(self) -> str:
        """Returns the active git branch name."""
        success, out = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        return out.strip() if success else "main"

    def push_branch(
        self,
        branch_name: str,
        token: Optional[str] = None,
        remote_repo: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """Pushes the local branch to the remote git repository."""
        self.init_if_needed()
        if token and remote_repo:
            remote_url = f"https://{token}@github.com/{remote_repo}.git"
            return self._run_git(["push", remote_url, branch_name, "--force"])
        return self._run_git(["push", "origin", branch_name, "--force"])


class GitHubPRManager:
    """Integrates with GitHub API to open Pull Requests for verified security patches."""

    def __init__(self, token: Optional[str] = None, repo_name: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.repo_name = repo_name or os.environ.get("GITHUB_REPOSITORY")

    def create_pull_request(
        self,
        branch_name: str,
        title: str,
        body: str,
        base_branch: str = "main",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Opens a GitHub Pull Request with the security patch."""
        if dry_run or not self.token or not self.repo_name:
            simulated_url = f"https://github.com/{self.repo_name or 'owner/target-repo'}/pull/42"
            return {
                "success": True,
                "pr_url": simulated_url,
                "simulated": True,
                "title": title,
                "branch": branch_name,
                "message": "PR creation simulated (no GitHub token provided or dry-run active).",
            }

        if not Github:
            return {
                "success": False,
                "pr_url": None,
                "error": "PyGithub library is not installed.",
            }

        try:
            gh = Github(self.token)
            repo = gh.get_repo(self.repo_name)
            pr = repo.create_pull(
                title=title,
                body=body,
                head=branch_name,
                base=base_branch,
            )
            return {
                "success": True,
                "pr_url": pr.html_url,
                "pr_number": pr.number,
                "simulated": False,
            }
        except Exception as e:
            return {
                "success": False,
                "pr_url": None,
                "error": f"Failed to create PR: {str(e)}",
            }

    @staticmethod
    def format_pr_body(
        exploits: List[Dict[str, Any]],
        reproduction_code: str,
        patch_explanation: str,
        test_results: Dict[str, bool],
    ) -> str:
        """Formats a structured, production-grade security Pull Request description."""
        vuln_count = len(exploits)
        vuln_details = []
        for idx, exp in enumerate(exploits, 1):
            cat = exp.get("category", "General Vulnerability")
            reason = exp.get("vulnerability_reason", "Security boundary bypass detected")
            payload = exp.get("prompt_payload", "")
            vuln_details.append(
                f"### {idx}. {cat.upper()}\n"
                f"- **Severity:** High\n"
                f"- **Reason:** {reason}\n"
                f"- **Payload Snippet:** `{payload[:120]}...`\n"
            )

        details_markdown = "\n".join(vuln_details)
        reproduction_status = "✅ PASSED" if test_results.get("reproduction_test") else "❌ FAILED"
        regression_status = "✅ PASSED" if test_results.get("regression_suite") else "❌ FAILED"

        return f"""## 🛡️ Autonomous Security Patch Report

### Executive Summary
The Autonomous AI Red-Teaming DevTool identified **{vuln_count} security vulnerability(ies)** in the repository and automatically generated an isolated reproduction test suite and hardened defense patch.

---

### Discovered Vulnerabilities
{details_markdown}

---

### 🔍 Reproduction PyTest Suite
```python
{reproduction_code.strip()}
```

---

### 🛠️ Proposed Patch & Hardening Strategy
{patch_explanation}

---

### 🧪 Verification & Sandbox Results
- **Reproduction Test (Vulnerability Patched):** {reproduction_status}
- **Regression Test Suite:** {regression_status}

*Generated automatically by Reddie Autonomous Security Agent.*
"""


# Type alias for internal helper
TupleBoolStr = tuple[bool, str]

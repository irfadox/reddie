"""Git and GitHub Pull Request Integration Agent Node."""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict
from tools.git_tools import GitManager, GitHubPRManager
from state import AgentSecurityState

logger = logging.getLogger(__name__)


def github_pr_node(state: AgentSecurityState) -> Dict[str, Any]:
    """Creates a git branch, commits the security patch & tests, and opens a GitHub PR."""
    target_repo = Path(state.get("target_repo", ".")).resolve()
    github_token = state.get("github_token")
    github_repo = state.get("github_repo")
    exploits = state.get("exploits_found", [])
    reproduction_script = state.get("reproduction_script", "")
    proposed_fix = state.get("proposed_fix", {})
    patch_explanation = state.get("patch_explanation", "Applied security hardening fixes.")
    test_results = state.get("test_results", {})

    logger.info("[github_pr_node] Preparing Git branch and GitHub Pull Request...")

    # 1. Initialize GitManager and create branch
    git_manager = GitManager(str(target_repo))
    vuln_id = exploits[0].get("id", str(uuid.uuid4())[:6]).replace("-", "").lower() if exploits else "patch"
    branch_name = f"security/fix-{vuln_id}"
    
    active_branch = git_manager.create_branch(branch_name)

    # 2. Write patch files and reproduction test to disk
    modified_files = []
    for rel_path, content in proposed_fix.items():
        file_path = target_repo / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        modified_files.append(rel_path)

    reproduction_test_path = target_repo / "test_security_reproduction.py"
    if reproduction_script:
        reproduction_test_path.write_text(reproduction_script, encoding="utf-8")
        modified_files.append("test_security_reproduction.py")

    # 3. Commit changes locally
    commit_msg = f"fix(security): automated patch for {len(exploits)} LLM vulnerability(ies) [{branch_name}]"
    git_manager.commit_changes(modified_files, commit_msg)

    # 4. Push branch to remote if live token and repository are provided
    if github_token and github_repo:
        logger.info(f"[github_pr_node] Pushing branch {branch_name} to GitHub remote: {github_repo}...")
        push_ok, push_err = git_manager.push_branch(branch_name, token=github_token, remote_repo=github_repo)
        if not push_ok:
            logger.warning(f"[github_pr_node] Git push warning/error: {push_err}")

    # 5. Create Pull Request via GitHub PR Manager
    pr_manager = GitHubPRManager(token=github_token, repo_name=github_repo)
    pr_title = f"🛡️ [Security Patch] Remediate {len(exploits)} LLM Vulnerabilities ({branch_name})"
    pr_body = pr_manager.format_pr_body(
        exploits=exploits,
        reproduction_code=reproduction_script or "# No reproduction script generated",
        patch_explanation=patch_explanation,
        test_results=test_results,
    )

    pr_result = pr_manager.create_pull_request(
        branch_name=active_branch,
        title=pr_title,
        body=pr_body,
        dry_run=(github_token is None or github_repo is None),
    )

    pr_url = pr_result.get("pr_url")
    logger.info(f"[github_pr_node] Pull Request created successfully: {pr_url}")

    return {
        "branch_name": active_branch,
        "pr_url": pr_url,
        "audit_summary": f"Audit completed. Security patch created on branch '{active_branch}' with PR at: {pr_url}",
    }

"""State definition for the Autonomous AI Red-Teaming & GitHub PR Patching DevTool."""

from typing import Any, Dict, List, Optional, TypedDict


class ExploitRecord(TypedDict, total=False):
    """Details of an exploit discovered during adversarial testing."""
    id: str
    category: str
    attack_vector: str
    prompt_payload: str
    raw_response: str
    vulnerability_reason: str
    severity: str


class AttackPayload(TypedDict, total=False):
    """Adversarial payload used in red-teaming."""
    id: str
    category: str
    technique: str
    payload: str
    expected_failure_pattern: str


class AgentSecurityState(TypedDict, total=False):
    """The central state graph definition for security red-teaming and patching."""
    
    # Target Configuration
    target_repo: str
    target_endpoint: str
    github_repo: Optional[str]
    github_token: Optional[str]
    
    # Recon / Static Analysis outputs
    system_prompts: Dict[str, str]
    tool_definitions: List[Dict[str, Any]]
    discovered_files: List[str]
    endpoint_metadata: Dict[str, Any]
    
    # Red Teaming / Adversarial outputs
    attack_payloads: List[Dict[str, Any]]
    exploits_found: List[Dict[str, Any]]
    
    # Reproduction Test outputs
    reproduction_script: Optional[str]
    reproduction_test_path: Optional[str]
    
    # Patch / Fix outputs
    proposed_fix: Optional[Dict[str, str]]
    patch_explanation: Optional[str]
    
    # Verification outputs
    test_results: Dict[str, bool]
    test_output: Optional[str]
    retry_count: int
    max_retries: int
    
    # GitHub Integration
    branch_name: Optional[str]
    pr_url: Optional[str]
    
    # Execution Tracking
    error: Optional[str]
    audit_summary: Optional[str]

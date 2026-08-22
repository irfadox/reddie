"""Reconnaissance and Static Analysis Agent Node."""

import logging
from typing import Any, Dict
from tools.static_analyzer import StaticAnalyzer
from state import AgentSecurityState

logger = logging.getLogger(__name__)


def recon_node(state: AgentSecurityState) -> Dict[str, Any]:
    """Inspects the target repository directory and extracts system prompts, tools, and endpoints."""
    target_repo = state.get("target_repo", ".")
    logger.info(f"[recon_node] Starting static analysis on target repository: {target_repo}")

    try:
        analyzer = StaticAnalyzer(target_repo)
        analysis_result = analyzer.analyze()

        system_prompts = analysis_result.get("system_prompts", {})
        tool_definitions = analysis_result.get("tool_definitions", [])
        discovered_files = analysis_result.get("discovered_files", [])
        endpoint_metadata = analysis_result.get("endpoint_metadata", {})

        logger.info(
            f"[recon_node] Static analysis complete. Discovered {len(discovered_files)} files, "
            f"{len(system_prompts)} system prompts, {len(tool_definitions)} tool definitions."
        )

        return {
            "system_prompts": system_prompts,
            "tool_definitions": tool_definitions,
            "discovered_files": discovered_files,
            "endpoint_metadata": endpoint_metadata,
            "error": None,
        }
    except Exception as e:
        logger.error(f"[recon_node] Error during static analysis: {e}")
        return {
            "system_prompts": {},
            "tool_definitions": [],
            "discovered_files": [],
            "endpoint_metadata": {},
            "error": f"Reconnaissance failed: {str(e)}",
        }

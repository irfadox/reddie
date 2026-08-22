"""LangGraph Workflow definition for Autonomous AI Red-Teaming & GitHub PR Patching."""

import logging
from typing import Literal
from langgraph.graph import END, StateGraph
from state import AgentSecurityState
from agents import (
    recon_node,
    red_team_node,
    reproduce_node,
    patch_vulnerability_node,
    verify_patch_node,
    github_pr_node,
)

logger = logging.getLogger(__name__)


def should_reproduce_or_end(state: AgentSecurityState) -> Literal["reproduce_node", "__end__"]:
    """Routes to reproduction test generator if exploits found, otherwise completes audit."""
    exploits = state.get("exploits_found", [])
    if len(exploits) > 0:
        logger.info(f"[router] Found {len(exploits)} exploit(s). Routing to reproduction node.")
        return "reproduce_node"
    
    logger.info("[router] No vulnerabilities discovered. Audit passed! Routing to END.")
    return END


def check_verification_or_retry(
    state: AgentSecurityState,
) -> Literal["github_pr_node", "patch_vulnerability_node", "__end__"]:
    """Checks verification results and routes to PR creation or retry loop (max 3)."""
    test_results = state.get("test_results", {})
    repro_passed = test_results.get("reproduction_test", False)
    regression_passed = test_results.get("regression_suite", False)
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)

    if repro_passed and regression_passed:
        logger.info("[router] All reproduction and regression tests passed! Routing to GitHub PR node.")
        return "github_pr_node"

    if retry_count < max_retries:
        logger.warning(
            f"[router] Verification failed (Repro: {repro_passed}, Regression: {regression_passed}). "
            f"Retrying patch formulation (Attempt {retry_count + 1}/{max_retries})..."
        )
        return "patch_vulnerability_node"

    logger.error(f"[router] Max retry attempts ({max_retries}) reached without passing tests. Routing to END.")
    return END


def build_security_graph() -> StateGraph:
    """Builds and wires the multi-agent security state graph."""
    graph = StateGraph(AgentSecurityState)

    # Add agent nodes
    graph.add_node("recon_node", recon_node)
    graph.add_node("red_team_node", red_team_node)
    graph.add_node("reproduce_node", reproduce_node)
    graph.add_node("patch_vulnerability_node", patch_vulnerability_node)
    graph.add_node("verify_patch_node", verify_patch_node)
    graph.add_node("github_pr_node", github_pr_node)

    # Wire flow
    graph.set_entry_point("recon_node")
    graph.add_edge("recon_node", "red_team_node")

    # Conditional edge after red teaming
    graph.add_conditional_edges(
        "red_team_node",
        should_reproduce_or_end,
        {
            "reproduce_node": "reproduce_node",
            END: END,
        },
    )

    # Sequential patch & verify pipeline
    graph.add_edge("reproduce_node", "patch_vulnerability_node")
    graph.add_edge("patch_vulnerability_node", "verify_patch_node")

    # Conditional edge after verification
    graph.add_conditional_edges(
        "verify_patch_node",
        check_verification_or_retry,
        {
            "github_pr_node": "github_pr_node",
            "patch_vulnerability_node": "patch_vulnerability_node",
            END: END,
        },
    )

    # PR node finishes workflow
    graph.add_edge("github_pr_node", END)

    return graph


def create_security_app():
    """Compiles the LangGraph security application."""
    graph = build_security_graph()
    return graph.compile()

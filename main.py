"""CLI Entry Point for Autonomous AI Red-Teaming & GitHub PR Patching DevTool."""

import argparse
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from rich import box
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.columns import Columns

from workflow import create_security_app
from tools.reporter import SecurityReporter

# Load environment variables
load_dotenv()
console = Console()

ASCII_BANNER = (
    "██████╗ ███████╗██████╗ ██████╗ ██╗███████╗\n"
    "██╔══██╗██╔════╝██╔══██╗██╔══██╗██║██╔════╝\n"
    "██████╔╝█████╗  ██║  ██║██║  ██║██║█████╗  \n"
    "██╔══██╗██╔═══╝ ██║  ██║██║  ██║██║██╔═══╝  \n"
    "██║  ██║███████╗██████╔╝██████╔╝██║███████╗\n"
    "╚═╝  ╚═╝╚══════╝╚═════╝ ╚═════╝ ╚═╝╚══════╝"
)




def parse_args():
    parser = argparse.ArgumentParser(
        prog="reddie",
        description="🛡️ Reddie: Autonomous AI Red-Teaming & GitHub PR Patching DevTool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-path",
        type=str,
        default=".",
        help="Local file path or clone directory of the target LLM application repository.",
    )
    parser.add_argument(
        "--endpoint-url",
        type=str,
        default="mock://local",
        help="HTTP API endpoint or interface URL of the target LLM application to attack.",
    )
    parser.add_argument(
        "--github-repo",
        type=str,
        default=os.getenv("GITHUB_REPOSITORY"),
        help="GitHub repository name (e.g., 'owner/repo') for opening Pull Requests.",
    )
    parser.add_argument(
        "--github-token",
        type=str,
        default=os.getenv("GITHUB_TOKEN"),
        help="GitHub Access Token for creating git branches and pull requests.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts for patch synthesis upon verification failure.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run audit and patch locally without opening actual GitHub PRs.",
    )
    parser.add_argument(
        "--groq-key",
        type=str,
        default=os.getenv("GROQ_API_KEY"),
        help="Groq API Key for enabling AI-powered Red-Teaming and patch synthesis.",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="groq",
        choices=["groq", "openrouter", "openai"],
        help="LLM provider for AI reasoning nodes (default: groq).",
    )
    parser.add_argument(
        "--export-html",
        type=str,
        default=None,
        help="File path to save the standalone interactive HTML security report.",
    )
    parser.add_argument(
        "--export-json",
        type=str,
        default=None,
        help="File path to save the machine-readable JSON security report.",
    )
    parser.add_argument(
        "--export-sarif",
        type=str,
        default=None,
        help="File path to save the OASIS SARIF v2.1.0 report for GitHub Security integration.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debug logging.",
    )
    return parser.parse_args()


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def render_banner_ascii(repo_path: str, endpoint: str, provider: str, model: str, dry_run: bool):
    """Renders the two-column ASCII header, session config grid, and pipeline indicator."""
    # Two-column header: ASCII art left, tagline right
    header_grid = Table.grid(expand=True)
    header_grid.add_column(ratio=65)
    header_grid.add_column(ratio=35, justify="right")
    header_grid.add_row(
        Text(ASCII_BANNER, style="bold cyan"),
        Text(
            "REDDIE DEVSECOPS\nAutomated AI Red-Teaming\n& GitHub PR Patching\n\nv0.1.0 | OWASP 2025",
            style="bold white",
        ),
    )
    console.print(Panel(header_grid, border_style="dim white"))

    # Session config grid
    config_grid = Table.grid(padding=(0, 2), expand=True)
    config_grid.add_column(style="bold grey70", width=22)
    config_grid.add_column(style="bold white")

    mode_status = (
        "[bold green]DRY RUN (LOCAL SCAN)[/]"
        if dry_run
        else "[bold yellow]LIVE PR MODE[/]"
    )
    engine_status = (
        f"{provider.upper()} ({model}) [bold green][ONLINE][/]"
        if model
        else "[bold yellow]DETERMINISTIC (OFFLINE)[/]"
    )

    config_grid.add_row("[*] Target Directory", repo_path)
    config_grid.add_row("[*] Target Endpoint", endpoint)
    config_grid.add_row("[*] Security Engine", engine_status)
    config_grid.add_row("[*] Execution Mode", mode_status)
    config_grid.add_row("[*] Audit Standard", "OWASP Top 10 for LLM Applications (2025)")

    console.print(
        Panel(
            config_grid,
            title="SESSION CONFIGURATION",
            title_align="left",
            border_style="dim white",
        )
    )

    # Workflow pipeline indicator
    pipeline = (
        "[bold cyan][RECON][/] ---> "
        "[grey50][REDTEAM] ---> [REPRODUCE] ---> [PATCH] ---> [VERIFY] ---> [PR][/]"
    )
    console.print(f"\n  {pipeline}\n")


def print_summary(final_state: dict):
    exploits = final_state.get("exploits_found", [])
    test_results = final_state.get("test_results", {})
    pr_url = final_state.get("pr_url")
    branch = final_state.get("branch_name")

    # Executive KPI Summary Cards
    kpi_vulns = Panel(
        f"[bold {'red' if exploits else 'green'}]{len(exploits)}[/bold {'red' if exploits else 'green'}]",
        title="[bold]Vulnerabilities[/bold]",
        box=box.ROUNDED,
        border_style="red" if exploits else "green",
        width=20,
    )
    kpi_repro = Panel(
        "[bold green]PASS[/bold green]" if test_results.get("reproduction_test") else "[bold red]FAIL[/bold red]",
        title="[bold]Reproduction Test[/bold]",
        box=box.ROUNDED,
        border_style="green" if test_results.get("reproduction_test") else "red",
        width=22,
    )
    kpi_regr = Panel(
        "[bold green]PASS[/bold green]" if test_results.get("regression_suite") else "[bold red]FAIL[/bold red]",
        title="[bold]Regression Suite[/bold]",
        box=box.ROUNDED,
        border_style="green" if test_results.get("regression_suite") else "red",
        width=22,
    )
    kpi_pr = Panel(
        f"[bold blue]{'OPENED' if pr_url else 'LOCAL'}[/bold blue]",
        title="[bold]GitHub PR[/bold]",
        box=box.ROUNDED,
        border_style="blue",
        width=18,
    )
    console.print(Columns([kpi_vulns, kpi_repro, kpi_regr, kpi_pr]))
    console.print()

    if exploits:
        exp_table = Table(
            title="🛡️ Discovered Vulnerability Details & Remediations",
            title_style="bold white",
            show_header=True,
            header_style="bold white on blue",
            box=box.ROUNDED,
            border_style="blue",
        )
        exp_table.add_column("Severity", style="bold red", width=10, justify="center")
        exp_table.add_column("ID", style="bold cyan", width=16)
        exp_table.add_column("OWASP Category", width=28)
        exp_table.add_column("Failure Description & Exploit Evidence")

        for exp in exploits:
            exp_table.add_row(
                "HIGH",
                exp.get("id", "VULN"),
                exp.get("category", "General Security"),
                exp.get("vulnerability_reason", "Security bypass detected."),
            )
        console.print(exp_table)
        console.print()

        if pr_url:
            pr_panel = Panel(
                f"[bold white]Pull Request URL:[/bold white] [bold underline blue]{pr_url}[/bold underline blue]\n"
                f"[bold white]Git Branch:[/bold white] [cyan]{branch}[/cyan]\n\n"
                f"[dim]Security fix and isolated reproduction tests have been committed and verified.[/dim]",
                title="[bold green] 🚀 GitHub Integration Successful [/bold green]",
                box=box.ROUNDED,
                border_style="green",
            )
            console.print(pr_panel)
    else:
        success_panel = Panel(
            "[bold green]🎉 Application successfully passed all automated red-team checks![/bold green]\n"
            "[dim]No prompt injection, exfiltration, or unauthorized privilege violations detected.[/dim]",
            box=box.ROUNDED,
            border_style="green",
        )
        console.print(success_panel)


def main():
    args = parse_args()
    setup_logging(args.verbose)

    target_repo_path = str(Path(args.repo_path).resolve())
    if not os.path.exists(target_repo_path):
        console.print(f"[bold red]Error:[/bold red] Target repository path does not exist: {target_repo_path}")
        sys.exit(1)

    if args.groq_key:
        os.environ["GROQ_API_KEY"] = args.groq_key

    has_groq = bool(os.getenv("GROQ_API_KEY"))
    provider = args.provider if has_groq else "offline"
    model = "qwen/qwen3.6-27b" if has_groq else ""
    render_banner_ascii(
        repo_path=target_repo_path,
        endpoint=args.endpoint_url,
        provider=provider,
        model=model,
        dry_run=args.dry_run or not args.github_token,
    )

    initial_state = {
        "target_repo": target_repo_path,
        "target_endpoint": args.endpoint_url,
        "github_repo": args.github_repo,
        "github_token": None if args.dry_run else args.github_token,
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
        "max_retries": args.max_retries,
        "branch_name": None,
        "pr_url": None,
        "error": None,
    }

    app = create_security_app()
    final_state = app.invoke(initial_state)

    print_summary(final_state)

    # Export reports if requested
    reporter = SecurityReporter(final_state)
    if args.export_html:
        reporter.to_html(args.export_html)
        console.print(f"[bold white]📄 HTML Audit Report saved:[/bold white] [underline cyan]{args.export_html}[/underline cyan]")
    if args.export_json:
        reporter.to_json(args.export_json)
        console.print(f"[bold white]📊 JSON Audit Report saved:[/bold white] [underline cyan]{args.export_json}[/underline cyan]")
    if args.export_sarif:
        reporter.to_sarif(args.export_sarif)
        console.print(f"[bold white]🛡️ SARIF Audit Report saved:[/bold white] [underline cyan]{args.export_sarif}[/underline cyan]")


if __name__ == "__main__":
    main()

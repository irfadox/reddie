# 🚀 Launch Guide & Announcement: Reddie

Use this copy to announce **Reddie** across developer communities (Hacker News, Reddit, Twitter/X, and LinkedIn).

---

## 📢 Hacker News / "Show HN" Copy

**Title:**
> Show HN: Reddie – Autonomous AI Red-Teaming & GitHub PR Patching DevTool

**Body:**
```markdown
Hey HN,

We built **Reddie** (https://github.com/irfadox/reddie), an open-source DevSecOps tool that automatically discovers LLM application vulnerabilities, converts them into isolated `pytest` reproduction test suites, synthesizes hardened prompt/guardrail patches, verifies them in a test sandbox, and opens a GitHub Pull Request with the fix.

### Why we built this
Most LLM security tools today stop at reporting — giving you a PDF or dashboard with vague descriptions of prompt injections. Developers then have to spend hours trying to manually reproduce the attack, write a regression test, and figure out how to harden their prompts without breaking legitimate behavior.

### How it works under the hood
Reddie uses a multi-agent state graph (LangGraph) orchestrating specialized nodes:
1. **Reconnaissance:** AST-level parsing of Python, TypeScript, and JS files to extract system prompts, tool schemas, and agent definitions (supporting LangChain, LlamaIndex, CrewAI, and custom frameworks).
2. **Adversarial Fuzzing:** Simulates targeted prompt exfiltration, instruction overrides, persona jailbreaks, and tool overprivilege attacks mapped to the official OWASP Top 10 for LLM Applications (2025).
3. **Reproduction Test Generator:** Auto-generates standalone pytest files with isolated mock harnesses reproducing the exact failure.
4. **Adaptive Patch Synthesis:** Synthesizes context-aware prompt boundary locks and defensive guardrails.
5. **Sandbox Verifier & Auto-Repair Loop:** Executes reproduction + regression tests in a sandboxed subprocess. If existing unit tests fail, it adaptive-retries up to 3 times before deciding whether it's safe to submit.
6. **Git & GitHub PR Integration:** Pushes a security branch and opens a Pull Request with full SARIF, HTML, and JSON audit reports.

### Try it locally:
```bash
pip install reddie-ai
# or: pip install git+https://github.com/irfadox/reddie.git

# Fast offline heuristics scan:
reddie --repo-path ./my-llm-app --export-html report.html --dry-run

# AI-powered dynamic red-teaming:
export GROQ_API_KEY="gsk_..."
reddie --repo-path ./my-llm-app --export-html report.html --export-sarif report.sarif --dry-run
```

GitHub Action integration is also available as a turnkey workflow in our README.

We'd love to hear your feedback on our architecture and what attack vectors you'd like to see added next!

GitHub: https://github.com/irfadox/reddie
```

---

## 📱 Twitter / X Announcement Thread

**Tweet 1 (Hook):**
> 🛡️ Introducing **Reddie**: Autonomous AI Red-Teaming & GitHub PR Patching.
>
> It scans your LLM codebase for prompt injections & data leaks, turns exploits into isolated pytest test cases, auto-synthesizes patches, verifies them in a sandbox, and opens a GitHub PR.
>
> 100% Open Source 🧵👇
> [Include banner image: assets/banner.jpg]

**Tweet 2 (How it works):**
> Most LLM scanners just dump a PDF of warnings.
>
> Reddie closes the loop:
> 🔍 Static AST Recon $\to$
> 🎯 Adversarial Fuzzing $\to$
> 🧪 PyTest Reproduction Suite $\to$
> 🩹 Adaptive Prompt Patching $\to$
> 🔒 Sandbox Verification $\to$
> 🚀 GitHub PR Opened

**Tweet 3 (OWASP 2025 & Action):**
> Mapped directly to the official OWASP Top 10 for LLM Applications (2025):
> • LLM01: Prompt Injection
> • LLM02: Sensitive Info Disclosure
> • LLM06: Excessive Agency
> • LLM07: System Prompt Leakage
>
> Run it via CLI or as a GitHub Action in CI.

**Tweet 4 (CTA):**
> Check out the repo, star it, and run a scan on your agent app:
> 👉 https://github.com/irfadox/reddie

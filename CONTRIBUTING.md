# Contributing to Reddie

Thank you for your interest in contributing to Reddie! We welcome bug fixes, documentation improvements, new fuzzing heuristics, framework integrations, and feature contributions.

---

## 🧭 Code of Conduct

Please be respectful, collaborative, and constructive. We strive to maintain a welcoming, inclusive, and professional environment for all contributors.

---

## 🛠️ Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/irfadox/reddie.git
   cd reddie
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in editable mode with development dependencies:**
   ```bash
   pip install -e .
   pip install pytest pre-commit build twine
   ```

4. **Install pre-commit hooks:**
   ```bash
   pre-commit install
   ```

---

## 🧪 Testing Guidelines

Before submitting any code changes, ensure all tests pass:

```bash
pytest -v
```

When adding new features (such as a new static analyzer parser or report format), please add corresponding unit tests in the `tests/` directory.

---

## 📝 Commit Conventions

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` A new feature or capability
- `fix:` A bug fix or remediation correction
- `docs:` Documentation updates or explainer guides
- `test:` Adding or refactoring unit/integration tests
- `refactor:` Code improvements that do not alter public behavior
- `ci:` Updates to GitHub Actions, workflows, or packaging scripts

**Example:**
```bash
git commit -m "feat(analyzer): add support for Semantic Kernel prompt templates"
```

---

## 🚀 Pull Request Workflow

1. Fork the repository and create a feature branch (`git checkout -b feat/my-new-feature`).
2. Implement your changes with clean, well-documented code.
3. Run `pytest -v` to ensure the full test suite passes.
4. Push your branch to your fork (`git push origin feat/my-new-feature`).
5. Open a Pull Request on GitHub with a clear description of the problem and your solution.

---

## 🔒 Security & Vulnerability Reporting

If you discover a security vulnerability in Reddie itself, please do **not** open a public issue. Review our [SECURITY.md](SECURITY.md) policy for coordinated disclosure instructions.

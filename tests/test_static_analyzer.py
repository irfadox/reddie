"""Tests for StaticAnalyzer tool."""

import tempfile
from pathlib import Path
from tools.static_analyzer import StaticAnalyzer


def test_static_analyzer_python_prompts():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        py_file = tmp_path / "agent.py"
        py_file.write_text("""
SYSTEM_PROMPT = \"\"\"You are a customer support agent. Help users with their questions.\"\"\"

def dummy_helper():
    prompt = "Translate this text: {user_input}"
    return prompt
""", encoding="utf-8")

        analyzer = StaticAnalyzer(tmp_dir)
        result = analyzer.analyze()

        prompts = result.get("system_prompts", {})
        assert any("SYSTEM_PROMPT" in k for k in prompts.keys())
        assert "customer support agent" in str(prompts)


def test_static_analyzer_tools_detection():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        py_file = tmp_path / "tools.py"
        py_file.write_text("""
def tool(func):
    return func

@tool
def calculate_tax(income: float, rate: float = 0.2):
    \"\"\"Calculates tax amount for given income.\"\"\"
    return income * rate
""", encoding="utf-8")

        analyzer = StaticAnalyzer(tmp_dir)
        result = analyzer.analyze()

        tools = result.get("tool_definitions", [])
        assert len(tools) == 1
        assert tools[0]["function_name"] == "calculate_tax"
        assert "income" in tools[0]["arguments"]

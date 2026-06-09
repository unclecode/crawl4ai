import ast
from pathlib import Path


EXPECTED_REQUIRES_PYTHON = ">=3.10,<3.15"
ROOT = Path(__file__).resolve().parents[1]


def _read_pyproject_requires_python() -> str:
    in_project_section = False

    for line in (ROOT / "pyproject.toml").read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped == "[project]":
            in_project_section = True
            continue
        if in_project_section and stripped.startswith("["):
            break
        if in_project_section and stripped.startswith("requires-python"):
            return ast.literal_eval(stripped.split("=", 1)[1].strip())

    raise AssertionError("pyproject.toml is missing [project].requires-python")


def _read_setup_python_requires() -> str:
    tree = ast.parse((ROOT / "setup.py").read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "setup":
            continue
        for keyword in node.keywords:
            if keyword.arg == "python_requires":
                return ast.literal_eval(keyword.value)

    raise AssertionError("setup.py is missing setup(python_requires=...)")


def test_project_metadata_caps_future_python_versions() -> None:
    assert _read_pyproject_requires_python() == EXPECTED_REQUIRES_PYTHON


def test_legacy_setup_py_matches_project_python_requirement() -> None:
    assert _read_setup_python_requires() == EXPECTED_REQUIRES_PYTHON

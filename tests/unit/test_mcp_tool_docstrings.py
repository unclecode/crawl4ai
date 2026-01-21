"""
Test that MCP tools have proper docstrings for LLM tool descriptions.

This test uses AST parsing to avoid importing the server module which has
many dependencies that may not be available in a test environment.
"""

import ast
import os
from typing import Optional


def get_function_docstring(filepath: str, function_name: str) -> Optional[str]:
    """Parse a Python file and extract the docstring of a specific function."""
    with open(filepath, 'r') as f:
        tree = ast.parse(f.read())

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == function_name:
                return ast.get_docstring(node)
    return None


def test_get_markdown_has_docstring():
    """Test that the get_markdown endpoint has a docstring for MCP tool description."""
    server_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'deploy', 'docker', 'server.py'
    )
    docstring = get_function_docstring(server_path, 'get_markdown')

    assert docstring is not None, "get_markdown should have a docstring"
    assert len(docstring) > 0, "get_markdown docstring should not be empty"
    assert "Markdown" in docstring or "markdown" in docstring, \
        "get_markdown docstring should mention markdown"


def test_generate_html_has_docstring():
    """Test that the generate_html endpoint has a docstring for MCP tool description."""
    server_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'deploy', 'docker', 'server.py'
    )
    docstring = get_function_docstring(server_path, 'generate_html')

    assert docstring is not None, "generate_html should have a docstring"
    assert len(docstring) > 0, "generate_html docstring should not be empty"


if __name__ == "__main__":
    test_get_markdown_has_docstring()
    test_generate_html_has_docstring()
    print("All docstring tests passed!")

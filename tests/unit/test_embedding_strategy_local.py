"""
Test that EmbeddingStrategy correctly returns None for local embeddings.

When no embedding_llm_config is provided, the strategy should return None
from _get_embedding_llm_config_dict() to allow get_text_embeddings to use
local sentence-transformers instead of falling back to OpenAI.

This test uses AST parsing to verify the fix without importing the module
which has many dependencies that may not be available in a test environment.
"""

import ast
import os


def get_function_source(filepath: str, function_name: str) -> str:
    """Parse a Python file and extract the source of a specific function."""
    with open(filepath, 'r') as f:
        source = f.read()
        tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == function_name:
                return ast.get_source_segment(source, node)
    return None


def test_get_embedding_llm_config_dict_returns_none():
    """Test that _get_embedding_llm_config_dict returns None (not a fallback dict).

    The fix ensures that when no embedding_llm_config is provided, the method
    returns None instead of a fallback OpenAI configuration, allowing
    get_text_embeddings to use local sentence-transformers.
    """
    adaptive_crawler_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'crawl4ai', 'adaptive_crawler.py'
    )

    source = get_function_source(adaptive_crawler_path, '_get_embedding_llm_config_dict')
    assert source is not None, "Could not find _get_embedding_llm_config_dict function"

    # Verify the function returns None at the end (not a fallback dict)
    assert 'return None' in source, \
        "_get_embedding_llm_config_dict should return None when no config provided"

    # Verify it does NOT have the old fallback to OpenAI
    assert "openai/text-embedding-3-small" not in source, \
        "_get_embedding_llm_config_dict should not have hardcoded OpenAI fallback"

    # Verify the docstring mentions local embeddings
    assert 'local' in source.lower() or 'sentence-transformers' in source.lower(), \
        "_get_embedding_llm_config_dict docstring should mention local embeddings"


def test_return_type_is_optional():
    """Test that _get_embedding_llm_config_dict return type is Optional[Dict]."""
    adaptive_crawler_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'crawl4ai', 'adaptive_crawler.py'
    )

    with open(adaptive_crawler_path, 'r') as f:
        source = f.read()

    # Check that the function signature includes Optional[Dict] return type
    assert 'def _get_embedding_llm_config_dict(self) -> Optional[Dict]' in source, \
        "_get_embedding_llm_config_dict should have Optional[Dict] return type"


if __name__ == "__main__":
    test_get_embedding_llm_config_dict_returns_none()
    test_return_type_is_optional()
    print("All EmbeddingStrategy local embeddings tests passed!")

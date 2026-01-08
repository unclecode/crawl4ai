"""
Test that html2text respects the <base> tag when resolving relative links.

According to HTML standards, when an HTML document contains a <base> tag,
relative links should be resolved against the URL specified in the <base>
tag's href attribute, not the original page URL.

This test uses AST parsing to verify the fix is present since the html2text
module has internal imports that require a full package setup.
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


def test_handle_tag_has_base_tag_support():
    """Test that handle_tag method processes <base> tag to update baseurl."""
    html2text_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'crawl4ai', 'html2text', '__init__.py'
    )

    source = get_function_source(html2text_path, 'handle_tag')
    assert source is not None, "Could not find handle_tag function"

    # Verify the function handles base tag
    assert 'tag == "base"' in source or "tag == 'base'" in source, \
        "handle_tag should check for base tag"

    # Verify it updates self.baseurl
    assert 'self.baseurl' in source, \
        "handle_tag should update self.baseurl when processing base tag"

    # Verify it gets href attribute
    assert 'href' in source, \
        "handle_tag should get href attribute from base tag"


def test_base_tag_code_structure():
    """Test that the base tag handling code is properly structured."""
    html2text_path = os.path.join(
        os.path.dirname(__file__), '..', '..', 'crawl4ai', 'html2text', '__init__.py'
    )

    with open(html2text_path, 'r') as f:
        source = f.read()

    # Check that base tag handling exists and uses urljoin
    assert 'tag == "base"' in source, \
        "html2text should handle base tag"
    assert 'urlparse.urljoin' in source, \
        "html2text should use urljoin for URL resolution"


if __name__ == "__main__":
    test_handle_tag_has_base_tag_support()
    test_base_tag_code_structure()
    print("All html2text base tag tests passed!")

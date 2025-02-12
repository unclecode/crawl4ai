# ## Issue #236
# - **Last Updated:** 2024-11-11 01:42:14
# - **Title:** [user data crawling opens two windows, unable to control correct user browser](https://github.com/unclecode/crawl4ai/issues/236)
# - **State:** open

import os, sys, time

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
import os
import time
from typing import Dict, Any
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

# Get current directory
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


def print_test_result(name: str, result: Dict[str, Any], execution_time: float):
    """Helper function to print test results."""
    print(f"\n{'='*20} {name} {'='*20}")
    print(f"Execution time: {execution_time:.4f} seconds")

    # Save markdown to files
    for key, content in result.items():
        if isinstance(content, str):
            with open(__location__ + f"/output/{name.lower()}_{key}.md", "w") as f:
                f.write(content)

    # # Print first few lines of each markdown version
    # for key, content in result.items():
    #     if isinstance(content, str):
    #         preview = '\n'.join(content.split('\n')[:3])
    #         print(f"\n{key} (first 3 lines):")
    #         print(preview)
    #         print(f"Total length: {len(content)} characters")


def test_basic_markdown_conversion():
    """Test basic markdown conversion with links."""
    with open(__location__ + "/data/wikipedia.html", "r") as f:
        cleaned_html = f.read()

    generator = DefaultMarkdownGenerator()

    start_time = time.perf_counter()
    result = generator.generate_markdown(
        cleaned_html=cleaned_html, base_url="https://en.wikipedia.org"
    )
    execution_time = time.perf_counter() - start_time

    print_test_result(
        "Basic Markdown Conversion",
        {
            "raw": result.raw_markdown,
            "with_citations": result.markdown_with_citations,
            "references": result.references_markdown,
        },
        execution_time,
    )

    # Basic assertions
    assert result.raw_markdown, "Raw markdown should not be empty"
    assert result.markdown_with_citations, "Markdown with citations should not be empty"
    assert result.references_markdown, "References should not be empty"
    assert "⟨" in result.markdown_with_citations, "Citations should use ⟨⟩ brackets"
    assert (
        "## References" in result.references_markdown
    ), "Should contain references section"


def test_relative_links():
    """Test handling of relative links with base URL."""
    markdown = """
    Here's a [relative link](/wiki/Apple) and an [absolute link](https://example.com).
    Also an [image](/images/test.png) and another [page](/wiki/Banana).
    """

    generator = DefaultMarkdownGenerator()
    result = generator.generate_markdown(
        cleaned_html=markdown, base_url="https://en.wikipedia.org"
    )

    assert "https://en.wikipedia.org/wiki/Apple" in result.references_markdown
    assert "https://example.com" in result.references_markdown
    assert "https://en.wikipedia.org/images/test.png" in result.references_markdown


def test_duplicate_links():
    """Test handling of duplicate links."""
    markdown = """
    Here's a [link](/test) and another [link](/test) and a [different link](/other).
    """

    generator = DefaultMarkdownGenerator()
    result = generator.generate_markdown(
        cleaned_html=markdown, base_url="https://example.com"
    )

    # Count citations in markdown
    citations = result.markdown_with_citations.count("⟨1⟩")
    assert citations == 2, "Same link should use same citation number"


def test_link_descriptions():
    """Test handling of link titles and descriptions."""
    markdown = """
    Here's a [link with title](/test "Test Title") and a [link with description](/other) to test.
    """

    generator = DefaultMarkdownGenerator()
    result = generator.generate_markdown(
        cleaned_html=markdown, base_url="https://example.com"
    )

    assert (
        "Test Title" in result.references_markdown
    ), "Link title should be in references"
    assert (
        "link with description" in result.references_markdown
    ), "Link text should be in references"


def test_performance_large_document():
    """Test performance with large document."""
    with open(__location__ + "/data/wikipedia.md", "r") as f:
        markdown = f.read()

    # Test with multiple iterations
    iterations = 5
    times = []

    generator = DefaultMarkdownGenerator()

    for i in range(iterations):
        start_time = time.perf_counter()
        result = generator.generate_markdown(
            cleaned_html=markdown, base_url="https://en.wikipedia.org"
        )
        end_time = time.perf_counter()
        times.append(end_time - start_time)

    avg_time = sum(times) / len(times)
    print(f"\n{'='*20} Performance Test {'='*20}")
    print(
        f"Average execution time over {iterations} iterations: {avg_time:.4f} seconds"
    )
    print(f"Min time: {min(times):.4f} seconds")
    print(f"Max time: {max(times):.4f} seconds")


def test_image_links():
    """Test handling of image links."""
    markdown = """
    Here's an ![image](/image.png "Image Title") and another ![image](/other.jpg).
    And a regular [link](/page).
    """

    generator = DefaultMarkdownGenerator()
    result = generator.generate_markdown(
        cleaned_html=markdown, base_url="https://example.com"
    )

    assert (
        "![" in result.markdown_with_citations
    ), "Image markdown syntax should be preserved"
    assert (
        "Image Title" in result.references_markdown
    ), "Image title should be in references"


if __name__ == "__main__":
    print("Running markdown generation strategy tests...")

    test_basic_markdown_conversion()
    test_relative_links()
    test_duplicate_links()
    test_link_descriptions()
    test_performance_large_document()
    test_image_links()

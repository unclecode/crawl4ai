import sys

from _pytest.mark.structures import ParameterSet # pyright: ignore[reportPrivateImportUsage]
from crawl4ai.content_filter_strategy import BM25ContentFilter, PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import time
import pytest

TEST_HTML_SAMPLES = {
    "basic": """
        <body>
            <h1>Test Title</h1>
            <p>This is a test paragraph with <a href="http://example.com">a link</a>.</p>
            <div class="content">
                <h2>Section 1</h2>
                <p>More content here with <b>bold text</b>.</p>
            </div>
        </body>
    """,

    "complex": """
        <body>
            <nav>Navigation menu that should be removed</nav>
            <header>Header content to remove</header>
            <main>
                <article>
                    <h1>Main Article</h1>
                    <p>Important content paragraph with <a href="http://test.com">useful link</a>.</p>
                    <section>
                        <h2>Key Section</h2>
                        <p>Detailed explanation with multiple sentences. This should be kept
                           in the final output. Very important information here.</p>
                    </section>
                </article>
                <aside>Sidebar content to remove</aside>
            </main>
            <footer>Footer content to remove</footer>
        </body>
    """,

    "edge_cases": """
        <body>
            <div>
                <p></p>
                <p>   </p>
                <script>alert('remove me');</script>
                <div class="advertisement">Ad content to remove</div>
                <p class="social-share">Share buttons to remove</p>
                <h1>!!Special>> Characters## Title!!</h1>
                <pre><code>def test(): pass</code></pre>
            </div>
        </body>
    """,

    "links_citations": """
        <body>
            <h1>Article with Links</h1>
            <p>First link to <a href="http://example.com/1">Example 1</a></p>
            <p>Second link to <a href="http://example.com/2" title="Example 2">Test 2</a></p>
            <p>Image link: <img src="test.jpg" alt="test image"></p>
            <p>Repeated link to <a href="http://example.com/1">Example 1 again</a></p>
        </body>
    """,
}

GENERATORS = {
    "no_filter": DefaultMarkdownGenerator(),
    "pruning": DefaultMarkdownGenerator(
        content_filter=PruningContentFilter(threshold=0.48)
    ),
    "bm25": DefaultMarkdownGenerator(
        content_filter=BM25ContentFilter(
            user_query="test article content important"
        )
    )
}


def filter_params() -> list[ParameterSet]:
    """Return a list of test parameters for the content filter tests."""
    return [
        pytest.param(html, id=name) for name, html in TEST_HTML_SAMPLES.items()
    ]

@pytest.mark.parametrize("html", filter_params())
def test_content_filters(html: str):
    """Test various content filtering strategies and return length comparisons."""
    # Initialize filters
    pruning_filter = PruningContentFilter(
        threshold=0.48,
        threshold_type="fixed",
        min_word_threshold=2
    )

    bm25_filter = BM25ContentFilter(
        bm25_threshold=1.0,
        user_query="test article content important"
    )

    # Test PruningContentFilter
    start_time = time.time()
    pruned_content = pruning_filter.filter_content(html)
    pruning_time = time.time() - start_time

    # Test BM25ContentFilter
    start_time = time.time()
    bm25_content = bm25_filter.filter_content(html)
    bm25_time = time.time() - start_time

    assert len(pruned_content) > 0
    assert len(bm25_content) > 0
    print(f"Original length: {len(html)}")
    print(f"Pruned length: {sum(len(c) for c in pruned_content)} ({pruning_time:.3f}s)")
    print(f"BM25 length: {sum(len(c) for c in bm25_content)} ({bm25_time:.3f}s)")


def markdown_params() -> list[ParameterSet]:
    """Return a list of test parameters for the content filter tests."""
    params: list[ParameterSet] = []
    for name, html in TEST_HTML_SAMPLES.items():
        for gen_name, generator in GENERATORS.items():
            params.append(pytest.param(html, generator, id=f"{name}_{gen_name}"))
    return params

@pytest.mark.parametrize("html,generator", markdown_params())
def test_markdown_generation(html: str, generator: DefaultMarkdownGenerator):
    """Test markdown generation with different configurations."""

    start_time = time.time()
    result = generator.generate_markdown(
        html,
        base_url="http://example.com",
        citations=True
    )

    assert result is not None
    assert result.raw_markdown is not None
    assert result.fit_markdown is not None
    assert result.references_markdown is not None

    print(f"Time: {time.time() - start_time:.3f}s")
    print(f"Raw length: {len(result.raw_markdown)}")
    print(f"Fit length: {len(result.fit_markdown) if result.fit_markdown else 0}")
    print(f"Citations: {len(result.references_markdown)}")

if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))

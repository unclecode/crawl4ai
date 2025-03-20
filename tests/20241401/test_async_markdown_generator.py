import asyncio
from typing import Dict
from crawl4ai.content_filter_strategy import BM25ContentFilter, PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
import time

# Test HTML samples
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
            <h1>Document with Links</h1>
            <p>First link to <a href="http://example.com/1">Example 1</a></p>
            <p>Second link to <a href="http://example.com/2" title="Example 2">Test 2</a></p>
            <p>Image link: <img src="test.jpg" alt="test image"></p>
            <p>Repeated link to <a href="http://example.com/1">Example 1 again</a></p>
        </body>
    """,
}

def test_content_filters() -> Dict[str, Dict[str, int]]:
    """Test various content filtering strategies and return length comparisons."""
    results = {}
    
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
    
    # Test each HTML sample
    for test_name, html in TEST_HTML_SAMPLES.items():
        # Store results for this test case
        results[test_name] = {}
        
        # Test PruningContentFilter
        start_time = time.time()
        pruned_content = pruning_filter.filter_content(html)
        pruning_time = time.time() - start_time
        
        # Test BM25ContentFilter
        start_time = time.time()
        bm25_content = bm25_filter.filter_content(html)
        bm25_time = time.time() - start_time
        
        # Store results
        results[test_name] = {
            "original_length": len(html),
            "pruned_length": sum(len(c) for c in pruned_content),
            "bm25_length": sum(len(c) for c in bm25_content),
            "pruning_time": pruning_time,
            "bm25_time": bm25_time
        }
        
    return results

def test_markdown_generation():
    """Test markdown generation with different configurations."""
    results = []
    
    # Initialize generators with different configurations
    generators = {
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
    
    # Test each generator with each HTML sample
    for test_name, html in TEST_HTML_SAMPLES.items():
        for gen_name, generator in generators.items():
            start_time = time.time()
            result = generator.generate_markdown(
                html,
                base_url="http://example.com",
                citations=True
            )
            
            results.append({
                "test_case": test_name,
                "generator": gen_name,
                "time": time.time() - start_time,
                "raw_length": len(result.raw_markdown),
                "fit_length": len(result.fit_markdown) if result.fit_markdown else 0,
                "citations": len(result.references_markdown)
            })
    
    return results

def main():
    """Run all tests and print results."""
    print("Starting content filter tests...")
    filter_results = test_content_filters()
    
    print("\nContent Filter Results:")
    print("-" * 50)
    for test_name, metrics in filter_results.items():
        print(f"\nTest case: {test_name}")
        print(f"Original length: {metrics['original_length']}")
        print(f"Pruned length: {metrics['pruned_length']} ({metrics['pruning_time']:.3f}s)")
        print(f"BM25 length: {metrics['bm25_length']} ({metrics['bm25_time']:.3f}s)")
        
    print("\nStarting markdown generation tests...")
    markdown_results = test_markdown_generation()
    
    print("\nMarkdown Generation Results:")
    print("-" * 50)
    for result in markdown_results:
        print(f"\nTest: {result['test_case']} - Generator: {result['generator']}")
        print(f"Time: {result['time']:.3f}s")
        print(f"Raw length: {result['raw_length']}")
        print(f"Fit length: {result['fit_length']}")
        print(f"Citations: {result['citations']}")

if __name__ == "__main__":
    main()
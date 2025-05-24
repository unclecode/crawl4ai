```markdown
# Examples Outline for crawl4ai - deep_crawling Component

**Target Document Type:** Examples Collection
**Target Output Filename Suggestion:** `llm_examples_deep_crawling.md`
**Library Version Context:** 0.6.3
**Outline Generation Date:** 2025-05-24
---

This document provides a collection of runnable Python code examples for the `deep_crawling` component of the `crawl4ai` library. Each example aims to demonstrate a specific feature or usage pattern.

---
## 1. Deep Crawling Strategies

This section will cover the different traversal and processing strategies available for deep crawling.

### 1.1. `DeepCrawlDecorator`

#### 1.1.1. Example: Basic application of `DeepCrawlDecorator` to an `AsyncWebCrawler` instance.

This example shows how to apply the `DeepCrawlDecorator` to an `AsyncWebCrawler` instance, which augments its `arun` method with deep crawling capabilities.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import DeepCrawlDecorator, BFSDeeepCrawlStrategy

# Basic setup - crawl4ai_server needs to be running for live examples
# For simplicity, we'll often use example.com or raw HTML for self-contained tests.

async def decorator_basic_application():
    crawler = AsyncWebCrawler()
    # The decorator enhances the crawler instance
    deep_crawl_decorator = DeepCrawlDecorator(crawler)
    
    # The original arun method is still available if needed
    # For deep crawling, the decorated arun will be used implicitly 
    # when a deep_crawl_strategy is set in CrawlerRunConfig.
    
    print(f"Crawler 'arun' method before decoration: {crawler.arun}")
    
    # Apply the decorator
    # This typically happens inside the AsyncWebCrawler when a strategy is provided
    # but for demonstration, we can show it being applied manually.
    # In practice, you don't call DeepCrawlDecorator directly like this for arun.
    # The AsyncWebCrawler's __init__ or arun method would handle this.
    # This example is more conceptual to show the decorator's existence.

    # A more realistic scenario is providing the strategy to CrawlerRunConfig:
    bfs_strategy = BFSDeeepCrawlStrategy(max_depth=0)
    config = CrawlerRunConfig(deep_crawl_strategy=bfs_strategy)

    # When arun is called with a config that has a deep_crawl_strategy,
    # the decorator's logic (if active) would take over.
    # Let's simulate a simple crawl
    try:
        async with crawler: # Ensure crawler is started and closed
            result = await crawler.arun(url="http://example.com", config=config)
            if result.success:
                print(f"Successfully crawled {result.url} using decorator (implicitly).")
                print(f"Decorator active status: {deep_crawl_decorator.deep_crawl_active.get()}")
            else:
                print(f"Crawl failed: {result.error_message}")
    except Exception as e:
        print(f"An error occurred: {e}")


asyncio.run(decorator_basic_application())
```

#### 1.1.2. Example: Triggering a deep crawl via the decorated `arun` method using `BFSDeeepCrawlStrategy`.

This example demonstrates how providing a `deep_crawl_strategy` in `CrawlerRunConfig` automatically triggers the deep crawling logic managed by `DeepCrawlDecorator`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy

async def trigger_deep_crawl_with_decorator():
    # Define a BFS strategy
    bfs_strategy = BFSDeeepCrawlStrategy(max_depth=1, max_pages=3) 
    
    # Configure the crawler run to use this strategy
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=bfs_strategy,
        # For real crawls, ensure verbosity or specific logging for clarity
        # For this example, we'll print basic info from results
    )

    async with AsyncWebCrawler() as crawler:
        # The DeepCrawlDecorator is implicitly active due to deep_crawl_strategy in config
        print(f"Starting deep crawl with BFS strategy for http://example.com (max_depth=1, max_pages=3)")
        results_container = await crawler.arun(url="http://example.com", config=run_config)
        
        crawled_count = 0
        if results_container: # arun returns a list/generator container
            print("\n--- Crawl Results ---")
            async for result in results_container: # If stream=True
                if result.success:
                    crawled_count += 1
                    print(f"Crawled: {result.url} (Depth: {result.metadata.get('depth', 'N/A')})")
                else:
                    print(f"Failed: {result.url} - {result.error_message}")
            if not isinstance(results_container, types.AsyncGeneratorType): # if stream=False (batch mode)
                 for result in results_container:
                    if result.success:
                        crawled_count +=1
                        print(f"Crawled: {result.url} (Depth: {result.metadata.get('depth', 'N/A')})")
                    else:
                        print(f"Failed: {result.url} - {result.error_message}")


        print(f"\nTotal pages processed by deep crawl: {crawled_count}")

# Note: example.com might not have many links or varied depth.
# For a more illustrative output, a mock server or a known simple site would be better.
import types
asyncio.run(trigger_deep_crawl_with_decorator())
```

#### 1.1.3. Example: Showing `DeepCrawlDecorator` respects the `deep_crawl_active` context to prevent recursion.

This example conceptually illustrates how `DeepCrawlDecorator` uses a `ContextVar` (`deep_crawl_active`) to prevent recursive deep crawls if the decorated method were to call itself indirectly with another deep crawl strategy.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import DeepCrawlDecorator, BFSDeeepCrawlStrategy

async def decorator_recursion_prevention():
    # This is a conceptual example. In a real scenario, the AsyncWebCrawler
    # manages the decorator and its context.
    
    crawler_instance = AsyncWebCrawler()
    decorator = DeepCrawlDecorator(crawler_instance)

    # Simulate an initial call that sets the context
    print(f"Initial deep_crawl_active: {decorator.deep_crawl_active.get()}")
    token = decorator.deep_crawl_active.set(True)
    print(f"After setting, deep_crawl_active: {decorator.deep_crawl_active.get()}")

    # Now, imagine original_arun (if called within the strategy) tries to start another deep crawl
    # The decorator's __call__ would check deep_crawl_active.get()
    # If True, it would call the original_arun directly, not the strategy.

    # Simulate what would happen if a nested deep crawl was attempted:
    # A config that would normally trigger a deep crawl
    nested_strategy = BFSDeeepCrawlStrategy(max_depth=0)
    nested_config = CrawlerRunConfig(deep_crawl_strategy=nested_strategy)

    # If decorator.__call__(original_arun) is invoked while deep_crawl_active is True:
    if nested_config.deep_crawl_strategy and not decorator.deep_crawl_active.get():
        print("This part (nested deep crawl strategy execution) should NOT be reached if active.")
        # strategy_result = await nested_strategy.arun(...) 
    elif nested_config.deep_crawl_strategy and decorator.deep_crawl_active.get():
        print("Deep crawl already active. Nested strategy will be bypassed, original_arun would be called.")
        # original_arun_result = await original_arun(...)
    else:
        print("Not a deep crawl config or context not active.")

    decorator.deep_crawl_active.reset(token)
    print(f"After reset, deep_crawl_active: {decorator.deep_crawl_active.get()}")
    
    # In a real run with AsyncWebCrawler, this management is internal.
    # This example is to show the ContextVar's role.

asyncio.run(decorator_recursion_prevention())
```

### 1.2. `DeepCrawlStrategy` (Abstract Base Class - Conceptual)

#### 1.2.1. Note: This is an ABC.
Examples will use concrete implementations like `BFSDeeepCrawlStrategy`, `DFSDeeepCrawlStrategy`, and `BestFirstCrawlingStrategy`. This section provides conceptual examples of how the base strategy's `arun` method works.

#### 1.2.2. Example: Conceptual demonstration of the `arun` method dispatching to `_arun_batch` (non-streaming).

This shows that if `config.stream` is `False` (or not set, as `False` is default for strategies not explicitly setting it), the `arun` method of a `DeepCrawlStrategy` (like `BFSDeeepCrawlStrategy`) will internally call its `_arun_batch` method.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy # Using BFS as a concrete example

async def conceptual_arun_batch_dispatch():
    strategy = BFSDeeepCrawlStrategy(max_depth=0) # max_depth=0 for minimal crawl
    config = CrawlerRunConfig(stream=False) # Explicitly non-streaming

    # Mock the _arun_batch method to confirm it's called
    original_arun_batch = strategy._arun_batch
    called_arun_batch = False
    async def mock_arun_batch(*args, **kwargs):
        nonlocal called_arun_batch
        called_arun_batch = True
        # Simulate returning a list of results
        return await original_arun_batch(*args, **kwargs) 
    strategy._arun_batch = mock_arun_batch

    async with AsyncWebCrawler() as crawler:
        await strategy.arun(start_url="http://example.com", crawler=crawler, config=config)

    if called_arun_batch:
        print("Conceptual: strategy.arun() correctly dispatched to _arun_batch() for non-streaming mode.")
    else:
        print("Conceptual: strategy.arun() DID NOT dispatch to _arun_batch().")
    
    # Restore original method
    strategy._arun_batch = original_arun_batch

asyncio.run(conceptual_arun_batch_dispatch())
```

#### 1.2.3. Example: Conceptual demonstration of the `arun` method dispatching to `_arun_stream` (streaming).

This shows that if `config.stream` is `True`, the `arun` method of a `DeepCrawlStrategy` (like `BFSDeeepCrawlStrategy`) will internally call its `_arun_stream` method.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy # Using BFS as a concrete example

async def conceptual_arun_stream_dispatch():
    strategy = BFSDeeepCrawlStrategy(max_depth=0)
    config = CrawlerRunConfig(stream=True) # Explicitly streaming

    # Mock the _arun_stream method
    original_arun_stream = strategy._arun_stream
    called_arun_stream = False
    async def mock_arun_stream(*args, **kwargs):
        nonlocal called_arun_stream
        called_arun_stream = True
        # Simulate yielding results from an async generator
        async for item in original_arun_stream(*args, **kwargs):
            yield item
    strategy._arun_stream = mock_arun_stream
    
    async with AsyncWebCrawler() as crawler:
        async for _ in strategy.arun(start_url="http://example.com", crawler=crawler, config=config):
            pass # Consume the generator

    if called_arun_stream:
        print("Conceptual: strategy.arun() correctly dispatched to _arun_stream() for streaming mode.")
    else:
        print("Conceptual: strategy.arun() DID NOT dispatch to _arun_stream().")

    # Restore original method
    strategy._arun_stream = original_arun_stream

asyncio.run(conceptual_arun_stream_dispatch())
```

#### 1.2.4. Example: Demonstrating `ValueError` when `CrawlerRunConfig` is not provided to `arun`.

This example demonstrates that calling `strategy.arun(...)` without a `config` (or with `config=None`) raises a `ValueError`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy

async def arun_without_config():
    strategy = BFSDeeepCrawlStrategy(max_depth=0)
    async with AsyncWebCrawler() as crawler:
        try:
            await strategy.arun(start_url="http://example.com", crawler=crawler, config=None)
        except ValueError as e:
            print(f"Caught expected ValueError: {e}")
        except Exception as e:
            print(f"Caught unexpected error: {e}")
        else:
            print("ValueError was not raised as expected.")

asyncio.run(arun_without_config())
```

#### 1.2.5. Example: Demonstrating the `__call__` method making the strategy instance callable.

The `__call__` method allows a strategy instance to be called directly like a function, which internally calls its `arun` method.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy

async def strategy_is_callable():
    strategy = BFSDeeepCrawlStrategy(max_depth=0, max_pages=1)
    config = CrawlerRunConfig()

    async with AsyncWebCrawler() as crawler:
        print("Calling strategy instance directly using __call__...")
        # This is equivalent to strategy.arun(...)
        results_container = await strategy(start_url="http://example.com", crawler=crawler, config=config)
        
        if results_container:
            for result in results_container: # If batch mode
                 if result.success:
                    print(f"Callable strategy crawled: {result.url}")
                 else:
                    print(f"Callable strategy failed for {result.url}: {result.error_message}")
        else:
            print("Strategy call did not return results.")

asyncio.run(strategy_is_callable())
```

### 1.3. `BFSDeeepCrawlStrategy` (Breadth-First Search)

#### 1.3.1. **Initialization & Basic Usage**

##### 1.3.1.1. Example: Initializing `BFSDeeepCrawlStrategy` with a `max_depth` of 1 and performing a basic batch crawl.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy

async def bfs_basic_batch_crawl():
    # Initialize BFS strategy: crawl up to 1 level deep from the start URL
    # and fetch a maximum of 5 pages in total.
    bfs_strategy = BFSDeeepCrawlStrategy(max_depth=1, max_pages=5)
    
    # Create a run configuration using this strategy
    # stream=False is the default for batch mode
    run_config = CrawlerRunConfig(deep_crawl_strategy=bfs_strategy)

    async with AsyncWebCrawler() as crawler:
        print("Starting BFS batch crawl (max_depth=1, max_pages=5) on http://example.com...")
        # arun returns a list of CrawlResult objects in batch mode
        results_list = await crawler.arun(url="http://example.com", config=run_config)
        
        print(f"\n--- BFS Batch Crawl Results (max_depth=1, max_pages=5) ---")
        if results_list:
            for result in results_list:
                if result.success:
                    print(f"Crawled: {result.url} (Depth: {result.metadata.get('depth')})")
                else:
                    print(f"Failed: {result.url} - {result.error_message}")
            print(f"Total pages processed: {len(results_list)}")
        else:
            print("No results returned from crawl.")

# Note: example.com has very few links, so it might not reach max_pages=5 or depth=1.
# A site with more links like docs.crawl4ai.com would be more illustrative if accessible.
asyncio.run(bfs_basic_batch_crawl())
```

##### 1.3.1.2. Example: Performing a BFS crawl in stream mode (`config.stream=True`).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy

async def bfs_stream_crawl():
    # Initialize BFS strategy
    bfs_strategy = BFSDeeepCrawlStrategy(max_depth=1, max_pages=3)
    
    # Enable stream mode in the run configuration
    run_config = CrawlerRunConfig(deep_crawl_strategy=bfs_strategy, stream=True)

    async with AsyncWebCrawler() as crawler:
        print("Starting BFS stream crawl (max_depth=1, max_pages=3) on http://example.com...")
        # arun returns an async generator in stream mode
        results_generator = await crawler.arun(url="http://example.com", config=run_config)
        
        print(f"\n--- BFS Stream Crawl Results ---")
        processed_count = 0
        async for result in results_generator:
            processed_count +=1
            if result.success:
                print(f"Streamed: {result.url} (Depth: {result.metadata.get('depth')})")
            else:
                print(f"Stream Failed: {result.url} - {result.error_message}")
        print(f"Total pages streamed: {processed_count}")

asyncio.run(bfs_stream_crawl())
```

#### 1.3.2. **Controlling Crawl Depth and Scope**

##### 1.3.2.1. Example: Demonstrating `max_depth` limiting the crawl (e.g., `max_depth=0` for only the start URL).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy

async def bfs_max_depth_zero():
    # max_depth=0 means only the starting URL will be crawled.
    bfs_strategy = BFSDeeepCrawlStrategy(max_depth=0, max_pages=5) # max_pages won't be hit
    run_config = CrawlerRunConfig(deep_crawl_strategy=bfs_strategy)

    async with AsyncWebCrawler() as crawler:
        print("Starting BFS crawl with max_depth=0 on http://example.com...")
        results_list = await crawler.arun(url="http://example.com", config=run_config)
        
        print(f"\n--- BFS Crawl Results (max_depth=0) ---")
        if results_list:
            for result in results_list:
                print(f"Crawled: {result.url} (Depth: {result.metadata.get('depth')})")
            print(f"Total pages processed: {len(results_list)}")
            assert len(results_list) == 1, "Should only crawl the start URL with max_depth=0"
            assert results_list[0].metadata.get('depth') == 0, "Depth should be 0"
        else:
            print("No results returned.")

asyncio.run(bfs_max_depth_zero())
```

##### 1.3.2.2. Example: Demonstrating `max_pages` limiting the number of crawled pages.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy

# For this example, we'll use a site that likely has more than 2 links accessible
# from the start page to demonstrate max_pages.
# If docs.crawl4ai.com is not available, replace with another suitable site.
# Or, use raw HTML with multiple links.
TARGET_URL = "https://docs.crawl4ai.com/core/async-web-crawler/" 

async def bfs_max_pages_limit():
    # Crawl up to depth 2, but stop after 2 pages.
    bfs_strategy = BFSDeeepCrawlStrategy(max_depth=2, max_pages=2)
    run_config = CrawlerRunConfig(deep_crawl_strategy=bfs_strategy)

    async with AsyncWebCrawler() as crawler:
        print(f"Starting BFS crawl with max_pages=2 on {TARGET_URL}...")
        results_list = await crawler.arun(url=TARGET_URL, config=run_config)
        
        print(f"\n--- BFS Crawl Results (max_pages=2) ---")
        crawled_urls = []
        if results_list:
            for result in results_list:
                if result.success:
                    print(f"Crawled: {result.url} (Depth: {result.metadata.get('depth')})")
                    crawled_urls.append(result.url)
            print(f"Total pages processed: {len(results_list)}")
            # The number of results might be slightly more than max_pages
            # due to how BFS processes levels, but pages_crawled stat should be accurate.
            # print(f"Strategy stats: Pages crawled = {bfs_strategy.stats._pages_crawled}")
            # For simplicity, we check len(results_list) but acknowledge bfs_strategy.stats is more precise.
            assert len(crawled_urls) <= 2, "Should process at most max_pages"
        else:
            print("No results returned.")

asyncio.run(bfs_max_pages_limit())
```

##### 1.3.2.3. Example: BFS crawl including external links (`include_external=True`).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy

# We need a page with known external links. example.com might have iana.org.
# For a more robust test, a mock HTML would be better.
RAW_HTML_WITH_EXTERNAL_LINK = """
<html><body>
    <a href="http://example.com/internal">Internal Link</a>
    <a href="https://www.iana.org/domains/reserved">External IANA Link</a>
    <a href="http://another-external.com">Another External</a>
</body></html>
"""
START_URL_RAW = f"raw://{RAW_HTML_WITH_EXTERNAL_LINK}"


async def bfs_include_external():
    # Crawl depth 1, include external links, limit to 3 pages to see some externals.
    bfs_strategy = BFSDeeepCrawlStrategy(max_depth=1, max_pages=3, include_external=True)
    run_config = CrawlerRunConfig(deep_crawl_strategy=bfs_strategy)

    async with AsyncWebCrawler() as crawler:
        print(f"Starting BFS crawl including external links (max_depth=1, max_pages=3)...")
        results_list = await crawler.arun(url=START_URL_RAW, config=run_config)
        
        print(f"\n--- BFS Crawl Results (include_external=True) ---")
        external_found = False
        if results_list:
            for result in results_list:
                if result.success:
                    print(f"Crawled: {result.url} (Depth: {result.metadata.get('depth')})")
                    if "iana.org" in result.url or "another-external.com" in result.url:
                        external_found = True
                else:
                    print(f"Failed: {result.url} - {result.error_message}")
            print(f"Total pages processed: {len(results_list)}")
            assert external_found, "Expected to crawl at least one external link."
        else:
            print("No results returned.")

asyncio.run(bfs_include_external())
```

#### 1.3.3. **Filtering and Scoring**

##### 1.3.3.1. Example: Using `BFSDeeepCrawlStrategy` with a `FilterChain` to include/exclude specific URLs.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy, FilterChain, URLPatternFilter, DomainFilter

RAW_HTML_FOR_FILTERING = """
<html><body>
    <a href="http://example.com/page1.html">Page 1 (HTML)</a>
    <a href="http://example.com/image.png">Image (PNG)</a>
    <a href="http://example.com/docs/doc1.pdf">Doc 1 (PDF)</a>
    <a href="http://external.com/anotherpage">External Page</a>
    <a href="http://example.com/blog/post1">Blog Post 1</a>
</body></html>
"""
START_URL_RAW_FILTER = f"raw://{RAW_HTML_FOR_FILTERING}"

async def bfs_with_filter_chain():
    # Allow only HTML files from example.com
    filter_chain = FilterChain(filters=[
        DomainFilter(allowed_domains=["example.com"]),
        URLPatternFilter(patterns=["*.html"]) 
    ])
    
    bfs_strategy = BFSDeeepCrawlStrategy(max_depth=1, max_pages=5, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=bfs_strategy)

    async with AsyncWebCrawler() as crawler:
        print("Starting BFS crawl with FilterChain (allow *.html from example.com)...")
        results_list = await crawler.arun(url=START_URL_RAW_FILTER, config=run_config)
        
        print(f"\n--- BFS Crawl Results (with FilterChain) ---")
        crawled_urls = []
        if results_list:
            for result in results_list:
                if result.success:
                    print(f"Crawled: {result.url}")
                    crawled_urls.append(result.url)
            print(f"Total pages processed: {len(results_list)}")
            
            assert all("example.com" in url for url in crawled_urls if url != START_URL_RAW_FILTER), "Only example.com URLs should be crawled (excluding start)."
            assert all(url.endswith(".html") for url in crawled_urls if url != START_URL_RAW_FILTER), "Only .html URLs should be crawled (excluding start)."
            assert "http://example.com/page1.html" in crawled_urls
            assert "http://example.com/image.png" not in crawled_urls
            assert "http://example.com/docs/doc1.pdf" not in crawled_urls
            assert "http://external.com/anotherpage" not in crawled_urls
            assert "http://example.com/blog/post1" not in crawled_urls

        else:
            print("No results returned.")

asyncio.run(bfs_with_filter_chain())
```

##### 1.3.3.2. Example: Using `BFSDeeepCrawlStrategy` with a `url_scorer` and `score_threshold` to prune links.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy, PathDepthScorer

RAW_HTML_FOR_SCORING = """
<html><body>
    <a href="/page1">Page 1 (depth 1)</a>
    <a href="/category/page2">Page 2 (depth 2)</a>
    <a href="/category/sub/page3">Page 3 (depth 3)</a>
    <a href="/very/deep/path/page4">Page 4 (depth 4)</a>
</body></html>
"""
START_URL_RAW_SCORE = f"raw://{RAW_HTML_FOR_SCORING}"


async def bfs_with_scorer_and_threshold():
    # Score by path depth, optimal depth is 1.
    # Threshold will prune links that are too deep (lower score).
    # PathDepthScorer gives 1.0 for optimal, 0.5 for diff 1, 0.33 for diff 2, etc.
    url_scorer = PathDepthScorer(optimal_depth=1) 
    score_threshold = 0.4  # This should allow depth 1 (score 1.0) and depth 2 (score 0.5) links, but not depth 3 (score 0.33)

    bfs_strategy = BFSDeeepCrawlStrategy(
        max_depth=3, 
        max_pages=5, 
        url_scorer=url_scorer, 
        score_threshold=score_threshold
    )
    run_config = CrawlerRunConfig(deep_crawl_strategy=bfs_strategy)

    async with AsyncWebCrawler() as crawler:
        print("Starting BFS crawl with URL scorer and threshold (optimal_depth=1, threshold=0.4)...")
        results_list = await crawler.arun(url=START_URL_RAW_SCORE, config=run_config)
        
        print(f"\n--- BFS Crawl Results (with Scorer & Threshold) ---")
        crawled_urls = []
        if results_list:
            for result in results_list:
                if result.success:
                    print(f"Crawled: {result.url} (Depth: {result.metadata.get('depth')}, Score: {result.metadata.get('score', 'N/A')})")
                    crawled_urls.append(result.url)
            print(f"Total pages processed: {len(results_list)}")
            
            assert any("/page1" in url for url in crawled_urls)
            assert any("/category/page2" in url for url in crawled_urls)
            assert not any("/category/sub/page3" in url for url in crawled_urls)
            assert not any("/very/deep/path/page4" in url for url in crawled_urls)
        else:
            print("No results returned.")

asyncio.run(bfs_with_scorer_and_threshold())
```

#### 1.3.4. **URL Processing Logic**

##### 1.3.4.1. Example: Demonstrating `can_process_url` for valid and invalid URL formats (e.g., missing scheme, unsupported scheme).

The `can_process_url` method is primarily used internally by strategies. We can test its behavior directly for demonstration.

```python
import asyncio
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy

async def demo_can_process_url_formats():
    strategy = BFSDeeepCrawlStrategy(max_depth=1) # Filters are not applied at depth 0 by default

    print("Testing can_process_url (at depth=1, default filters):")
    
    valid_http_url = "http://example.com/page"
    can_process_http = await strategy.can_process_url(valid_http_url, depth=1)
    print(f"Can process '{valid_http_url}'? {can_process_http}")
    assert can_process_http

    valid_https_url = "https://example.com/secure"
    can_process_https = await strategy.can_process_url(valid_https_url, depth=1)
    print(f"Can process '{valid_https_url}'? {can_process_https}")
    assert can_process_https

    url_missing_scheme = "example.com/page" # This would typically be resolved by normalize_url_for_deep_crawl
                                          # but can_process_url expects a full URL.
                                          # Let's assume it's already normalized to http://example.com/page
    # For direct test of can_process_url, it would fail if scheme is missing before normalization
    # Assuming it's passed post-normalization phase where scheme is present for this check
    
    url_ftp_scheme = "ftp://example.com/file"
    can_process_ftp = await strategy.can_process_url(url_ftp_scheme, depth=1)
    print(f"Can process '{url_ftp_scheme}' (unsupported scheme)? {can_process_ftp}")
    assert not can_process_ftp # FTP is not a supported scheme by default

    url_no_netloc = "http:///page" # Invalid netloc
    can_process_no_netloc = await strategy.can_process_url(url_no_netloc, depth=1)
    print(f"Can process '{url_no_netloc}' (no netloc)? {can_process_no_netloc}")
    assert not can_process_no_netloc
    
    # Depth 0 always bypasses filters in default can_process_url logic of strategies
    can_process_depth_zero = await strategy.can_process_url(url_ftp_scheme, depth=0)
    print(f"Can process '{url_ftp_scheme}' at depth 0 (bypassing filters)? {can_process_depth_zero}")
    assert can_process_depth_zero

asyncio.run(demo_can_process_url_formats())
```

##### 1.3.4.2. Example: Demonstrating `can_process_url` with a `filter_chain` that rejects certain URLs.

```python
import asyncio
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy, FilterChain, URLPatternFilter

async def demo_can_process_url_with_filter():
    # Filter chain that rejects URLs containing "admin"
    filter_chain = FilterChain(filters=[
        URLPatternFilter(patterns=["*admin*"], reverse=True) # reverse=True means reject if matches
    ])
    strategy = BFSDeeepCrawlStrategy(max_depth=1, filter_chain=filter_chain)

    print("Testing can_process_url with a filter_chain (rejecting '*admin*'):")

    url_to_allow = "http://example.com/dashboard"
    can_process_allow = await strategy.can_process_url(url_to_allow, depth=1)
    print(f"Can process '{url_to_allow}'? {can_process_allow}")
    assert can_process_allow

    url_to_reject = "http://example.com/admin/login"
    can_process_reject = await strategy.can_process_url(url_to_reject, depth=1)
    print(f"Can process '{url_to_reject}'? {can_process_reject}")
    assert not can_process_reject

asyncio.run(demo_can_process_url_with_filter())
```

#### 1.3.5. **Link Discovery**

The `link_discovery` method is internal. Its effects are best observed through the URLs selected for the next level of a crawl.

##### 1.3.5.1. Example: Showing how `link_discovery` populates the `next_level` for BFS.

This conceptual example shows how `link_discovery` (if it were public and directly callable for this purpose) would take a `CrawlResult` and populate a `next_level` list.

```python
import asyncio
from crawl4ai.models import CrawlResult, Links, Link
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy
from crawl4ai.utils import normalize_url_for_deep_crawl

# Simulate a CrawlResult
mock_crawl_result = CrawlResult(
    url="http://example.com/source",
    html="<a href='/page1'>Page 1</a> <a href='page2.html'>Page 2</a>",
    success=True,
    links=Links(
        internal=[
            Link(href="/page1", text="Page 1"),
            Link(href="page2.html", text="Page 2")
        ],
        external=[]
    )
)

async def demo_link_discovery_populates_next_level():
    strategy = BFSDeeepCrawlStrategy(max_depth=1)
    
    # Simulate internal state for link_discovery
    source_url = mock_crawl_result.url
    current_depth = 0
    visited = {source_url}
    next_level_links = [] # This is what link_discovery populates
    depths = {source_url: 0}

    # Call link_discovery (conceptually)
    # In real code, this is an internal method: strategy.link_discovery(...)
    # We'll manually simulate its core logic for this demonstration.
    
    next_depth = current_depth + 1
    if next_depth <= strategy.max_depth:
        discovered_links_from_result = []
        for link_type in ["internal", "external"] if strategy.include_external else ["internal"]:
            for link_obj in getattr(mock_crawl_result.links, link_type, []):
                link_href = link_obj.href
                if link_href:
                    # Normalize URL (simplified for example)
                    abs_url = normalize_url_for_deep_crawl(link_href, source_url)
                    if abs_url and abs_url not in visited:
                        if await strategy.can_process_url(abs_url, next_depth):
                             if strategy.url_scorer:
                                score = await strategy.url_scorer.score(abs_url)
                                if score < strategy.score_threshold:
                                    strategy.stats.urls_skipped +=1
                                    continue
                             discovered_links_from_result.append((abs_url, source_url))
                             visited.add(abs_url)
                             depths[abs_url] = next_depth
        
        next_level_links.extend(discovered_links_from_result)


    print(f"Source URL: {source_url}")
    print(f"Discovered and added to next_level (url, parent_url):")
    for link_info in next_level_links:
        print(f"  - {link_info[0]} (from {link_info[1]}) at depth {depths[link_info[0]]}")

    assert ("http://example.com/page1", "http://example.com/source") in next_level_links
    assert ("http://example.com/page2.html", "http://example.com/source") in next_level_links
    assert depths.get("http://example.com/page1") == 1
    assert depths.get("http://example.com/page2.html") == 1

asyncio.run(demo_link_discovery_populates_next_level())
```

##### 1.3.5.2. Example: How `link_discovery` respects `max_pages` when adding new links.

This conceptual example shows how `link_discovery` would limit adding new links if `max_pages` is about to be reached.

```python
import asyncio
from crawl4ai.models import CrawlResult, Links, Link
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy
from crawl4ai.utils import normalize_url_for_deep_crawl


mock_crawl_result_many_links = CrawlResult(
    url="http://example.com/source_many",
    html="""
        <a href="/link1">1</a> <a href="/link2">2</a> <a href="/link3">3</a>
        <a href="/link4">4</a> <a href="/link5">5</a>
    """,
    success=True,
    links=Links(
        internal=[
            Link(href="/link1"), Link(href="/link2"), Link(href="/link3"),
            Link(href="/link4"), Link(href="/link5")
        ]
    )
)

async def demo_link_discovery_respects_max_pages():
    # Max 3 pages total, already crawled 1 (the start URL)
    # So, only 2 more pages can be added from discovered links.
    strategy = BFSDeeepCrawlStrategy(max_depth=1, max_pages=3)
    strategy._pages_crawled = 1 # Simulate start URL already crawled

    source_url = mock_crawl_result_many_links.url
    current_depth = 0
    visited = {source_url}
    next_level_links_tuples = []
    depths = {source_url: 0}

    # Manual simulation of link_discovery's core logic for this specific scenario
    next_depth = current_depth + 1
    valid_links_to_consider = []
    
    if next_depth <= strategy.max_depth:
        for link_type in ["internal"]: # Assuming include_external is False
            for link_obj in getattr(mock_crawl_result_many_links.links, link_type, []):
                link_href = link_obj.href
                if link_href:
                    abs_url = normalize_url_for_deep_crawl(link_href, source_url)
                    if abs_url and abs_url not in visited:
                        if await strategy.can_process_url(abs_url, next_depth):
                            valid_links_to_consider.append(abs_url)
                            # visited.add(abs_url) # Add to visited only if selected
                            # depths[abs_url] = next_depth # Add depth only if selected
    
    remaining_capacity = strategy.max_pages - strategy._pages_crawled
    
    if remaining_capacity > 0 and valid_links_to_consider:
        # If scoring is involved, links would be sorted by score here. For simplicity, we take first N.
        selected_links = valid_links_to_consider[:remaining_capacity]
        if len(valid_links_to_consider) > remaining_capacity and strategy.logger:
            strategy.logger.info(f"Limiting to {remaining_capacity} URLs due to max_pages limit")
            
        for sel_url in selected_links:
            next_level_links_tuples.append((sel_url, source_url))
            visited.add(sel_url)
            depths[sel_url] = next_depth

    print(f"Source URL: {source_url}")
    print(f"Pages already crawled: {strategy._pages_crawled}")
    print(f"Max pages: {strategy.max_pages}, Remaining capacity: {remaining_capacity}")
    print(f"Discovered and added to next_level due to max_pages limit:")
    for link_url, parent_url in next_level_links_tuples:
        print(f"  - {link_url} (from {parent_url}) at depth {depths.get(link_url)}")
    
    assert len(next_level_links_tuples) <= remaining_capacity, f"Expected {remaining_capacity} links, got {len(next_level_links_tuples)}"
    assert len(next_level_links_tuples) == 2 # 3 (max_pages) - 1 (already_crawled) = 2

asyncio.run(demo_link_discovery_respects_max_pages())
```

#### 1.3.6. **Shutdown**

##### 1.3.6.1. Example: Demonstrating the `shutdown` method and its effect on crawl stats (e.g., `end_time`).

```python
import asyncio
import time
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy

async def demo_shutdown_method():
    strategy = BFSDeeepCrawlStrategy(max_depth=1)
    print(f"Initial strategy stats: Start time: {strategy.stats.start_time}, End time: {strategy.stats.end_time}")
    
    # Simulate some activity
    strategy.stats.urls_processed = 5
    await asyncio.sleep(0.1) # Simulate time passing
    
    await strategy.shutdown()
    
    print(f"Stats after shutdown: Start time: {strategy.stats.start_time}, End time: {strategy.stats.end_time}")
    assert strategy.stats.end_time is not None, "End time should be set after shutdown"
    assert strategy.stats.end_time > strategy.stats.start_time, "End time should be after start time"

asyncio.run(demo_shutdown_method())
```

### 1.4. `DFSDeeepCrawlStrategy` (Depth-First Search)

#### 1.4.1. **Initialization & Basic Usage**

##### 1.4.1.1. Example: Initializing `DFSDeeepCrawlStrategy` with a `max_depth` of 2 and performing a basic batch DFS crawl.
For DFS, a site with clear branching is needed to see the depth-first behavior. `example.com` has limited depth. We'll use a mock structure.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import DFSDeeepCrawlStrategy

# Mock HTML for DFS demonstration
# Page A -> B, C
# Page B -> D
# Page C -> E
RAW_HTML_DFS_A = "<html><body><a href='raw://PAGE_B'>B</a> <a href='raw://PAGE_C'>C</a></body></html>"
RAW_HTML_DFS_B = "<html><body><a href='raw://PAGE_D'>D</a></body></html>"
RAW_HTML_DFS_C = "<html><body><a href='raw://PAGE_E'>E</a></body></html>"
RAW_HTML_DFS_D = "<html><body>Depth 2 D</body></html>"
RAW_HTML_DFS_E = "<html><body>Depth 2 E</body></html>"

# Replace placeholders with actual raw content for the crawler
START_URL_DFS = f"raw://{RAW_HTML_DFS_A.replace('PAGE_B', RAW_HTML_DFS_B).replace('PAGE_C', RAW_HTML_DFS_C).replace('PAGE_D', RAW_HTML_DFS_D).replace('PAGE_E', RAW_HTML_DFS_E)}"

async def dfs_basic_batch_crawl():
    dfs_strategy = DFSDeeepCrawlStrategy(max_depth=2, max_pages=5)
    run_config = CrawlerRunConfig(deep_crawl_strategy=dfs_strategy)

    async with AsyncWebCrawler() as crawler:
        print("Starting DFS batch crawl (max_depth=2, max_pages=5)...")
        # arun for DFS is expected to return results in a somewhat depth-first order
        results_list = await crawler.arun(url=START_URL_DFS, config=run_config)
        
        print(f"\n--- DFS Batch Crawl Results (Order may vary based on internal async processing but generally depth-first) ---")
        crawled_urls_with_depth = []
        if results_list:
            for result in results_list:
                if result.success:
                    depth = result.metadata.get('depth', 'N/A')
                    print(f"Crawled: {result.url_for_display()} (Depth: {depth})") # Using url_for_display for raw URLs
                    crawled_urls_with_depth.append((result.url_for_display(), depth))
            print(f"Total pages processed: {len(results_list)}")
            
            # Assertions to check if expected pages were crawled (order can be tricky with async)
            # We expect all 5 mock pages if max_pages=5 and max_depth=2 allows
            page_names = [url_display.split("<body>")[1].split("</body>")[0].strip() for url_display, _ in crawled_urls_with_depth if "raw://" in url_display and "<body>" in url_display]
            assert "Depth 2 D" in page_names or "Depth 2 E" in page_names, "Expected to reach depth 2"

        else:
            print("No results returned from crawl.")
            
# Replace placeholders correctly for the crawler to understand nested raw URLs
# This is tricky because the raw URL itself contains other raw URLs.
# A proper mock server or carefully crafted single raw HTML would be better.
# For now, this is a conceptual example of the expected DFS behavior.
# The current raw URL setup is too complex for simple string replacement.

async def dfs_basic_batch_crawl_simplified():
    # Simpler mock for easier verification.
    # A -> B ; B -> C
    html_c = "<html><body>Page C (depth 2)</body></html>"
    html_b = f"<html><body>Page B (depth 1) <a href='raw://{html_c}'>Link to C</a></body></html>"
    start_url_dfs_simple = f"raw://<html><body>Page A (depth 0) <a href='raw://{html_b}'>Link to B</a></body></html>"

    dfs_strategy = DFSDeeepCrawlStrategy(max_depth=2, max_pages=3)
    run_config = CrawlerRunConfig(deep_crawl_strategy=dfs_strategy)

    async with AsyncWebCrawler() as crawler:
        print("Starting DFS batch crawl (max_depth=2, max_pages=3) on simplified mock...")
        results_list = await crawler.arun(url=start_url_dfs_simple, config=run_config)
        
        print(f"\n--- DFS Batch Crawl Results (Simplified Mock) ---")
        crawled_info = []
        if results_list:
            for result in results_list:
                if result.success:
                    depth = result.metadata.get('depth', 'N/A')
                    # Extract a simple identifier from the raw HTML for easier assertion
                    content_id = "Unknown"
                    if "Page A" in result.html: content_id="A"
                    elif "Page B" in result.html: content_id="B"
                    elif "Page C" in result.html: content_id="C"
                    print(f"Crawled: Page {content_id} (Depth: {depth})")
                    crawled_info.append({"id": content_id, "depth": depth, "url": result.url_for_display()})
            print(f"Total pages processed: {len(results_list)}")
            
            # Expected order for DFS: A, B, C (or A, C, B depending on link order in A if it had multiple)
            # With the given structure (A -> B, B -> C), order should be A, B, C
            if len(crawled_info) == 3:
                assert crawled_info[0]["id"] == "A" and crawled_info[0]["depth"] == 0
                assert crawled_info[1]["id"] == "B" and crawled_info[1]["depth"] == 1
                assert crawled_info[2]["id"] == "C" and crawled_info[2]["depth"] == 2
                print("DFS order appears correct for this simplified structure.")
            else:
                print(f"Expected 3 pages, got {len(crawled_info)}. Crawled: {crawled_info}")


asyncio.run(dfs_basic_batch_crawl_simplified())
```

##### 1.4.1.2. Example: Performing a DFS crawl in stream mode (`config.stream=True`), highlighting the order of results.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import DFSDeeepCrawlStrategy

# Simplified mock for DFS streaming order demonstration
# A -> B, D
# B -> C
# D -> E
async def dfs_stream_crawl_order():
    html_e = "<html><body>Page E (depth 2 from D)</body></html>"
    html_d = f"<html><body>Page D (depth 1) <a href='raw://{html_e}'>Link to E</a></body></html>"
    html_c = "<html><body>Page C (depth 2 from B)</body></html>"
    html_b = f"<html><body>Page B (depth 1) <a href='raw://{html_c}'>Link to C</a></body></html>"
    start_url_dfs_stream = f"raw://<html><body>Page A (depth 0) <a href='raw://{html_b}'>Link to B</a> <a href='raw://{html_d}'>Link to D</a></body></html>"


    dfs_strategy = DFSDeeepCrawlStrategy(max_depth=2, max_pages=5)
    # Stream mode
    run_config = CrawlerRunConfig(deep_crawl_strategy=dfs_strategy, stream=True)

    async with AsyncWebCrawler() as crawler:
        print("Starting DFS stream crawl (max_depth=2, max_pages=5)...")
        results_generator = await crawler.arun(url=start_url_dfs_stream, config=run_config)
        
        print(f"\n--- DFS Stream Crawl Results (Order of processing) ---")
        crawled_order_ids = []
        async for result in results_generator:
            if result.success:
                depth = result.metadata.get('depth', 'N/A')
                content_id = "Unknown"
                if "Page A" in result.html: content_id="A"
                elif "Page B" in result.html: content_id="B"
                elif "Page C" in result.html: content_id="C"
                elif "Page D" in result.html: content_id="D"
                elif "Page E" in result.html: content_id="E"
                print(f"Streamed: Page {content_id} (Depth: {depth})")
                crawled_order_ids.append(content_id)
            else:
                print(f"Stream Failed: {result.url_for_display()} - {result.error_message}")
        
        print(f"Crawled order: {crawled_order_ids}")
        # Expected DFS orders (stack behavior, depends on which link is pushed last/first):
        # If D is processed before B from A: A, D, E, B, C
        # If B is processed before D from A: A, B, C, D, E
        # The `reverse=True` on new_links in dfs_strategy.py means the *first* link in HTML is processed *last* by stack.
        # So, if A has links to B then D, D will be put on stack last, thus popped (processed) first.
        expected_order_1 = ['A', 'D', 'E', 'B', 'C'] # If "Link to D" is processed from stack first
        expected_order_2 = ['A', 'B', 'C', 'D', 'E'] # If "Link to B" is processed from stack first

        # Given the current DFS implementation pushes in reversed order of discovery
        # and HTML link order is B then D, D gets added to stack on top of B.
        # So D's branch should be explored first.
        assert crawled_order_ids == expected_order_1 or crawled_order_ids == expected_order_2, \
            f"DFS order incorrect. Expected one of {expected_order_1} or {expected_order_2}, got {crawled_order_ids}"


asyncio.run(dfs_stream_crawl_order())
```

#### 1.4.2. **Controlling Crawl Depth and Scope**

##### 1.4.2.1. Example: Demonstrating `max_depth` limiting the DFS crawl.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import DFSDeeepCrawlStrategy

async def dfs_max_depth_limit():
    html_c = "<html><body>Page C (depth 2)</body></html>"
    html_b = f"<html><body>Page B (depth 1) <a href='raw://{html_c}'>Link to C</a></body></html>"
    start_url_dfs_simple = f"raw://<html><body>Page A (depth 0) <a href='raw://{html_b}'>Link to B</a></body></html>"

    # Set max_depth to 1. Page C (depth 2) should not be crawled.
    dfs_strategy = DFSDeeepCrawlStrategy(max_depth=1, max_pages=5)
    run_config = CrawlerRunConfig(deep_crawl_strategy=dfs_strategy)

    async with AsyncWebCrawler() as crawler:
        print("Starting DFS crawl with max_depth=1...")
        results_list = await crawler.arun(url=start_url_dfs_simple, config=run_config)
        
        print(f"\n--- DFS Crawl Results (max_depth=1) ---")
        crawled_pages_at_depth = {}
        if results_list:
            for result in results_list:
                if result.success:
                    depth = result.metadata.get('depth')
                    crawled_pages_at_depth.setdefault(depth, []).append(result.url_for_display())
                    print(f"Crawled: {result.url_for_display()} (Depth: {depth})")
            print(f"Total pages processed: {len(results_list)}")
            
            assert 0 in crawled_pages_at_depth
            assert 1 in crawled_pages_at_depth
            assert 2 not in crawled_pages_at_depth, "Should not crawl beyond max_depth=1"
            assert len(results_list) == 2 # Page A and Page B
        else:
            print("No results returned.")

asyncio.run(dfs_max_depth_limit())
```

##### 1.4.2.2. Example: Demonstrating `max_pages` limiting the number of crawled pages during DFS.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import DFSDeeepCrawlStrategy

async def dfs_max_pages_limit():
    html_c = "<html><body>Page C (depth 2)</body></html>"
    html_b = f"<html><body>Page B (depth 1) <a href='raw://{html_c}'>Link to C</a></body></html>"
    start_url_dfs_simple = f"raw://<html><body>Page A (depth 0) <a href='raw://{html_b}'>Link to B</a></body></html>"

    # max_pages = 2 means only Page A and Page B should be crawled.
    dfs_strategy = DFSDeeepCrawlStrategy(max_depth=2, max_pages=2)
    run_config = CrawlerRunConfig(deep_crawl_strategy=dfs_strategy)

    async with AsyncWebCrawler() as crawler:
        print("Starting DFS crawl with max_pages=2...")
        results_list = await crawler.arun(url=start_url_dfs_simple, config=run_config)
        
        print(f"\n--- DFS Crawl Results (max_pages=2) ---")
        crawled_count = 0
        if results_list:
            for result in results_list:
                if result.success:
                    crawled_count +=1
                    print(f"Crawled: {result.url_for_display()} (Depth: {result.metadata.get('depth')})")
            print(f"Total pages processed: {crawled_count}")
            assert crawled_count <= 2, "Should process at most max_pages"
             # Check strategy's internal count for precision
            assert strategy._pages_crawled <= 2
        else:
            print("No results returned.")

asyncio.run(dfs_max_pages_limit())
```

#### 1.4.3. **Traversal Order**

##### 1.4.3.1. Example: A small site crawl demonstrating the LIFO (stack-like) behavior of DFS link processing.
(This is effectively covered by 1.4.1.2. The stream mode example shows the order of processing which is a direct result of LIFO.)
We can re-emphasize it or consider this covered. For completeness, a slight variation:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import DFSDeeepCrawlStrategy

async def dfs_lifo_demonstration():
    # Structure: A -> [B, D], B -> C, D -> E
    # HTML links in order: B then D
    # DFS stack (simplified, top is right):
    # Initial: [A]
    # Pop A, discover B, D. Push D, then B. Stack: [B, D]
    # Pop D, discover E. Push E. Stack: [B, E]
    # Pop E. Stack: [B]
    # Pop B, discover C. Push C. Stack: [C]
    # Pop C. Stack: []
    # Expected processing order: A, D, E, B, C (because D is pushed last from A's links, so processed first)
    
    html_e = "<html><body>Page E (child of D)</body></html>"
    html_d = f"<html><body>Page D <a href='raw://{html_e}'>To E</a></body></html>"
    html_c = "<html><body>Page C (child of B)</body></html>"
    html_b = f"<html><body>Page B <a href='raw://{html_c}'>To C</a></body></html>"
    # Links in A are ordered B then D
    start_url_dfs_lifo = f"raw://<html><body>Page A <a href='raw://{html_b}'>To B</a> <a href='raw://{html_d}'>To D</a></body></html>"

    dfs_strategy = DFSDeeepCrawlStrategy(max_depth=2, max_pages=5)
    run_config = CrawlerRunConfig(deep_crawl_strategy=dfs_strategy, stream=True) # Stream to see order

    async with AsyncWebCrawler() as crawler:
        print("Demonstrating DFS LIFO behavior (stream mode)...")
        crawled_ids_in_order = []
        async for result in await crawler.arun(url=start_url_dfs_lifo, config=run_config):
            if result.success:
                content_id = "Unknown"
                if "Page A" in result.html: content_id="A"
                elif "Page B" in result.html: content_id="B"
                elif "Page C" in result.html: content_id="C"
                elif "Page D" in result.html: content_id="D"
                elif "Page E" in result.html: content_id="E"
                print(f"Processed: Page {content_id} (Depth: {result.metadata.get('depth')})")
                crawled_ids_in_order.append(content_id)
        
        print(f"\nActual processing order: {crawled_ids_in_order}")
        # Based on current DFS strategy (reversing links before adding to stack):
        # Links from A: B, D. Reversed: D, B. Stack (top right): [B, D]
        # Pop D, links: E. Stack: [B, E]
        # Pop E. Stack: [B]
        # Pop B, links: C. Stack: [C]
        # Pop C. Stack: []
        # Order: A, D, E, B, C
        expected_order = ['A', 'D', 'E', 'B', 'C']
        assert crawled_ids_in_order == expected_order, f"Expected LIFO order {expected_order}, got {crawled_ids_in_order}"

asyncio.run(dfs_lifo_demonstration())
```

### 1.5. `BestFirstCrawlingStrategy`

#### 1.5.1. **Initialization & Basic Usage**

##### 1.5.1.1. Example: Initializing `BestFirstCrawlingStrategy` with `max_depth` and a `url_scorer`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy, KeywordRelevanceScorer

async def best_first_init_and_usage():
    # Score URLs based on keyword "product"
    keyword_scorer = KeywordRelevanceScorer(keywords=["product"])
    
    best_first_strategy = BestFirstCrawlingStrategy(
        max_depth=1, 
        max_pages=3,
        url_scorer=keyword_scorer
    )
    
    run_config = CrawlerRunConfig(deep_crawl_strategy=best_first_strategy)

    # Mock HTML for demonstration
    html_product = "<html><body><a href='/product-page.html'>Cool Product</a> Product details...</body></html>"
    html_blog = "<html><body><a href='/blog-post.html'>Blog Post</a> News and updates...</body></html>"
    html_contact = "<html><body><a href='/contact.html'>Contact Us</a> Get in touch...</body></html>"
    
    start_url_best_first = f"""raw://<html><body>
        <h1>Welcome</h1>
        <a href="raw://{html_product.replace('"', '&quot;')}">View Product</a>
        <a href="raw://{html_blog.replace('"', '&quot;')}">Read Blog</a>
        <a href="raw://{html_contact.replace('"', '&quot;')}">Contact</a>
    </body></html>"""


    async with AsyncWebCrawler() as crawler:
        print("Starting Best-First crawl (scoring for 'product')...")
        results_list = await crawler.arun(url=start_url_best_first, config=run_config)
        
        print(f"\n--- Best-First Crawl Results (Batch) ---")
        if results_list:
            for result in results_list:
                if result.success:
                    print(f"Crawled: {result.url_for_display()} (Score: {result.metadata.get('score', 'N/A')}, Depth: {result.metadata.get('depth')})")
            # Expect product page to be crawled due to higher score
            assert any("product-page.html" in res.url_for_display() for res in results_list if res.success), "Product page should have been crawled."
        else:
            print("No results from crawl.")

asyncio.run(best_first_init_and_usage())
```

##### 1.5.1.2. Example: Performing a Best-First crawl in batch mode.
(Covered by 1.5.1.1, as batch mode is default if `stream=False` is not specified or is False in `CrawlerRunConfig` for the strategy)

##### 1.5.1.3. Example: Performing a Best-First crawl in stream mode.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy, KeywordRelevanceScorer

async def best_first_stream_mode():
    keyword_scorer = KeywordRelevanceScorer(keywords=["feature"])
    
    best_first_strategy = BestFirstCrawlingStrategy(
        max_depth=1, 
        max_pages=3,
        url_scorer=keyword_scorer
    )
    
    run_config = CrawlerRunConfig(deep_crawl_strategy=best_first_strategy, stream=True)

    html_feature = "<html><body><a href='/new-feature.html'>New Feature</a> Details about feature...</body></html>"
    html_about = "<html><body><a href='/about-us.html'>About Us</a> Company info...</body></html>"
    
    start_url_stream = f"""raw://<html><body>
        <a href="raw://{html_feature.replace('"', '&quot;')}">Amazing Feature</a>
        <a href="raw://{html_about.replace('"', '&quot;')}">About Page</a>
    </body></html>"""

    async with AsyncWebCrawler() as crawler:
        print("Starting Best-First stream crawl (scoring for 'feature')...")
        results_generator = await crawler.arun(url=start_url_stream, config=run_config)
        
        print(f"\n--- Best-First Stream Crawl Results ---")
        async for result in results_generator:
            if result.success:
                print(f"Streamed: {result.url_for_display()} (Score: {result.metadata.get('score', 'N/A')}, Depth: {result.metadata.get('depth')})")
            else:
                print(f"Stream Failed: {result.url_for_display()} - {result.error_message}")

asyncio.run(best_first_stream_mode())
```

#### 1.5.2. **Priority-Based Crawling**

##### 1.5.2.1. Example: Demonstrating how `url_scorer` (e.g., `KeywordRelevanceScorer`) influences the crawl order.
(Effectively demonstrated in 1.5.1.1 and 1.5.1.3 where pages containing the keyword are prioritized. We can make a more direct comparison here.)

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy, KeywordRelevanceScorer

async def best_first_order_influence():
    # Scenario 1: Prioritize "tutorials"
    tutorial_scorer = KeywordRelevanceScorer(keywords=["tutorial"])
    strategy_tut = BestFirstCrawlingStrategy(max_depth=1, max_pages=3, url_scorer=tutorial_scorer)
    config_tut = CrawlerRunConfig(deep_crawl_strategy=strategy_tut, stream=True)

    # Scenario 2: Prioritize "pricing"
    pricing_scorer = KeywordRelevanceScorer(keywords=["pricing"])
    strategy_price = BestFirstCrawlingStrategy(max_depth=1, max_pages=3, url_scorer=pricing_scorer)
    config_price = CrawlerRunConfig(deep_crawl_strategy=strategy_price, stream=True)

    html_home = """<html><body>
        <a href="raw_tut.html">Tutorials</a>
        <a href="raw_price.html">Pricing Info</a>
        <a href="raw_blog.html">Blog</a>
    </body></html>"""
    html_tut = "<html><body>Learn with our tutorial.</body></html>"
    html_price = "<html><body>Check our pricing plans.</body></html>"
    html_blog = "<html><body>Latest news from our blog.</body></html>"
    
    # Create self-contained raw URLs
    start_url = f"raw://{html_home.replace('raw_tut.html', f'raw://{html_tut.replace(&quot;,&quot;&amp;quot;&quot;)}').replace('raw_price.html', f'raw://{html_price.replace(&quot;,&quot;&amp;quot;&quot;)}').replace('raw_blog.html', f'raw://{html_blog.replace(&quot;,&quot;&amp;quot;&quot;)}')}"


    async with AsyncWebCrawler() as crawler:
        print("\n--- Crawling with 'tutorial' priority ---")
        order_tut = []
        async for result in await crawler.arun(url=start_url, config=config_tut):
            if result.success:
                order_tut.append(result.url_for_display())
                print(f"  Crawled (tut): {result.url_for_display()} Score: {result.metadata.get('score')}")
        
        print("\n--- Crawling with 'pricing' priority ---")
        order_price = []
        async for result in await crawler.arun(url=start_url, config=config_price): # Re-crawl for new strategy application
            if result.success:
                order_price.append(result.url_for_display())
                print(f"  Crawled (price): {result.url_for_display()} Score: {result.metadata.get('score')}")
        
        # Assertions are tricky due to async nature and BATCH_SIZE. 
        # The goal is that the higher-scored item (if within the first BATCH_SIZE) appears earlier.
        # For a small number of links (3 in this case), it should be quite deterministic.
        # Assuming BATCH_SIZE is >= 3 or more links are processed per batch.

        # Check if "tutorial" related page is prioritized in first run (could be 2nd after start_url)
        if len(order_tut) > 1:
            assert any("tutorial" in url_disp.lower() for url_disp in order_tut[1:2]), \
                f"Tutorial link was not prioritized. Order: {order_tut}"
        
        # Check if "pricing" related page is prioritized in second run
        if len(order_price) > 1:
            assert any("pricing" in url_disp.lower() for url_disp in order_price[1:2]), \
                f"Pricing link was not prioritized. Order: {order_price}"

asyncio.run(best_first_order_influence())
```

##### 1.5.2.2. Example: Showing how `BATCH_SIZE` affects the processing of URLs from the priority queue.

`BATCH_SIZE` in `BestFirstCrawlingStrategy` determines how many URLs are fetched from the priority queue at once to be processed by `crawler.arun_many`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy, KeywordRelevanceScorer
from crawl4ai.deep_crawling.bff_strategy import BATCH_SIZE as BFF_BATCH_SIZE # Import to show its value

# This example is more conceptual as BATCH_SIZE is a module-level constant.
# We can illustrate its effect by showing how many URLs are processed in parallel
# if we could control it or if the number of high-priority URLs is less/more than BATCH_SIZE.

# For demonstration, let's assume we have many high-priority links.
# The strategy will pull BATCH_SIZE of them at a time.
async def best_first_batch_size_effect():
    print(f"Current BATCH_SIZE for BestFirstCrawlingStrategy: {BFF_BATCH_SIZE}")

    # Create more links than BATCH_SIZE to see the batching effect
    num_links = BFF_BATCH_SIZE + 5 
    links_html = ""
    for i in range(num_links):
        # All links will have the keyword to make them high priority
        html_content = f"<html><body>Content with keyword 'important' number {i}</body></html>"
        links_html += f"<a href='raw_link_{i}.html'>Link {i} (important)</a>\n"
        # This creates placeholder names, actual content needs to be embedded for raw://
        # For simplicity in this example, we won't fully embed, but focus on the number of links
        # that *would* be processed.

    start_url_batch_effect = f"raw://<html><body>{links_html}</body></html>"
    
    # Mock the crawler.arun_many to see how many URLs it receives in one call
    class MockCrawler(AsyncWebCrawler):
        async def arun_many(self, urls, config, **kwargs):
            print(f"MockCrawler.arun_many called with {len(urls)} URLs: {urls[:3]}...") # Show first 3
            # Simulate successful crawl for all
            mock_results = []
            for i, url_str in enumerate(urls):
                # Simplified HTML content based on the URL
                html_content = f"<html><body>Mock content for {url_str.split('/')[-1]}</body></html>"
                # Determine depth; for this mock, assume all are depth 1 if not start_url
                depth = 1 if url_str != start_url_batch_effect else 0
                
                mock_results.append(self._create_crawl_result(
                    url=url_str,
                    html=html_content, # Create some HTML for each
                    success=True,
                    status_code=200,
                    metadata={"depth": depth, "score": 1.0}, # Mock score
                    config=config
                ))
            return mock_results

    scorer = KeywordRelevanceScorer(keywords=["important"])
    strategy = BestFirstCrawlingStrategy(max_depth=1, max_pages=num_links + 1, url_scorer=scorer)
    # Note: max_pages is set high to not interfere with BATCH_SIZE demonstration for link discovery
    
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy)

    async with MockCrawler() as crawler:
        print(f"Starting Best-First crawl with {num_links} high-priority links...")
        # This will call arun_many multiple times if num_links > BATCH_SIZE
        results_list = await crawler.arun(url=start_url_batch_effect, config=run_config)
        
        print(f"\n--- Best-First Crawl (BATCH_SIZE effect) ---")
        if results_list:
            print(f"Total pages processed: {len(results_list)-1}") # -1 for the start URL itself
            # Further assertions could be made if arun_many was more intricately mocked to track calls.
        else:
            print("No results returned.")
    print("Observe the 'MockCrawler.arun_many called with...' print statements.")
    print("If num_links > BATCH_SIZE, you should see multiple calls to arun_many, "
          f"each with up to {BFF_BATCH_SIZE} URLs.")

asyncio.run(best_first_batch_size_effect())
```

#### 1.5.3. **Controlling Crawl Scope**

##### 1.5.3.1. Example: Best-First crawl with `max_depth` reached.
(Similar to BFS/DFS max_depth, BestFirst also respects it.)

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy, PathDepthScorer

async def best_first_max_depth():
    html_c = "<html><body>Page C (depth 2)</body></html>"
    html_b = f"<html><body>Page B (depth 1) <a href='raw://{html_c}'>Link to C</a></body></html>"
    start_url_simple = f"raw://<html><body>Page A (depth 0) <a href='raw://{html_b}'>Link to B</a></body></html>"

    # Score by path depth, optimal is 0 to ensure links are explored if possible
    scorer = PathDepthScorer(optimal_depth=0) 
    
    # max_depth=1 should stop before Page C
    strategy = BestFirstCrawlingStrategy(max_depth=1, max_pages=5, url_scorer=scorer)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        print("Starting Best-First crawl with max_depth=1...")
        results_list = await crawler.arun(url=start_url_simple, config=run_config)
        
        print(f"\n--- Best-First Crawl Results (max_depth=1) ---")
        crawled_depths = set()
        if results_list:
            for result in results_list:
                if result.success:
                    depth = result.metadata.get('depth')
                    crawled_depths.add(depth)
                    print(f"Crawled: {result.url_for_display()} (Depth: {depth})")
            print(f"Depths crawled: {crawled_depths}")
            assert 2 not in crawled_depths, "Should not have crawled to depth 2"
            assert len(results_list) == 2 # Page A and Page B
        else:
            print("No results.")

asyncio.run(best_first_max_depth())
```

##### 1.5.3.2. Example: Best-First crawl with `max_pages` reached.
(Similar to BFS/DFS max_pages, BestFirst also respects it.)

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy, PathDepthScorer

async def best_first_max_pages():
    html_c = "<html><body>Page C (depth 2)</body></html>"
    html_b = f"<html><body>Page B (depth 1) <a href='raw://{html_c}'>Link to C</a></body></html>"
    start_url_simple = f"raw://<html><body>Page A (depth 0) <a href='raw://{html_b}'>Link to B</a></body></html>"
    
    scorer = PathDepthScorer(optimal_depth=0) # Score to explore if possible
    
    # max_pages=2 should process only Page A and Page B
    strategy = BestFirstCrawlingStrategy(max_depth=2, max_pages=2, url_scorer=scorer)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        print("Starting Best-First crawl with max_pages=2...")
        results_list = await crawler.arun(url=start_url_simple, config=run_config)
        
        crawled_count = 0
        if results_list:
            print(f"\n--- Best-First Crawl Results (max_pages=2) ---")
            for result in results_list:
                if result.success:
                    crawled_count += 1
                    print(f"Crawled: {result.url_for_display()} (Depth: {result.metadata.get('depth')})")
            print(f"Total pages processed: {crawled_count}")
            assert crawled_count <= 2
            # Check strategy's internal count for precision
            assert strategy._pages_crawled <= 2
        else:
            print("No results.")
            
asyncio.run(best_first_max_pages())
```

#### 1.5.4. **Link Discovery and Scoring**

##### 1.5.4.1. Example: `link_discovery` adding new links to the priority queue based on their scores.
(This is implicitly shown in examples 1.5.1.1 and 1.5.2.1, where higher-scored links are processed. The priority queue mechanism itself is internal to `BestFirstCrawlingStrategy`.)
This conceptual example will show how `link_discovery` calculates scores and would (internally) add items with scores to the priority queue.

```python
import asyncio
from crawl4ai.models import CrawlResult, Links, Link
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy, KeywordRelevanceScorer
from crawl4ai.utils import normalize_url_for_deep_crawl

mock_crawl_result_for_scoring = CrawlResult(
    url="http://example.com/home",
    html="""
        <a href="/product-feature.html">Feature Page</a>
        <a href="/about-us.html">About Page</a>
        <a href="/another-feature.html">Another Feature</a>
    """,
    success=True,
    links=Links(
        internal=[
            Link(href="/product-feature.html"), Link(href="/about-us.html"), Link(href="/another-feature.html")
        ]
    )
)

async def demo_best_first_link_discovery_scoring():
    scorer = KeywordRelevanceScorer(keywords=["feature"]) # Prioritize "feature"
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=scorer)
    
    # Simulate internal state for link_discovery
    source_url = mock_crawl_result_for_scoring.url
    current_depth = 0 # Depth of the source_url
    visited = {source_url}
    # PriorityQueue would store (negative_score, depth, url, parent_url)
    # We'll simulate the items that would be put into it.
    priority_queue_items_to_add = [] 
    depths = {source_url: 0}

    # Manual simulation of link_discovery's core logic
    next_depth = current_depth + 1
    if next_depth <= strategy.max_depth:
        for link_obj in mock_crawl_result_for_scoring.links.internal:
            abs_url = normalize_url_for_deep_crawl(link_obj.href, source_url)
            if abs_url and abs_url not in visited:
                if await strategy.can_process_url(abs_url, next_depth): # Standard checks
                    score = await strategy.url_scorer.score(abs_url) # Score the URL
                    # Store with negative score because asyncio.PriorityQueue is a min-heap
                    priority_queue_items_to_add.append((-score, next_depth, abs_url, source_url))
                    visited.add(abs_url) # Mark as "to be processed"
                    depths[abs_url] = next_depth
    
    # Sort by score (descending, as priority queue would handle)
    priority_queue_items_to_add.sort(key=lambda x: x[0], reverse=True) # Actually sorts by -score asc -> score desc

    print(f"Source URL: {source_url}")
    print(f"Items that would be added to priority queue (score, depth, url, parent):")
    for neg_score, depth_val, url_val, parent_val in priority_queue_items_to_add:
        print(f"  - Score: {-neg_score:.2f}, Depth: {depth_val}, URL: {url_val}")

    assert len(priority_queue_items_to_add) == 3
    # Check if "feature" links have higher scores (lower negative_score, appear earlier after sort)
    assert "product-feature.html" in priority_queue_items_to_add[0][2] or "another-feature.html" in priority_queue_items_to_add[0][2]
    assert "product-feature.html" in priority_queue_items_to_add[1][2] or "another-feature.html" in priority_queue_items_to_add[1][2]
    assert "about-us.html" in priority_queue_items_to_add[2][2] # Should have lower score

asyncio.run(demo_best_first_link_discovery_scoring())
```

---
## 2. URL Filters

This section demonstrates how to use various filters to control which URLs are processed during a deep crawl.

### 2.1. `FilterStats`

#### 2.1.1. Example: Accessing `total_urls`, `passed_urls`, and `rejected_urls` from a `FilterStats` object after applying a filter.

```python
import asyncio
from crawl4ai.deep_crawling import URLPatternFilter, FilterStats

async def demo_filter_stats():
    # Create a filter (e.g., allow only .html files)
    html_filter = URLPatternFilter(patterns=["*.html"])

    urls_to_test = [
        "http://example.com/index.html",
        "http://example.com/script.js",
        "http://example.com/about.html",
        "http://example.com/image.png",
    ]

    print("Applying URLPatternFilter (allow *.html):")
    for url in urls_to_test:
        # The apply method updates stats internally
        passed = await html_filter.apply(url) 
        print(f"  URL: {url}, Passed: {passed}")

    # Access the stats from the filter instance
    stats = html_filter.stats
    print(f"\n--- Filter Stats ---")
    print(f"Total URLs processed: {stats.total_urls}")
    print(f"Passed URLs: {stats.passed_urls}")
    print(f"Rejected URLs: {stats.rejected_urls}")

    assert stats.total_urls == 4
    assert stats.passed_urls == 2
    assert stats.rejected_urls == 2

asyncio.run(demo_filter_stats())
```

### 2.2. `FilterChain`

#### 2.2.1. Example: Creating a `FilterChain` with `DomainFilter` and `URLPatternFilter`.

```python
import asyncio
from crawl4ai.deep_crawling import FilterChain, DomainFilter, URLPatternFilter

async def create_filter_chain():
    # Filter 1: Allow only 'example.com'
    domain_filter = DomainFilter(allowed_domains=["example.com"])
    
    # Filter 2: Allow only URLs ending with '.html' or '.htm'
    pattern_filter = URLPatternFilter(patterns=["*.html", "*.htm"])
    
    # Create a chain: URL must pass BOTH filters
    filter_chain = FilterChain(filters=[domain_filter, pattern_filter])
    
    print(f"FilterChain created with {len(filter_chain.filters)} filters.")

    url1 = "http://example.com/page.html" # Should pass
    url2 = "http://example.com/script.js" # Should fail pattern_filter
    url3 = "http://otherexample.com/page.html" # Should fail domain_filter
    url4 = "http://otherexample.com/image.png" # Should fail both

    print(f"\nTesting URL: {url1} -> Passed: {await filter_chain.apply(url1)}")
    print(f"Testing URL: {url2} -> Passed: {await filter_chain.apply(url2)}")
    print(f"Testing URL: {url3} -> Passed: {await filter_chain.apply(url3)}")
    print(f"Testing URL: {url4} -> Passed: {await filter_chain.apply(url4)}")

    assert await filter_chain.apply(url1) == True
    assert await filter_chain.apply(url2) == False
    assert await filter_chain.apply(url3) == False
    assert await filter_chain.apply(url4) == False
    
    print("\nDomainFilter stats:", domain_filter.stats.passed_urls, "passed,", domain_filter.stats.rejected_urls, "rejected.")
    print("PatternFilter stats:", pattern_filter.stats.passed_urls, "passed,", pattern_filter.stats.rejected_urls, "rejected.")
    print("FilterChain aggregated stats:", filter_chain.stats.passed_urls, "passed,", filter_chain.stats.rejected_urls, "rejected.")


asyncio.run(create_filter_chain())
```

#### 2.2.2. Example: Applying a `FilterChain` within a `BFSDeeepCrawlStrategy` and observing filtered results.
(This was effectively covered in 1.3.3.1. That example shows a `FilterChain` used with `BFSDeeepCrawlStrategy`.)

#### 2.2.3. Example: Checking aggregated `FilterStats` from a `FilterChain`.
(This was effectively covered in 2.2.1, where `filter_chain.stats` are printed.)

### 2.3. `URLPatternFilter`

#### 2.3.1. Example: Using `URLPatternFilter` to allow only URLs matching a specific regex pattern.

```python
import asyncio
from crawl4ai.deep_crawling import URLPatternFilter

async def url_pattern_regex():
    # Allow URLs that look like product pages, e.g., /products/item123
    regex_pattern = r"/products/item\d+"
    product_filter = URLPatternFilter(patterns=[regex_pattern]) # use_glob=False is default for regex

    url_product = "http://example.com/products/item123"
    url_blog = "http://example.com/blog/my-post"

    print(f"Testing with regex pattern: {regex_pattern}")
    print(f"URL: {url_product}, Passed: {await product_filter.apply(url_product)}")
    print(f"URL: {url_blog}, Passed: {await product_filter.apply(url_blog)}")

    assert await product_filter.apply(url_product) == True
    assert await product_filter.apply(url_blog) == False

asyncio.run(url_pattern_regex())
```

#### 2.3.2. Example: Using `URLPatternFilter` with `reverse=True` to disallow URLs matching a pattern.

```python
import asyncio
from crawl4ai.deep_crawling import URLPatternFilter

async def url_pattern_reverse():
    # Disallow URLs containing 'admin' or 'login'
    disallow_patterns = [r".*admin.*", r".*login.*"]
    admin_block_filter = URLPatternFilter(patterns=disallow_patterns, reverse=True)

    url_safe = "http://example.com/dashboard"
    url_admin = "http://example.com/admin/panel"
    url_login = "http://example.com/user/login/page"

    print(f"Testing with reverse patterns: {disallow_patterns}")
    print(f"URL: {url_safe}, Passed: {await admin_block_filter.apply(url_safe)}")
    print(f"URL: {url_admin}, Passed: {await admin_block_filter.apply(url_admin)}")
    print(f"URL: {url_login}, Passed: {await admin_block_filter.apply(url_login)}")

    assert await admin_block_filter.apply(url_safe) == True
    assert await admin_block_filter.apply(url_admin) == False
    assert await admin_block_filter.apply(url_login) == False

asyncio.run(url_pattern_reverse())
```

#### 2.3.3. Example: `URLPatternFilter` with `use_glob=True` for wildcard matching.

```python
import asyncio
from crawl4ai.deep_crawling import URLPatternFilter

async def url_pattern_glob():
    # Allow only .jpg or .png images in an /assets/ directory using glob
    # use_glob=True is effectively default when patterns don't look like regex
    # but we can be explicit. The categorization logic determines this.
    # Forcing glob by not using regex-like characters.
    # This filter's internal logic auto-detects glob for simple patterns like "*.jpg"
    # If you want to force fnmatch style globbing over regex for ambiguous patterns,
    # there isn't a direct `use_glob` parameter on URLPatternFilter itself.
    # The categorization of pattern types (SUFFIX, PREFIX, DOMAIN, PATH, REGEX)
    # handles this. Let's demonstrate a simple suffix pattern.
    
    # Example: Allow only *.jpg or *.png
    image_filter_suffix = URLPatternFilter(patterns=["*.jpg", "*.png"]) # This will be categorized as SUFFIX

    url_jpg = "http://example.com/image.jpg"
    url_png = "http://example.com/photo.png"
    url_gif = "http://example.com/animation.gif"

    print("Testing with SUFFIX patterns: ['*.jpg', '*.png']")
    print(f"URL: {url_jpg}, Passed: {await image_filter_suffix.apply(url_jpg)}")
    print(f"URL: {url_png}, Passed: {await image_filter_suffix.apply(url_png)}")
    print(f"URL: {url_gif}, Passed: {await image_filter_suffix.apply(url_gif)}")

    assert await image_filter_suffix.apply(url_jpg) == True
    assert await image_filter_suffix.apply(url_png) == True
    assert await image_filter_suffix.apply(url_gif) == False

asyncio.run(url_pattern_glob())
```
*Self-correction: The `use_glob` parameter was mentioned in the prompt for `URLPatternFilter`, but it's not a direct constructor parameter. The filter categorizes patterns and applies fnmatch-like logic for SUFFIX, PREFIX, etc. The above example demonstrates this behavior for SUFFIX.*

#### 2.3.4. Example: `URLPatternFilter` demonstrating "SUFFIX" pattern type (e.g., `*.html`).
(Covered by 2.3.3 with `*.jpg`, `*.png`. A specific `*.html` example is similar)

```python
import asyncio
from crawl4ai.deep_crawling import URLPatternFilter

async def url_pattern_suffix_html():
    html_filter = URLPatternFilter(patterns=["*.html"]) # Categorized as SUFFIX

    url_html = "http://example.com/index.html"
    url_php = "http://example.com/index.php"
    
    print("Testing SUFFIX pattern: '*.html'")
    print(f"URL: {url_html}, Passed: {await html_filter.apply(url_html)}")
    print(f"URL: {url_php}, Passed: {await html_filter.apply(url_php)}")

    assert await html_filter.apply(url_html) == True
    assert await html_filter.apply(url_php) == False

asyncio.run(url_pattern_suffix_html())
```

#### 2.3.5. Example: `URLPatternFilter` demonstrating "PREFIX" pattern type (e.g., `/blog/*`).

```python
import asyncio
from crawl4ai.deep_crawling import URLPatternFilter

async def url_pattern_prefix_blog():
    # Note: For `URLPatternFilter`, a pattern like "/blog/*" would be treated as a REGEX
    # or a general PATH if it doesn't have special regex characters.
    # The internal categorization distinguishes between simple wildcards and full regex.
    # Let's use a pattern that is clearly a prefix and would be handled by fnmatch-like logic.
    # The `_categorize_pattern` method would likely treat "/blog/*" as PATH or REGEX.
    # To demonstrate a pure prefix, we'd use a simpler pattern without the trailing `*` if it's not a glob pattern.
    # If "/blog/*" is intended as a glob, it's treated as such for PATH.
    
    # Let's use a pattern that clearly falls into PREFIX category: "http://example.com/blog/"
    # And another that would be a PATH type: "/blog/*"
    
    # This will be categorized as PATH due to the wildcard if not complex enough for REGEX
    blog_path_filter = URLPatternFilter(patterns=["*/blog/*"]) 

    url_blog_post = "http://example.com/blog/my-first-post"
    url_blog_main = "http://example.com/blog/"
    url_products = "http://example.com/products/item"

    print("Testing PATH pattern: '*/blog/*'") # Will match URLs containing /blog/
    print(f"URL: {url_blog_post}, Passed: {await blog_path_filter.apply(url_blog_post)}")
    print(f"URL: {url_blog_main}, Passed: {await blog_path_filter.apply(url_blog_main)}")
    print(f"URL: {url_products}, Passed: {await blog_path_filter.apply(url_products)}")

    assert await blog_path_filter.apply(url_blog_post) == True
    assert await blog_path_filter.apply(url_blog_main) == True
    assert await blog_path_filter.apply(url_products) == False
    
    # To strictly test _simple_prefixes (checked before general path patterns):
    # This uses exact string startswith logic.
    simple_prefix_filter = URLPatternFilter(patterns=["http://example.com/blog"]) 
    # This will not match /blog/ as a prefix, but as a PATH pattern if it makes it there.
    # The internal categorization logic is: SUFFIX -> DOMAIN -> PREFIX -> PATH/REGEX
    # So, "http://example.com/blog" would be a simple prefix.

    print("\nTesting simple prefix pattern: 'http://example.com/blog'")
    print(f"URL: {url_blog_post}, Passed: {await simple_prefix_filter.apply(url_blog_post)}") # True
    print(f"URL: http://example.com/blog, Passed: {await simple_prefix_filter.apply('http://example.com/blog')}") # True
    print(f"URL: {url_products}, Passed: {await simple_prefix_filter.apply(url_products)}") # False
    
    assert await simple_prefix_filter.apply(url_blog_post) == True


asyncio.run(url_pattern_prefix_blog())
```

#### 2.3.6. Example: `URLPatternFilter` demonstrating "DOMAIN" pattern type (e.g., `*.example.com`).

```python
import asyncio
from crawl4ai.deep_crawling import URLPatternFilter

async def url_pattern_domain():
    # This pattern type matches the domain part of the URL.
    # "*.example.com" would allow "www.example.com", "blog.example.com", but not "example.com" itself
    # or "badexample.com".
    # The internal logic converts "*.example.com" into a regex like r"[^/]+\.example\.com" for domain matching.
    
    domain_filter = URLPatternFilter(patterns=["*.example.com"]) 

    url_subdomain = "http://blog.example.com/article"
    url_maindomain = "http://example.com/main" # This should NOT pass if pattern is strictly *.example.com
    url_other_sub = "http://www.example.com/page"
    url_external = "http://another.domain.com"
    
    # If we want to include example.com itself, we'd need another pattern "example.com" or a regex.
    # Let's test with "example.com" to show it's treated as a domain pattern
    main_domain_filter = URLPatternFilter(patterns=["example.com"])


    print("Testing DOMAIN pattern: '*.example.com'")
    print(f"URL: {url_subdomain}, Passed: {await domain_filter.apply(url_subdomain)}")
    print(f"URL: {url_maindomain}, Passed: {await domain_filter.apply(url_maindomain)}") # Expected False
    print(f"URL: {url_other_sub}, Passed: {await domain_filter.apply(url_other_sub)}")
    print(f"URL: {url_external}, Passed: {await domain_filter.apply(url_external)}")
    
    assert await domain_filter.apply(url_subdomain) == True
    assert await domain_filter.apply(url_maindomain) == False # `*.example.com` does not match `example.com`
    assert await domain_filter.apply(url_other_sub) == True
    assert await domain_filter.apply(url_external) == False

    print("\nTesting DOMAIN pattern: 'example.com'")
    print(f"URL: {url_subdomain}, Passed: {await main_domain_filter.apply(url_subdomain)}") # True (subdomain of example.com)
    print(f"URL: {url_maindomain}, Passed: {await main_domain_filter.apply(url_maindomain)}") # True
    
    assert await main_domain_filter.apply(url_subdomain) == True
    assert await main_domain_filter.apply(url_maindomain) == True


asyncio.run(url_pattern_domain())
```

#### 2.3.7. Example: `URLPatternFilter` demonstrating "PATH" pattern type (e.g., `/products/electronics/*`).
(Covered by 2.3.5 with `*/blog/*`. The categorization logic handles these general path/glob-like patterns after specific prefix/suffix/domain.)

### 2.4. `ContentTypeFilter`

*Note: `ContentTypeFilter` examples ideally require a live server or a mock HTTP server to return actual `Content-Type` headers. For self-contained examples, we'll primarily rely on the extension-based fallback.*

#### 2.4.1. Example: Using `ContentTypeFilter` to allow only "text/html" URLs.

```python
import asyncio
from crawl4ai.deep_crawling import ContentTypeFilter

async def content_type_html_only():
    # This filter will primarily use URL extensions if check_extension=True (default)
    # as we are not making live HTTP requests in this isolated example.
    html_only_filter = ContentTypeFilter(allowed_types=["text/html"])

    url_html = "http://example.com/index.html"
    url_pdf = "http://example.com/document.pdf"
    url_no_ext = "http://example.com/api/data" # No extension, would rely on Content-Type header in live scenario

    print("Testing ContentTypeFilter (allow 'text/html', relies on extension here):")
    print(f"URL: {url_html}, Passed: {await html_only_filter.apply(url_html)}")
    print(f"URL: {url_pdf}, Passed: {await html_only_filter.apply(url_pdf)}")
    print(f"URL: {url_no_ext}, Passed: {await html_only_filter.apply(url_no_ext)}")
    print("Note: For URLs without extensions, this filter would need live HTTP HEAD requests to check Content-Type header.")

    assert await html_only_filter.apply(url_html) == True
    assert await html_only_filter.apply(url_pdf) == False
    # Without live request, url_no_ext might pass if default behavior is permissive or fail if strict.
    # The current implementation's apply method is synchronous and relies on _check_url_cached.
    # _check_url_cached primarily uses extension. If check_extension=False, it would always return True
    # unless a live check was made (which is not part of the filter's apply method directly).
    # For this test, it defaults to True if no extension and check_extension=True
    assert await html_only_filter.apply(url_no_ext) == True 


asyncio.run(content_type_html_only())
```

#### 2.4.2. Example: `ContentTypeFilter` allowing a list of types, e.g., ["text/html", "application/pdf"].

```python
import asyncio
from crawl4ai.deep_crawling import ContentTypeFilter

async def content_type_html_and_pdf():
    multi_type_filter = ContentTypeFilter(allowed_types=["text/html", "application/pdf"])

    url_html = "http://example.com/index.html"
    url_pdf = "http://example.com/report.pdf"
    url_jpg = "http://example.com/image.jpg"

    print("Testing ContentTypeFilter (allow 'text/html', 'application/pdf'):")
    print(f"URL: {url_html}, Passed: {await multi_type_filter.apply(url_html)}")
    print(f"URL: {url_pdf}, Passed: {await multi_type_filter.apply(url_pdf)}")
    print(f"URL: {url_jpg}, Passed: {await multi_type_filter.apply(url_jpg)}")
    
    assert await multi_type_filter.apply(url_html) == True
    assert await multi_type_filter.apply(url_pdf) == True
    assert await multi_type_filter.apply(url_jpg) == False

asyncio.run(content_type_html_and_pdf())
```

#### 2.4.3. Example: `ContentTypeFilter` with `check_extension=True` (default) vs. `check_extension=False` using URL extensions.

```python
import asyncio
from crawl4ai.deep_crawling import ContentTypeFilter

async def content_type_check_extension_toggle():
    url_html_like_no_ext = "http://example.com/about-us" # Could be HTML
    url_pdf_like_no_ext = "http://example.com/download/report" # Could be PDF

    # Default: check_extension=True
    filter_check_ext = ContentTypeFilter(allowed_types=["text/html"])
    # If no extension, it defaults to True (allows processing, hoping Content-Type header confirms)
    print(f"With check_extension=True (default):")
    print(f"  URL: {url_html_like_no_ext}, Passed: {await filter_check_ext.apply(url_html_like_no_ext)}")
    assert await filter_check_ext.apply(url_html_like_no_ext) == True

    # check_extension=False: Ignores extensions, always passes unless live HEAD request fails (not tested here)
    filter_no_check_ext = ContentTypeFilter(allowed_types=["text/html"], check_extension=False)
    # This will always return True from apply() because it skips extension check
    print(f"With check_extension=False:")
    print(f"  URL: {url_html_like_no_ext}, Passed: {await filter_no_check_ext.apply(url_html_like_no_ext)}")
    print(f"  URL: http://example.com/image.jpg, Passed: {await filter_no_check_ext.apply('http://example.com/image.jpg')}")
    
    assert await filter_no_check_ext.apply(url_html_like_no_ext) == True
    assert await filter_no_check_ext.apply("http://example.com/image.jpg") == True 
    # (Passes because it doesn't check extension; live HEAD would be needed to actually filter)

asyncio.run(content_type_check_extension_toggle())
```

### 2.5. `DomainFilter`

#### 2.5.1. Example: `DomainFilter` allowing only URLs from "example.com" and its subdomains.

```python
import asyncio
from crawl4ai.deep_crawling import DomainFilter

async def domain_filter_allow_specific():
    # Allows example.com and any subdomains like www.example.com, blog.example.com
    domain_filter = DomainFilter(allowed_domains=["example.com"])

    url_main = "http://example.com/page"
    url_sub = "http://blog.example.com/article"
    url_external = "http://anotherdomain.com"

    print("Testing DomainFilter (allow 'example.com' and subdomains):")
    print(f"URL: {url_main}, Passed: {await domain_filter.apply(url_main)}")
    print(f"URL: {url_sub}, Passed: {await domain_filter.apply(url_sub)}")
    print(f"URL: {url_external}, Passed: {await domain_filter.apply(url_external)}")

    assert await domain_filter.apply(url_main) == True
    assert await domain_filter.apply(url_sub) == True
    assert await domain_filter.apply(url_external) == False

asyncio.run(domain_filter_allow_specific())
```

#### 2.5.2. Example: `DomainFilter` blocking URLs from "ads.example.com".

```python
import asyncio
from crawl4ai.deep_crawling import DomainFilter

async def domain_filter_block_specific():
    # Blocks ads.example.com and its subdomains (e.g., tracker.ads.example.com)
    # but allows other example.com URLs if no allowed_domains is set (or if it includes example.com)
    domain_filter = DomainFilter(blocked_domains=["ads.example.com"])
    # By default, if allowed_domains is None, all non-blocked domains are permitted.

    url_allowed_sub = "http://blog.example.com/article"
    url_blocked_sub = "http://ads.example.com/banner"
    url_deep_blocked = "http://tracker.ads.example.com/pixel" # Also blocked as subdomain of ads.example.com
    url_main = "http://example.com/main"

    print("Testing DomainFilter (block 'ads.example.com'):")
    print(f"URL: {url_allowed_sub}, Passed: {await domain_filter.apply(url_allowed_sub)}")
    print(f"URL: {url_blocked_sub}, Passed: {await domain_filter.apply(url_blocked_sub)}")
    print(f"URL: {url_deep_blocked}, Passed: {await domain_filter.apply(url_deep_blocked)}")
    print(f"URL: {url_main}, Passed: {await domain_filter.apply(url_main)}")

    assert await domain_filter.apply(url_allowed_sub) == True
    assert await domain_filter.apply(url_blocked_sub) == False
    assert await domain_filter.apply(url_deep_blocked) == False
    assert await domain_filter.apply(url_main) == True

asyncio.run(domain_filter_block_specific())
```

#### 2.5.3. Example: Combining `allowed_domains` and `blocked_domains`.

```python
import asyncio
from crawl4ai.deep_crawling import DomainFilter

async def domain_filter_combined():
    # Allow example.com but specifically block sub.example.com
    domain_filter = DomainFilter(
        allowed_domains=["example.com"],
        blocked_domains=["sub.example.com"]
    )

    url_main_allowed = "http://www.example.com/page" # Subdomain of example.com, allowed
    url_blocked_sub = "http://sub.example.com/secret" # Specifically blocked
    url_other_sub_allowed = "http://blog.example.com/article" # Allowed as subdomain of example.com
    url_external = "http://another.com" # Not in allowed_domains

    print("Testing DomainFilter (allow 'example.com', block 'sub.example.com'):")
    print(f"URL: {url_main_allowed}, Passed: {await domain_filter.apply(url_main_allowed)}")
    print(f"URL: {url_blocked_sub}, Passed: {await domain_filter.apply(url_blocked_sub)}")
    print(f"URL: {url_other_sub_allowed}, Passed: {await domain_filter.apply(url_other_sub_allowed)}")
    print(f"URL: {url_external}, Passed: {await domain_filter.apply(url_external)}")

    assert await domain_filter.apply(url_main_allowed) == True
    assert await domain_filter.apply(url_blocked_sub) == False
    assert await domain_filter.apply(url_other_sub_allowed) == True
    assert await domain_filter.apply(url_external) == False

asyncio.run(domain_filter_combined())
```

### 2.6. `ContentRelevanceFilter`
*Note: Requires live HTTP requests to fetch `<head>` content. For isolated tests, mocking or a stable example site is needed. We'll use a simplified direct call for demonstration.*

#### 2.6.1. Example: Using `ContentRelevanceFilter` with a query and threshold to filter pages based on head content relevance.

```python
import asyncio
from crawl4ai.deep_crawling import ContentRelevanceFilter
# Mock HeadPeek for testing without live requests
from unittest.mock import patch

# This example will mock HeadPeek.peek_html to simulate responses
async def demo_content_relevance_filter():
    query = "Python programming tutorial"
    # Threshold: Score must be >= 0.1 to pass
    relevance_filter = ContentRelevanceFilter(query=query, threshold=0.1) 

    # Mock HTML heads
    html_head_relevant = """
    <head>
        <title>Advanced Python Programming Tutorial</title>
        <meta name="description" content="Learn Python programming concepts and best practices.">
        <meta name="keywords" content="Python, programming, tutorial, advanced">
    </head>
    """
    html_head_irrelevant = """
    <head>
        <title>Best Coffee Recipes</title>
        <meta name="description" content="Discover amazing coffee recipes.">
        <meta name="keywords" content="coffee, recipes, morning, brew">
    </head>
    """

    url_relevant = "http://example.com/python-tutorial"
    url_irrelevant = "http://example.com/coffee-recipes"

    print(f"Testing ContentRelevanceFilter with query: '{query}' and threshold: 0.1")

    # Patch HeadPeek.peek_html to return our mock heads
    with patch('crawl4ai.deep_crawling.filters.HeadPeek.peek_html') as mock_peek:
        # First call to apply (for url_relevant)
        mock_peek.return_value = html_head_relevant
        passed_relevant = await relevance_filter.apply(url_relevant)
        print(f"  URL: {url_relevant}, Passed: {passed_relevant}, Score: {relevance_filter._last_score:.2f}") # _last_score is for demo
        assert passed_relevant

        # Second call to apply (for url_irrelevant)
        mock_peek.return_value = html_head_irrelevant
        passed_irrelevant = await relevance_filter.apply(url_irrelevant)
        print(f"  URL: {url_irrelevant}, Passed: {passed_irrelevant}, Score: {relevance_filter._last_score:.2f}")
        assert not passed_irrelevant

asyncio.run(demo_content_relevance_filter())
```

#### 2.6.2. Example: Demonstrating different `k1` and `b` BM25 parameters.

```python
import asyncio
from crawl4ai.deep_crawling import ContentRelevanceFilter
from unittest.mock import patch

async def demo_bm25_params_relevance_filter():
    query = "web scraping tools"
    
    html_head_content = """
    <head>
        <title>Top Web Scraping Tools and Libraries</title>
        <meta name="description" content="A comprehensive list of web scraping tools.">
    </head>
    """
    url_test = "http://example.com/scraping-tools"

    # Filter 1: Default k1 and b
    filter_default_params = ContentRelevanceFilter(query=query, threshold=0.01)
    
    # Filter 2: Higher k1 (more sensitive to term frequency)
    filter_high_k1 = ContentRelevanceFilter(query=query, threshold=0.01, k1=2.0)

    # Filter 3: Lower b (less penalty for document length)
    filter_low_b = ContentRelevanceFilter(query=query, threshold=0.01, b=0.5)

    with patch('crawl4ai.deep_crawling.filters.HeadPeek.peek_html', return_value=html_head_content):
        await filter_default_params.apply(url_test)
        score_default = filter_default_params._last_score # Internal for demo
        print(f"Score with default BM25 params (k1={filter_default_params.k1}, b={filter_default_params.b}): {score_default:.4f}")

        await filter_high_k1.apply(url_test)
        score_high_k1 = filter_high_k1._last_score
        print(f"Score with high k1 (k1={filter_high_k1.k1}, b={filter_high_k1.b}): {score_high_k1:.4f}")
        
        await filter_low_b.apply(url_test)
        score_low_b = filter_low_b._last_score
        print(f"Score with low b (k1={filter_low_b.k1}, b={filter_low_b.b}): {score_low_b:.4f}")

    # Exact score assertions can be brittle, but we expect scores to change.
    # For this specific content and query, higher k1 might slightly increase score if query terms are frequent.
    # Lower b might increase score if avgdl is small relative to this doc's length.
    assert score_default != score_high_k1 or score_default != score_low_b, "BM25 scores should differ with parameter changes."

asyncio.run(demo_bm25_params_relevance_filter())
```

### 2.7. `SEOFilter`

#### 2.7.1. Example: Using `SEOFilter` with a threshold to filter pages based on SEO quality score.

```python
import asyncio
from crawl4ai.deep_crawling import SEOFilter
from unittest.mock import patch

async def demo_seo_filter_threshold():
    # Example: Require a minimum SEO score of 0.7
    seo_filter = SEOFilter(threshold=0.7)

    html_head_good_seo = """
    <head>
        <title>Optimize Your SEO: A Comprehensive Guide (55 chars)</title>
        <meta name="description" content="Learn SEO best practices to improve your website ranking. This guide covers keywords, on-page optimization, and link building. (150 chars)">
        <link rel="canonical" href="http://example.com/seo-guide" />
        <meta name="robots" content="index, follow">
        <script type="application/ld+json">{"@context": "https://schema.org"}</script>
    </head>
    """
    url_good_seo = "http://example.com/seo-guide"

    html_head_poor_seo = "<head><title>Seo</title></head>" # Short title, no meta, etc.
    url_poor_seo = "http://example.com/bad-seo"
    
    print(f"Testing SEOFilter with threshold 0.7:")
    with patch('crawl4ai.deep_crawling.filters.HeadPeek.peek_html') as mock_peek:
        mock_peek.return_value = html_head_good_seo
        passed_good = await seo_filter.apply(url_good_seo)
        print(f"  URL (Good SEO): {url_good_seo}, Passed: {passed_good}, Score: {seo_filter._last_score:.2f}")
        assert passed_good

        mock_peek.return_value = html_head_poor_seo
        passed_poor = await seo_filter.apply(url_poor_seo)
        print(f"  URL (Poor SEO): {url_poor_seo}, Passed: {passed_poor}, Score: {seo_filter._last_score:.2f}")
        assert not passed_poor

asyncio.run(demo_seo_filter_threshold())
```

#### 2.7.2. Example: `SEOFilter` with custom `keywords` to check for keyword presence in title/meta.

```python
import asyncio
from crawl4ai.deep_crawling import SEOFilter
from unittest.mock import patch

async def demo_seo_filter_keywords():
    # Filter requires "Crawl4AI" in title/meta, and overall score >= 0.5
    seo_filter = SEOFilter(threshold=0.5, keywords=["Crawl4AI", "web scraping"])

    html_head_with_keyword = """
    <head>
        <title>Crawl4AI: The Best Web Scraping Tool</title>
        <meta name="description" content="Discover Crawl4AI for efficient web scraping.">
        <meta name="robots" content="index, follow"> 
    </head>
    """ # Missing canonical but has keywords
    url_with_keyword = "http://example.com/crawl4ai-tool"

    html_head_no_keyword = """
    <head>
        <title>A Generic Web Tool</title>
        <meta name="description" content="This is a tool for the web.">
        <meta name="robots" content="index, follow">
        <link rel="canonical" href="http://example.com/generic-tool" />
    </head>
    """ # Good general SEO but missing keywords
    url_no_keyword = "http://example.com/generic-tool"

    print(f"Testing SEOFilter with keywords ['Crawl4AI', 'web scraping'] and threshold 0.5:")
    with patch('crawl4ai.deep_crawling.filters.HeadPeek.peek_html') as mock_peek:
        mock_peek.return_value = html_head_with_keyword
        passed_with_kw = await seo_filter.apply(url_with_keyword)
        print(f"  URL (With Keyword): {url_with_keyword}, Passed: {passed_with_kw}, Score: {seo_filter._last_score:.2f}")
        assert passed_with_kw # Keyword presence significantly boosts score

        mock_peek.return_value = html_head_no_keyword
        passed_no_kw = await seo_filter.apply(url_no_keyword)
        print(f"  URL (No Keyword): {url_no_keyword}, Passed: {passed_no_kw}, Score: {seo_filter._last_score:.2f}")
        assert not passed_no_kw # Lack of keyword drops score below threshold

asyncio.run(demo_seo_filter_keywords())
```

#### 2.7.3. Example: `SEOFilter` with custom `weights` for different SEO factors.

```python
import asyncio
from crawl4ai.deep_crawling import SEOFilter
from unittest.mock import patch

async def demo_seo_filter_weights():
    # Emphasize title length and canonical tag more than others
    custom_weights = {
        "title_length": 0.3,  # Default 0.15
        "title_kw": 0.1,      # Default 0.18
        "meta_description": 0.1, # Default 0.12
        "canonical": 0.3,     # Default 0.10
        "robot_ok": 0.1,      # Default 0.20
        "schema_org": 0.05,   # Default 0.10
        "url_quality": 0.05   # Default 0.15
    } # Sum should ideally be 1.0 but filter normalizes internally if not.
    
    seo_filter = SEOFilter(threshold=0.6, weights=custom_weights)

    html_strong_title_canonical = """
    <head>
        <title>Perfect Title Length For Custom SEO Weights Test (50char)</title>
        <meta name="description" content="Short description."> 
        <link rel="canonical" href="http://example.com/custom-weights" />
        <meta name="robots" content="index, follow">
    </head>
    """
    url_strong_tc = "http://example.com/custom-weights"

    html_weak_title_canonical = """
    <head>
        <title>Tiny</title> 
        <meta name="description" content="Very very very long description that will be penalized for length if that factor has weight, but here title and canonical matter most.">
        <meta name="robots" content="index, follow">
    </head>
    """ # No canonical, bad title length
    url_weak_tc = "http://example.com/weak-title-canonical"

    print(f"Testing SEOFilter with custom weights (emphasizing title_length, canonical):")
    with patch('crawl4ai.deep_crawling.filters.HeadPeek.peek_html') as mock_peek:
        mock_peek.return_value = html_strong_title_canonical
        passed_strong = await seo_filter.apply(url_strong_tc)
        print(f"  URL (Strong T/C): {url_strong_tc}, Passed: {passed_strong}, Score: {seo_filter._last_score:.2f}")
        assert passed_strong

        mock_peek.return_value = html_weak_title_canonical
        passed_weak = await seo_filter.apply(url_weak_tc)
        print(f"  URL (Weak T/C): {url_weak_tc}, Passed: {passed_weak}, Score: {seo_filter._last_score:.2f}")
        assert not passed_weak

asyncio.run(demo_seo_filter_weights())
```

---
## 3. URL Scorers

This section showcases how to score URLs to guide priority-based crawling strategies like `BestFirstCrawlingStrategy`.

### 3.1. `ScoringStats`

#### 3.1.1. Example: Accessing `urls_scored`, `total_score`, `min_score`, and `max_score` from a `ScoringStats` object.

```python
import asyncio
from crawl4ai.deep_crawling import KeywordRelevanceScorer # Any scorer will do

async def demo_scoring_stats():
    scorer = KeywordRelevanceScorer(keywords=["apple", "banana"])

    urls = [
        "http://example.com/apple-pie",       # Score: 0.5 (1/2 keywords)
        "http://example.com/banana-bread",    # Score: 0.5
        "http://example.com/apple-and-banana",# Score: 1.0 (2/2 keywords)
        "http://example.com/orange-juice"     # Score: 0.0
    ]
    
    scores_achieved = []
    for url in urls:
        score = await scorer.score(url) # score() updates stats
        scores_achieved.append(score)

    stats = scorer.stats
    print(f"--- Scoring Stats for KeywordRelevanceScorer ---")
    print(f"URLs Scored: {stats.urls_scored}")
    print(f"Total Score Sum: {stats.total_score:.2f}") # Sum of (score * weight), weight is 1.0 here
    print(f"Min Score: {stats.min_score:.2f}")
    print(f"Max Score: {stats.max_score:.2f}")
    print(f"Average Score: {stats.average_score:.2f}")

    assert stats.urls_scored == 4
    assert abs(stats.total_score - (0.5 + 0.5 + 1.0 + 0.0)) < 0.01
    assert abs(stats.min_score - 0.0) < 0.01
    assert abs(stats.max_score - 1.0) < 0.01
    assert abs(stats.average_score - 2.0/4) < 0.01


asyncio.run(demo_scoring_stats())
```

### 3.2. `CompositeScorer`

#### 3.2.1. Example: Creating a `CompositeScorer` with `KeywordRelevanceScorer` and `PathDepthScorer`, assigning weights.

```python
import asyncio
from crawl4ai.deep_crawling import CompositeScorer, KeywordRelevanceScorer, PathDepthScorer

async def demo_composite_scorer():
    # Scorer 1: Keyword relevance (weight 0.7)
    keyword_scorer = KeywordRelevanceScorer(keywords=["guide"], weight=0.7)
    
    # Scorer 2: Path depth, optimal at 2 (weight 0.3)
    depth_scorer = PathDepthScorer(optimal_depth=2, weight=0.3)

    composite_scorer = CompositeScorer(scorers=[keyword_scorer, depth_scorer])

    url1 = "http://example.com/guides/main-guide.html" # Keyword match, depth 2
    # kw_score = 1.0 * 0.7 = 0.7
    # depth_score (optimal_depth=2, current_depth=2, diff=0) = 1.0 * 0.3 = 0.3
    # total = 0.7 + 0.3 = 1.0
    
    url2 = "http://example.com/blog/post" # No keyword, depth 2
    # kw_score = 0.0 * 0.7 = 0.0
    # depth_score (optimal_depth=2, current_depth=2, diff=0) = 1.0 * 0.3 = 0.3
    # total = 0.0 + 0.3 = 0.3

    url3 = "http://example.com/guides/intro" # Keyword match, depth 1
    # kw_score = 1.0 * 0.7 = 0.7
    # depth_score (optimal_depth=2, current_depth=1, diff=1) = 0.5 * 0.3 = 0.15
    # total = 0.7 + 0.15 = 0.85

    score1 = await composite_scorer.score(url1)
    score2 = await composite_scorer.score(url2)
    score3 = await composite_scorer.score(url3)

    print(f"URL: {url1}, Composite Score: {score1:.4f}")
    print(f"URL: {url2}, Composite Score: {score2:.4f}")
    print(f"URL: {url3}, Composite Score: {score3:.4f}")

    assert abs(score1 - 1.0) < 0.01
    assert abs(score2 - 0.3) < 0.01
    assert abs(score3 - 0.85) < 0.01
    
    # Check stats of individual scorers and composite
    print(f"\nComposite Scorer Stats: Avg={composite_scorer.stats.average_score:.2f}")
    print(f"  Keyword Scorer Stats: Avg={keyword_scorer.stats.average_score:.2f}")
    print(f"  Depth Scorer Stats: Avg={depth_scorer.stats.average_score:.2f}")


asyncio.run(demo_composite_scorer())
```

#### 3.2.2. Example: `CompositeScorer` with `normalize=True` to scale scores.

When `normalize=True`, the final score is divided by the number of scorers if there are scorers, ensuring it stays roughly in the 0-1 range if individual scorers are also in that range.

```python
import asyncio
from crawl4ai.deep_crawling import CompositeScorer, KeywordRelevanceScorer, PathDepthScorer

async def demo_composite_scorer_normalized():
    keyword_scorer = KeywordRelevanceScorer(keywords=["guide"], weight=1.0) # Unweighted for clarity
    depth_scorer = PathDepthScorer(optimal_depth=2, weight=1.0)       # Unweighted for clarity

    # With normalize=True, final score will be (kw_score + depth_score) / 2
    composite_scorer_norm = CompositeScorer(
        scorers=[keyword_scorer, depth_scorer], 
        normalize=True
    )

    url1 = "http://example.com/guides/main-guide.html" # Keyword match, depth 2
    # kw_score = 1.0
    # depth_score = 1.0
    # total_raw = 2.0; normalized = 2.0 / 2 = 1.0
    
    url2 = "http://example.com/blog/post" # No keyword, depth 2
    # kw_score = 0.0
    # depth_score = 1.0
    # total_raw = 1.0; normalized = 1.0 / 2 = 0.5

    score1_norm = await composite_scorer_norm.score(url1)
    score2_norm = await composite_scorer_norm.score(url2)

    print(f"URL: {url1}, Normalized Composite Score: {score1_norm:.4f}")
    print(f"URL: {url2}, Normalized Composite Score: {score2_norm:.4f}")
    
    assert abs(score1_norm - 1.0) < 0.01
    assert abs(score2_norm - 0.5) < 0.01

asyncio.run(demo_composite_scorer_normalized())
```

### 3.3. `KeywordRelevanceScorer`

#### 3.3.1. Example: Scoring URLs based on the presence of specific keywords.

```python
import asyncio
from crawl4ai.deep_crawling import KeywordRelevanceScorer

async def demo_keyword_relevance_scorer():
    scorer = KeywordRelevanceScorer(keywords=["apple", "banana", "cherry"])

    url1 = "http://example.com/apple-pie-recipe" # 1 keyword
    url2 = "http://example.com/banana-and-cherry-smoothie" # 2 keywords
    url3 = "http://example.com/orange-juice" # 0 keywords
    url4 = "http://example.com/apple-banana-cherry-fruit-salad" # 3 keywords

    score1 = await scorer.score(url1)
    score2 = await scorer.score(url2)
    score3 = await scorer.score(url3)
    score4 = await scorer.score(url4)

    print(f"URL: {url1}, Score: {score1:.2f} (Expected: ~0.33)")
    print(f"URL: {url2}, Score: {score2:.2f} (Expected: ~0.67)")
    print(f"URL: {url3}, Score: {score3:.2f} (Expected: 0.00)")
    print(f"URL: {url4}, Score: {score4:.2f} (Expected: 1.00)")
    
    assert abs(score1 - 1/3) < 0.01
    assert abs(score2 - 2/3) < 0.01
    assert abs(score3 - 0.0) < 0.01
    assert abs(score4 - 1.0) < 0.01

asyncio.run(demo_keyword_relevance_scorer())
```

#### 3.3.2. Example: `KeywordRelevanceScorer` with `case_sensitive=True`.

```python
import asyncio
from crawl4ai.deep_crawling import KeywordRelevanceScorer

async def demo_keyword_relevance_case_sensitive():
    # Case-sensitive matching
    scorer_cs = KeywordRelevanceScorer(keywords=["Apple"], case_sensitive=True)
    # Default: case-insensitive
    scorer_ci = KeywordRelevanceScorer(keywords=["Apple"])


    url_exact_match = "http://example.com/Apple-iPhone"
    url_lowercase_match = "http://example.com/apple-ipad"
    url_no_match = "http://example.com/orange-device"

    print("--- Case-Sensitive Scorer (keyword: 'Apple') ---")
    print(f"URL: {url_exact_match}, Score: {await scorer_cs.score(url_exact_match):.2f}")
    print(f"URL: {url_lowercase_match}, Score: {await scorer_cs.score(url_lowercase_match):.2f}")
    print(f"URL: {url_no_match}, Score: {await scorer_cs.score(url_no_match):.2f}")

    assert abs(await scorer_cs.score(url_exact_match) - 1.0) < 0.01
    assert abs(await scorer_cs.score(url_lowercase_match) - 0.0) < 0.01
    assert abs(await scorer_cs.score(url_no_match) - 0.0) < 0.01

    print("\n--- Case-Insensitive Scorer (keyword: 'Apple') ---")
    print(f"URL: {url_exact_match}, Score: {await scorer_ci.score(url_exact_match):.2f}")
    print(f"URL: {url_lowercase_match}, Score: {await scorer_ci.score(url_lowercase_match):.2f}")
    
    assert abs(await scorer_ci.score(url_exact_match) - 1.0) < 0.01
    assert abs(await scorer_ci.score(url_lowercase_match) - 1.0) < 0.01

asyncio.run(demo_keyword_relevance_case_sensitive())
```

### 3.4. `PathDepthScorer`

#### 3.4.1. Example: `PathDepthScorer` with an `optimal_depth` of 2.

```python
import asyncio
from crawl4ai.deep_crawling import PathDepthScorer

async def demo_path_depth_scorer_optimal_2():
    scorer = PathDepthScorer(optimal_depth=2)

    url_depth0 = "http://example.com"                  # diff = 2, score ~0.33
    url_depth1 = "http://example.com/category"         # diff = 1, score 0.5
    url_depth2 = "http://example.com/category/product" # diff = 0, score 1.0
    url_depth3 = "http://example.com/cat/prod/details" # diff = 1, score 0.5
    url_depth4 = "http://example.com/cat/prod/det/rev" # diff = 2, score ~0.33

    print(f"PathDepthScorer with optimal_depth=2:")
    print(f"URL: {url_depth0} (depth 0), Score: {await scorer.score(url_depth0):.3f}")
    print(f"URL: {url_depth1} (depth 1), Score: {await scorer.score(url_depth1):.3f}")
    print(f"URL: {url_depth2} (depth 2), Score: {await scorer.score(url_depth2):.3f}")
    print(f"URL: {url_depth3} (depth 3), Score: {await scorer.score(url_depth3):.3f}")
    print(f"URL: {url_depth4} (depth 4), Score: {await scorer.score(url_depth4):.3f}")
    
    assert abs(await scorer.score(url_depth2) - 1.0) < 0.01
    assert abs(await scorer.score(url_depth1) - 0.5) < 0.01
    assert abs(await scorer.score(url_depth3) - 0.5) < 0.01

asyncio.run(demo_path_depth_scorer_optimal_2())
```

#### 3.4.2. Example: Demonstrating how scores decrease as path depth deviates from `optimal_depth`.
(This is covered by 3.4.1.)

### 3.5. `ContentTypeScorer`

#### 3.5.1. Example: `ContentTypeScorer` prioritizing ".html" and ".pdf" URLs over others based on `type_weights`.
*Note: This scorer relies on URL extensions primarily, as live HEAD requests are not part of its `score` method.*

```python
import asyncio
from crawl4ai.deep_crawling import ContentTypeScorer

async def demo_content_type_scorer():
    type_weights = {
        ".html": 1.0,
        ".pdf": 0.8,
        ".jpg": 0.2,
        # Other types get default 0.1 (not explicitly shown here)
    }
    scorer = ContentTypeScorer(type_weights=type_weights)

    url_html = "http://example.com/index.html"
    url_pdf = "http://example.com/document.pdf"
    url_jpg = "http://example.com/image.jpg"
    url_txt = "http://example.com/notes.txt" # Not in weights, gets default 0.1

    print(f"ContentTypeScorer with weights: {type_weights}")
    print(f"URL: {url_html}, Score: {await scorer.score(url_html):.2f}")
    print(f"URL: {url_pdf}, Score: {await scorer.score(url_pdf):.2f}")
    print(f"URL: {url_jpg}, Score: {await scorer.score(url_jpg):.2f}")
    print(f"URL: {url_txt}, Score: {await scorer.score(url_txt):.2f}")
    
    assert abs(await scorer.score(url_html) - 1.0) < 0.01
    assert abs(await scorer.score(url_pdf) - 0.8) < 0.01
    assert abs(await scorer.score(url_jpg) - 0.2) < 0.01
    assert abs(await scorer.score(url_txt) - 0.1) < 0.01 # Default for unlisted

asyncio.run(demo_content_type_scorer())
```

### 3.6. `FreshnessScorer`

#### 3.6.1. Example: `FreshnessScorer` scoring URLs with recent years higher.

```python
import asyncio
from datetime import datetime
from crawl4ai.deep_crawling import FreshnessScorer

async def demo_freshness_scorer():
    current_year = datetime.now().year
    scorer = FreshnessScorer(current_year=current_year)

    url_current_year = f"http://example.com/news/{current_year}/article"
    url_last_year = f"http://example.com/archive/{current_year - 1}/report"
    url_five_years_ago = f"http://example.com/blog/{current_year - 5}/post"
    url_ten_years_ago = f"http://example.com/old/{current_year - 10}/story"
    url_no_year = "http://example.com/static-page"

    print(f"FreshnessScorer (current year: {current_year}):")
    score_current = await scorer.score(url_current_year)
    score_last = await scorer.score(url_last_year)
    score_five_ago = await scorer.score(url_five_years_ago)
    score_ten_ago = await scorer.score(url_ten_years_ago)
    score_no_year = await scorer.score(url_no_year)
    
    print(f"URL: {url_current_year}, Score: {score_current:.2f} (Expected: 1.0)")
    print(f"URL: {url_last_year}, Score: {score_last:.2f} (Expected: 0.9)")
    print(f"URL: {url_five_years_ago}, Score: {score_five_ago:.2f} (Expected: 0.5)")
    print(f"URL: {url_ten_years_ago}, Score: {score_ten_ago:.2f} (Expected: ~0.1)") # 1.0 - 10 * 0.1 = 0, capped at 0.1
    print(f"URL: {url_no_year}, Score: {score_no_year:.2f} (Expected: 0.5 - default)")

    assert abs(score_current - 1.0) < 0.01
    assert abs(score_last - 0.9) < 0.01
    assert abs(score_five_ago - 0.5) < 0.01
    assert abs(score_ten_ago - 0.1) < 0.01 # Max(0.1, 1.0 - 10*0.1)
    assert abs(score_no_year - 0.5) < 0.01


asyncio.run(demo_freshness_scorer())
```

#### 3.6.2. Example: Demonstrating `FreshnessScorer` with a custom `current_year`.

```python
import asyncio
from crawl4ai.deep_crawling import FreshnessScorer

async def demo_freshness_scorer_custom_year():
    # Pretend it's 2030 for scoring purposes
    custom_current_year = 2030
    scorer = FreshnessScorer(current_year=custom_current_year)

    url_actually_2024 = "http://example.com/event/2024/details" # 6 years old relative to 2030
    # Expected score: max(0.1, 1.0 - 6 * 0.1) = max(0.1, 0.4) = 0.4
    # If using lookup: index 6 is out of bounds, so fallback calculation.
    # _FRESHNESS_SCORES has 6 elements (index 0-5). Year diff 6 is 1.0 - 6*0.1 = 0.4

    score_2024 = await scorer.score(url_actually_2024)
    print(f"FreshnessScorer (custom current year: {custom_current_year}):")
    print(f"URL: {url_actually_2024}, Score: {score_2024:.2f}")
    
    assert abs(score_2024 - 0.4) < 0.01

asyncio.run(demo_freshness_scorer_custom_year())
```

### 3.7. `DomainAuthorityScorer`

#### 3.7.1. Example: `DomainAuthorityScorer` with a custom `domain_weights` dictionary.

```python
import asyncio
from crawl4ai.deep_crawling import DomainAuthorityScorer

async def demo_domain_authority_custom_weights():
    domain_weights = {
        "wikipedia.org": 0.9,
        "github.com": 0.8,
        "example.com": 0.5  # Default is 0.5, but explicitly setting
    }
    scorer = DomainAuthorityScorer(domain_weights=domain_weights)

    url_wiki = "https://en.wikipedia.org/wiki/Web_scraping"
    url_github = "https://github.com/crawl4ai/crawl4ai"
    url_example = "http://www.example.com/somepage" # Subdomain is fine
    url_unknown = "http://unknownsite.net/path"

    print(f"DomainAuthorityScorer with custom weights:")
    print(f"URL: {url_wiki}, Score: {await scorer.score(url_wiki):.2f}")
    print(f"URL: {url_github}, Score: {await scorer.score(url_github):.2f}")
    print(f"URL: {url_example}, Score: {await scorer.score(url_example):.2f}")
    print(f"URL: {url_unknown}, Score: {await scorer.score(url_unknown):.2f} (default weight)")

    assert abs(await scorer.score(url_wiki) - 0.9) < 0.01
    assert abs(await scorer.score(url_github) - 0.8) < 0.01
    assert abs(await scorer.score(url_example) - 0.5) < 0.01
    assert abs(await scorer.score(url_unknown) - scorer.default_weight) < 0.01 # default_weight is 0.5

asyncio.run(demo_domain_authority_custom_weights())
```

#### 3.7.2. Example: `DomainAuthorityScorer` showing the effect of `default_weight`.

```python
import asyncio
from crawl4ai.deep_crawling import DomainAuthorityScorer

async def demo_domain_authority_default_weight():
    # No custom weights, so all domains get default_weight unless they are in the pre-cached top domains
    # Default_weight defaults to 0.5
    scorer_default = DomainAuthorityScorer() 
    
    # Custom default weight
    scorer_custom_default = DomainAuthorityScorer(default_weight=0.3)

    url_random1 = "http://random-new-site.xyz/page"
    url_random2 = "http://another-unknown-domain.io/blog"

    print(f"DomainAuthorityScorer with default_weight={scorer_default.default_weight}:")
    print(f"  URL: {url_random1}, Score: {await scorer_default.score(url_random1):.2f}")
    
    print(f"\nDomainAuthorityScorer with custom default_weight={scorer_custom_default.default_weight}:")
    print(f"  URL: {url_random2}, Score: {await scorer_custom_default.score(url_random2):.2f}")

    # Check if the score matches the default_weight for domains not in the top_domains cache
    # (Assuming these random domains are not in the small pre-cached list)
    assert abs(await scorer_default.score(url_random1) - 0.5) < 0.01 
    assert abs(await scorer_custom_default.score(url_random2) - 0.3) < 0.01

asyncio.run(demo_domain_authority_default_weight())
```

---
## 4. Integration Examples

Showcasing how different deep crawling components can be combined.

### 4.1. Example: `BFSDeeepCrawlStrategy` with a `FilterChain` (`DomainFilter` + `URLPatternFilter`) and a simple `PathDepthScorer`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import (
    BFSDeeepCrawlStrategy, FilterChain, DomainFilter, URLPatternFilter, PathDepthScorer
)

RAW_HTML_INTEGRATION_1 = """
<html><body>
    <a href="http://example.com/docs/page1.html">Docs Page 1</a>
    <a href="http://example.com/blog/post1.html">Blog Post 1 (depth 2)</a>
    <a href="http://example.com/docs/page2.pdf">Docs Page 2 (PDF)</a>
    <a href="http://anotherexample.com/external.html">External HTML</a>
    <a href="http://example.com/very/deep/page.html">Deep Page (depth 3)</a>
</body></html>
"""
START_URL_INTEGRATION_1 = f"raw://{RAW_HTML_INTEGRATION_1}"

async def bfs_integration_example():
    # Filters: Only example.com, only .html files
    filter_chain = FilterChain(filters=[
        DomainFilter(allowed_domains=["example.com"]),
        URLPatternFilter(patterns=["*.html"])
    ])
    
    # Scorer: Prioritize pages with path depth 1 (e.g. /docs/)
    # Threshold will allow only high-scored links based on this.
    # Optimal depth 1, score for depth 1 = 1.0; depth 2 = 0.5; depth 3 = 0.33
    url_scorer = PathDepthScorer(optimal_depth=1)
    score_threshold = 0.6 # Allows only depth 1 pages

    bfs_strategy = BFSDeeepCrawlStrategy(
        max_depth=2, 
        max_pages=5,
        filter_chain=filter_chain,
        url_scorer=url_scorer,
        score_threshold=score_threshold
    )
    run_config = CrawlerRunConfig(deep_crawl_strategy=bfs_strategy)

    async with AsyncWebCrawler() as crawler:
        print("Starting BFS integration crawl...")
        results_list = await crawler.arun(url=START_URL_INTEGRATION_1, config=run_config)
        
        print(f"\n--- BFS Integration Results ---")
        crawled_urls = []
        if results_list:
            for result in results_list:
                if result.success:
                    print(f"Crawled: {result.url} (Depth: {result.metadata.get('depth')}, Score: {result.metadata.get('score')})")
                    crawled_urls.append(result.url)
            
            # Expected: Only "http://example.com/docs/page1.html" (depth 1, .html, on domain, score 1.0)
            # "/blog/post1.html" is depth 2, score 0.5 (below threshold)
            # "/docs/page2.pdf" fails pattern filter
            # "external.html" fails domain filter
            # "/very/deep/page.html" is depth 3, score 0.33 (below threshold)
            assert "http://example.com/docs/page1.html" in crawled_urls
            assert len(crawled_urls) == 2 # Start URL + one matched page
            assert "http://example.com/blog/post1.html" not in crawled_urls
            assert "http://example.com/docs/page2.pdf" not in crawled_urls
            assert "http://anotherexample.com/external.html" not in crawled_urls
            assert "http://example.com/very/deep/page.html" not in crawled_urls
        else:
            print("No results.")

asyncio.run(bfs_integration_example())
```

### 4.2. Example: `BestFirstCrawlingStrategy` driven by a `CompositeScorer` (`KeywordRelevanceScorer` + `FreshnessScorer`) and filtered by `ContentTypeFilter`.

```python
import asyncio
from datetime import datetime
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import (
    BestFirstCrawlingStrategy, CompositeScorer, KeywordRelevanceScorer, 
    FreshnessScorer, ContentTypeFilter
)

RAW_HTML_INTEGRATION_2 = f"""
<html><body>
    <a href="/news/{datetime.now().year}/ai-breakthrough.html">AI Breakthrough ({datetime.now().year})</a>
    <a href="/news/{datetime.now().year-1}/old-ai-news.html">Old AI News ({datetime.now().year-1})</a>
    <a href="/tech/general-tech.html">General Tech ({datetime.now().year})</a>
    <a href="/news/{datetime.now().year}/ai-update.pdf">AI Update PDF ({datetime.now().year})</a>
</body></html>
"""
START_URL_INTEGRATION_2 = f"raw://{RAW_HTML_INTEGRATION_2}"

async def best_first_integration_example():
    # Scorers
    keyword_scorer = KeywordRelevanceScorer(keywords=["ai"], weight=0.6)
    freshness_scorer = FreshnessScorer(current_year=datetime.now().year, weight=0.4)
    composite_scorer = CompositeScorer(scorers=[keyword_scorer, freshness_scorer])

    # Filter: Only HTML content
    content_filter = ContentTypeFilter(allowed_types=["text/html"])
    filter_chain = FilterChain(filters=[content_filter])

    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        max_pages=3, # Start URL + 2 more
        url_scorer=composite_scorer,
        filter_chain=filter_chain
    )
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, stream=True) # Stream to see order

    async with AsyncWebCrawler() as crawler:
        print("Starting Best-First integration crawl...")
        crawled_items_in_order = []
        async for result in await crawler.arun(url=START_URL_INTEGRATION_2, config=run_config):
            if result.success:
                print(f"Crawled: {result.url_for_display()} (Score: {result.metadata.get('score'):.2f}, Depth: {result.metadata.get('depth')})")
                crawled_items_in_order.append(result.url_for_display())
        
        print(f"\nCrawled order: {crawled_items_in_order}")
        # Expected:
        # 1. Start URL
        # 2. AI Breakthrough (current year, "ai" keyword) - Highest score
        # 3. General Tech (current year, no "ai") OR Old AI News (last year, "ai" keyword)
        #    - AI Breakthrough: kw_score=1*0.6=0.6, fresh_score=1*0.4=0.4. Total=1.0
        #    - Old AI News: kw_score=1*0.6=0.6, fresh_score=0.9*0.4=0.36. Total=0.96
        #    - General Tech: kw_score=0*0.6=0.0, fresh_score=1*0.4=0.4. Total=0.4
        #    - AI Update PDF: Filtered out by ContentTypeFilter
        # So, order after start URL should be AI Breakthrough, then Old AI News.
        if len(crawled_items_in_order) >= 3: # Start URL + 2 others
            assert "ai-breakthrough.html" in crawled_items_in_order[1]
            assert "old-ai-news.html" in crawled_items_in_order[2]
        assert not any("ai-update.pdf" in url for url in crawled_items_in_order)

asyncio.run(best_first_integration_example())
```

### 4.3. Example: `DFSDeeepCrawlStrategy` with `max_pages` and `max_depth` to show interaction.
(This has been demonstrated in 1.4.2.1 and 1.4.2.2 where either `max_depth` or `max_pages` can limit the crawl first.)

### 4.4. Example: Using `DeepCrawlDecorator` to initiate a `BFSDeeepCrawlStrategy` with a `FilterChain` including `ContentRelevanceFilter`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import (
    BFSDeeepCrawlStrategy, FilterChain, ContentRelevanceFilter
)
from unittest.mock import patch # To mock HeadPeek

async def decorator_bfs_content_relevance():
    query = "important information"
    # Filter chain with content relevance
    filter_chain = FilterChain(filters=[
        ContentRelevanceFilter(query=query, threshold=0.1)
    ])

    bfs_strategy = BFSDeeepCrawlStrategy(
        max_depth=1, 
        max_pages=3,
        filter_chain=filter_chain
    )
    run_config = CrawlerRunConfig(deep_crawl_strategy=bfs_strategy)

    html_relevant_head = "<head><title>Key Info</title><meta name='description' content='This page contains important information about our services.'></head>"
    html_irrelevant_head = "<head><title>Random Stuff</title><meta name='description' content='Some other details.'></head>"
    
    start_html = f"""<html><body>
        <a href="raw_relevant.html">Relevant Link</a>
        <a href="raw_irrelevant.html">Irrelevant Link</a>
    </body></html>"""
    
    # Create self-contained raw URLs (simplified)
    relevant_page_content = f"raw://{html_relevant_head}<body>Relevant content</body></html>"
    irrelevant_page_content = f"raw://{html_irrelevant_head}<body>Irrelevant content</body></html>"
    
    start_url_content_rel = start_html.replace("raw_relevant.html", relevant_page_content.replace('"', '&quot;')) \
                                     .replace("raw_irrelevant.html", irrelevant_page_content.replace('"', '&quot;'))
    start_url_content_rel = f"raw://{start_url_content_rel}"


    # Mock HeadPeek.peek_html to control responses for filter
    # This mapping helps return the correct head content for each URL
    mock_heads = {
        relevant_page_content: html_relevant_head, # Key by the full raw URL string
        irrelevant_page_content: html_irrelevant_head
    }
    
    async def mock_peek_html_func(url_to_peek):
        # For raw URLs, the actual URL is the content itself. We need to find the one that matches.
        for mock_url_key, head_content in mock_heads.items():
            if mock_url_key == url_to_peek: # Direct match for raw URLs
                 return head_content
        return "" # Default for unexpected URLs

    with patch('crawl4ai.deep_crawling.filters.HeadPeek.peek_html', side_effect=mock_peek_html_func):
        async with AsyncWebCrawler() as crawler: # Decorator is active via run_config
            print("Starting Decorator + BFS + ContentRelevanceFilter crawl...")
            results_list = await crawler.arun(url=start_url_content_rel, config=run_config)
            
            crawled_urls = []
            if results_list:
                print("\n--- Crawl Results ---")
                for result in results_list:
                    if result.success:
                        print(f"Crawled: {result.url_for_display()}")
                        crawled_urls.append(result.url_for_display())
                
                assert any(u == relevant_page_content for u in crawled_urls), "Relevant page should have been crawled."
                assert not any(u == irrelevant_page_content for u in crawled_urls), "Irrelevant page should have been filtered."
            else:
                print("No results.")

asyncio.run(decorator_bfs_content_relevance())
```

### 4.5. Example: `BestFirstCrawlingStrategy` using a `url_scorer` that includes `DomainAuthorityScorer` to prioritize high-authority external links when `include_external=True`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import (
    BestFirstCrawlingStrategy, DomainAuthorityScorer
)

RAW_HTML_INTEGRATION_DOMAIN_AUTH = """
<html><body>
    <a href="https://www.wikipedia.org">Wikipedia (High Auth)</a>
    <a href="http://example-blog.blogspot.com">Personal Blog (Low Auth)</a>
    <a href="https://github.com/crawl4ai">Crawl4AI GitHub (Mid/High Auth)</a>
</body></html>
"""
START_URL_INTEGRATION_DA = f"raw://{RAW_HTML_INTEGRATION_DOMAIN_AUTH}"

async def best_first_domain_authority_external():
    # Scorer: Prioritize by domain authority
    # Note: DomainAuthorityScorer has some pre-defined weights, wikipedia.org and github.com are usually high.
    domain_scorer = DomainAuthorityScorer() 

    strategy = BestFirstCrawlingStrategy(
        max_depth=1,
        max_pages=3, # Start URL + 2 external links
        url_scorer=domain_scorer,
        include_external=True # Crucial for this example
    )
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, stream=True)

    async with AsyncWebCrawler() as crawler:
        print("Starting Best-First crawl prioritizing high-authority external links...")
        crawled_urls_in_order = []
        async for result in await crawler.arun(url=START_URL_INTEGRATION_DA, config=run_config):
            if result.success:
                score = result.metadata.get('score', 'N/A')
                print(f"Crawled: {result.url} (Score: {score:.2f})")
                crawled_urls_in_order.append(result.url)
        
        print(f"\nCrawled order (after start URL): {[url.split('//')[1] for url in crawled_urls_in_order[1:]]}")
        
        # Expected order (after start URL): wikipedia.org, then github.com (or vice-versa), then blogspot.com
        # This depends on the default scores in DomainAuthorityScorer.
        # Wikipedia usually has a very high score.
        if len(crawled_urls_in_order) > 1:
            assert "wikipedia.org" in crawled_urls_in_order[1], "Wikipedia (high authority) should be prioritized."
        if len(crawled_urls_in_order) > 2:
             assert "github.com" in crawled_urls_in_order[2] or "blogspot.com" in crawled_urls_in_order[2]

asyncio.run(best_first_domain_authority_external())
```

---
## 5. Advanced Scenarios & Edge Cases

### 5.1. Example: Deep crawling a site where initial pages have no links, but deeper pages (found via alternative means, if simulatable) do.
*This scenario is hard to demonstrate without a mock server or very specific site structure. The core idea is that if the `start_url` itself has no links, the crawl stops unless the strategy has other means to find URLs (not typical for these strategies without custom `link_discovery` or being fed URLs externally).*
*A conceptual example: if `arun` was called with multiple start URLs, and one of them had links.*

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy

RAW_HTML_NO_LINKS = "<html><body>No links here.</body></html>"
RAW_HTML_WITH_LINKS = "<html><body><a href='http://example.com/final'>Final Page</a></body></html>"

# Create a scenario where the first URL has no links, but we want to show that if other URLs
# were added to the queue (e.g., from a different source or a modified strategy), they'd be processed.
# This tests the strategy's ability to continue if the queue is populated externally/later.
# For this example, we'll use a simple BFS and "manually" add to its queue for demo.

async def advanced_no_initial_links():
    strategy = BFSDeeepCrawlStrategy(max_depth=1, max_pages=3)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy)
    
    start_url_no_links = f"raw://{RAW_HTML_NO_LINKS}"
    second_url_with_links = f"raw://{RAW_HTML_WITH_LINKS}"

    async with AsyncWebCrawler() as crawler:
        print(f"Attempting crawl starting with URL that has no links: {start_url_no_links}")
        
        # First, try to crawl the page with no links. Expected: only start_url is processed.
        results1_container = await crawler.arun(url=start_url_no_links, config=run_config)
        results1 = [res async for res in results1_container] if hasattr(results1_container, '__aiter__') else results1_container

        print(f"Results from first crawl (no links): {[r.url_for_display() for r in results1]}")
        assert len(results1) == 1

        # Now, let's conceptualize how a strategy might continue if new URLs are added.
        # The actual strategies' queues are internal. We'll simulate a new crawl.
        # If the strategy's queue was externally populated, it would process them.
        # For a direct test, we'd need to modify the strategy or use a more complex setup.
        # This is more about the crawler's ability to handle an empty next_level from one source.
        
        print(f"\nSimulating a scenario where another URL with links is processed by the *same strategy instance* (if possible):")
        # To truly test this with the same strategy instance maintaining state,
        # we'd need to call its internal methods or re-architect this test.
        # For simplicity, we show that a *new* crawl with a populated start will work.
        
        results2_container = await crawler.arun(url=second_url_with_links, config=run_config)
        results2 = [res async for res in results2_container] if hasattr(results2_container, '__aiter__') else results2_container

        print(f"Results from second crawl (with links):")
        found_final_page = False
        for r in results2:
            print(f"  - {r.url_for_display()} (Depth: {r.metadata.get('depth')})")
            if "example.com/final" in r.url_for_display():
                found_final_page = True
        assert len(results2) >= 2 # start URL + final page
        assert found_final_page

asyncio.run(advanced_no_initial_links())
```

### 5.2. Example: Handling a `score_threshold` so high in `BFSDeeepCrawlStrategy` or `BestFirstCrawlingStrategy` that no new links are added.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeeepCrawlStrategy, PathDepthScorer

RAW_HTML_FOR_HIGH_THRESHOLD = """
<html><body>
    <a href="/page1">Page 1</a>
    <a href="/category/page2">Page 2</a>
</body></html>
"""
START_URL_RAW_HIGH_THRESHOLD = f"raw://{RAW_HTML_FOR_HIGH_THRESHOLD}"

async def high_score_threshold_no_new_links():
    # Scorer that gives scores between 0 and 1
    url_scorer = PathDepthScorer(optimal_depth=0) 
    
    # Set a threshold higher than any possible score (e.g., PathDepthScorer max is 1.0)
    high_threshold = 1.1 

    strategy = BFSDeeepCrawlStrategy( # Could also be BestFirstCrawlingStrategy
        max_depth=1, 
        max_pages=5,
        url_scorer=url_scorer,
        score_threshold=high_threshold
    )
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        print(f"Starting crawl with very high score_threshold ({high_threshold})...")
        results_list = await crawler.arun(url=START_URL_RAW_HIGH_THRESHOLD, config=run_config)
        
        print(f"\n--- Crawl Results (High Threshold) ---")
        crawled_urls_count = 0
        if results_list:
            for result in results_list:
                if result.success:
                    crawled_urls_count +=1
                    print(f"Crawled: {result.url_for_display()} (Depth: {result.metadata.get('depth')}, Score: {result.metadata.get('score', 'N/A')})")
            
            # Expect only the start URL to be crawled, as all discovered links will fail threshold
            assert crawled_urls_count == 1, "Only the start URL should be crawled with such a high threshold."
            assert strategy.stats.urls_skipped > 0, "Links should have been skipped due to threshold."
            print(f"URLs skipped by scorer: {strategy.stats.urls_skipped}")
        else:
            print("No results (unexpected).")

asyncio.run(high_score_threshold_no_new_links())
```

### 5.3. Example: Demonstrating the behavior of `max_pages` in BFS when a level has more links than the remaining page capacity.
(This was covered effectively by 1.3.5.2, which simulates the internal logic of `link_discovery` respecting `max_pages`.)

### 5.4. Example: `URLPatternFilter` with complex regex to match very specific URL structures.

```python
import asyncio
from crawl4ai.deep_crawling import URLPatternFilter

async def complex_regex_url_pattern():
    # Regex to match URLs like: /archive/YYYY/MM/DD/article-slug-with-hyphens.html
    # Where YYYY is 20xx, MM is 01-12, DD is 01-31.
    complex_pattern = r"/archive/20\d{2}/(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])/[a-z0-9-]+(\.html)?$"
    
    archive_filter = URLPatternFilter(patterns=[complex_pattern])

    urls_to_test = [
        "http://example.com/archive/2023/05/15/my-great-article.html", # Match
        "http://example.com/archive/2024/12/31/another-post",          # Match (optional .html)
        "http://example.com/archive/2022/13/01/invalid-month.html",    # No Match (invalid month)
        "http://example.com/blog/2023/05/15/my-great-article.html",    # No Match (wrong base path)
        "http://example.com/archive/1999/01/01/old-article.html"      # No Match (year doesn't start with 20)
    ]

    print(f"Testing with complex regex pattern: {complex_pattern}")
    for url in urls_to_test:
        passed = await archive_filter.apply(url)
        print(f"  URL: {url}, Passed: {passed}")

    assert await archive_filter.apply(urls_to_test[0]) == True
    assert await archive_filter.apply(urls_to_test[1]) == True
    assert await archive_filter.apply(urls_to_test[2]) == False
    assert await archive_filter.apply(urls_to_test[3]) == False
    assert await archive_filter.apply(urls_to_test[4]) == False

asyncio.run(complex_regex_url_pattern())
```

### 5.5. Example: A `FilterChain` where one filter passes a URL but a subsequent filter rejects it.

```python
import asyncio
from crawl4ai.deep_crawling import FilterChain, DomainFilter, URLPatternFilter

async def filter_chain_sequential_rejection():
    # Filter 1: Allow 'example.com' (will pass 'http://example.com/admin/login')
    domain_filter = DomainFilter(allowed_domains=["example.com"])
    
    # Filter 2: Reject anything with 'admin' (will reject 'http://example.com/admin/login')
    no_admin_filter = URLPatternFilter(patterns=["*admin*"], reverse=True)
    
    filter_chain = FilterChain(filters=[domain_filter, no_admin_filter])

    url_admin_on_domain = "http://example.com/admin/login"
    url_safe_on_domain = "http://example.com/dashboard"

    print("Testing FilterChain: DomainFilter (allow example.com) -> URLPatternFilter (reject *admin*)")
    
    passed_admin = await filter_chain.apply(url_admin_on_domain)
    print(f"URL: {url_admin_on_domain}, Passed Chain: {passed_admin}")
    print(f"  DomainFilter passed: {await domain_filter.apply(url_admin_on_domain)}") # Apply individually to see
    print(f"  NoAdminFilter passed: {await no_admin_filter.apply(url_admin_on_domain)}")
    assert not passed_admin # Should be rejected by the second filter

    passed_safe = await filter_chain.apply(url_safe_on_domain)
    print(f"URL: {url_safe_on_domain}, Passed Chain: {passed_safe}")
    print(f"  DomainFilter passed: {await domain_filter.apply(url_safe_on_domain)}")
    print(f"  NoAdminFilter passed: {await no_admin_filter.apply(url_safe_on_domain)}")
    assert passed_safe # Should pass both filters

asyncio.run(filter_chain_sequential_rejection())
```

---
End of Examples Document.
```
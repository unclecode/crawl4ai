# Examples Outline for crawl4ai - vibe Component

**Target Document Type:** Examples Collection
**Target Output Filename Suggestion:** `llm_examples_vibe.md`
**Library Version Context:** 0.6.3
**Outline Generation Date:** 2024-05-24
---

This document provides a collection of runnable code examples for the `vibe` component of the `crawl4ai` library, focusing on its deep crawling capabilities, filtering, and scoring mechanisms.

**Note on URLs:** Most examples use placeholder URLs like `https://docs.crawl4ai.com/vibe-examples/pageN.html`. These are for demonstration and will be mocked to return predefined content. Replace them with actual URLs for real-world use.

**Common Imports (assumed for many examples below, but will be included in each runnable block):**
```python
import asyncio
import time
import re
from pathlib import Path
import os # For local file examples
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    CrawlResult,
    BrowserConfig,
    CacheMode,
    # Deep Crawling Strategies
    BFSDeePCrawlStrategy,
    DFSDeePCrawlStrategy,
    BestFirstCrawlingStrategy,
    DeepCrawlStrategy, # For custom strategy
    # Filters
    FilterChain,
    URLPatternFilter,
    DomainFilter,
    ContentTypeFilter,
    URLFilter,
    ContentRelevanceFilter, # Conceptual
    SEOFilter,            # Conceptual
    FilterStats,
    # Scorers
    URLScorer, # For custom scorer
    KeywordRelevanceScorer,
    PathDepthScorer,
    ContentTypeScorer,
    DomainAuthorityScorer, # Conceptual
    FreshnessScorer,       # Conceptual
    CompositeScorer,
    # Other
    LLMExtractionStrategy, # For combination example
    AsyncLogger          # For custom logger example
)
from unittest.mock import patch, AsyncMock # For mocking network calls

# --- Mock Website Data ---
# This data will be used by the MockAsyncWebCrawler to simulate a website
MOCK_SITE_DATA = {
    "https://docs.crawl4ai.com/vibe-examples/index.html": {
        "html_content": """
            <html><head><title>Index</title></head><body>
                <h1>Main Page</h1>
                <a href="page1.html">Page 1</a>
                <a href="page2.html">Page 2 (Feature)</a>
                <a href="https://external-site.com/pageA.html">External Site</a>
                <a href="/vibe-examples/archive/old_page.html">Archive</a>
                <a href="/vibe-examples/blog/post1.html">Blog Post 1</a>
                <a href="/vibe-examples/login.html">Login</a>
                <a href="javascript:void(0);" onclick="document.body.innerHTML += '<a href=js_page.html>JS Link</a>'">Load JS Link</a>
            </body></html>
        """,
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://docs.crawl4ai.com/vibe-examples/page1.html": {
        "html_content": """
            <html><head><title>Page 1</title></head><body>
                <h2>Page One</h2>
                <p>This is page 1. It has some core content about crawl strategies.</p>
                <a href="page1_sub1.html">Sub Page 1.1</a>
                <a href="page1_sub2.pdf">Sub Page 1.2 (PDF)</a>
                <a href="index.html">Back to Index</a>
            </body></html>
        """,
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://docs.crawl4ai.com/vibe-examples/page1_sub1.html": {
        "html_content": "<html><head><title>Sub Page 1.1</title></head><body><p>Sub page 1.1 content. More on core concepts.</p></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://docs.crawl4ai.com/vibe-examples/page1_sub2.pdf": {
        "html_content": "%PDF-1.4 ... (Mock PDF Content: Crawl examples)", # Mock PDF content
        "response_headers": {"Content-Type": "application/pdf"}
    },
    "https://docs.crawl4ai.com/vibe-examples/page2.html": {
        "html_content": """
            <html><head><title>Page 2 - Feature Rich</title></head><body>
                <h2>Page Two with Feature</h2>
                <p>This page discusses a key feature and advanced configuration for async tasks.</p>
                <a href="page2_sub1.html">Sub Page 2.1</a>
            </body></html>
        """,
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://docs.crawl4ai.com/vibe-examples/page2_sub1.html": {
        "html_content": "<html><head><title>Sub Page 2.1</title></head><body><p>More about the feature and JavaScript interaction.</p></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://docs.crawl4ai.com/vibe-examples/archive/old_page.html": {
        "html_content": "<html><head><title>Old Page</title></head><body><p>Archived content, less relevant.</p></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://docs.crawl4ai.com/vibe-examples/blog/post1.html": {
        "html_content": "<html><head><title>Blog Post 1</title></head><body><p>This is a blog post about core ideas and examples.</p></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    },
     "https://docs.crawl4ai.com/vibe-examples/login.html": {
        "html_content": "<html><head><title>Login</title></head><body><form>...</form></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://docs.crawl4ai.com/vibe-examples/js_page.html": {
        "html_content": "<html><head><title>JS Page</title></head><body><p>Content loaded by JavaScript.</p></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    },
    "https://external-site.com/pageA.html": {
        "html_content": "<html><head><title>External Page A</title></head><body><p>Content from external site about other topics.</p></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    },
    # For local file examples
    "file:" + str(Path(os.getcwd()) / "test_local_index.html"): {
         "html_content": """
            <html><head><title>Local Index</title></head><body>
                <h1>Local Main Page</h1>
                <a href="test_local_page1.html">Local Page 1</a>
                <a href="https://docs.crawl4ai.com/vibe-examples/index.html">Web Index</a>
            </body></html>
        """,
        "response_headers": {"Content-Type": "text/html"}
    },
    "file:" + str(Path(os.getcwd()) / "test_local_page1.html"): {
        "html_content": "<html><head><title>Local Page 1</title></head><body><p>Local page 1 content.</p></body></html>",
        "response_headers": {"Content-Type": "text/html"}
    }
}

# Create a dummy local file for testing
Path("test_local_index.html").write_text(MOCK_SITE_DATA["file:" + str(Path(os.getcwd()) / "test_local_index.html")]["html_content"])
Path("test_local_page1.html").write_text(MOCK_SITE_DATA["file:" + str(Path(os.getcwd()) / "test_local_page1.html")]["html_content"])


# --- Mock AsyncWebCrawler ---
# This mock crawler will simulate fetching pages from MOCK_SITE_DATA
class MockAsyncWebCrawler(AsyncWebCrawler):
    async def _fetch_page(self, url: str, config: CrawlerRunConfig):
        # Simulate network delay
        await asyncio.sleep(0.01)
        
        # Normalize URL for lookup (e.g. relative to absolute)
        if not url.startswith("file:") and not url.startswith("http"):
            # This is a simplified relative URL resolver for the mock
            base_parts = self.current_url.split('/')[:-1] if hasattr(self, 'current_url') and self.current_url else []
            normalized_url = "/".join(base_parts + [url])
            if "docs.crawl4ai.com" not in normalized_url and not normalized_url.startswith("file:"): # ensure base domain
                 normalized_url = "https://docs.crawl4ai.com/vibe-examples/" + url.lstrip("/")
        else:
            normalized_url = url

        if normalized_url in MOCK_SITE_DATA:
            page_data = MOCK_SITE_DATA[normalized_url]
            self.current_url = normalized_url # Store for relative path resolution
            
            # Basic link extraction for deep crawling
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_data["html_content"], 'html.parser')
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                # Simple relative to absolute conversion for mock
                if not href.startswith("http") and not href.startswith("file:") and not href.startswith("javascript:"):
                    abs_href = "/".join(normalized_url.split('/')[:-1]) + "/" + href.lstrip("./")
                     # Further simplify to ensure it hits mock data, very basic
                    if "docs.crawl4ai.com" in abs_href: # if it's a vibe-example page
                        abs_href = "https://docs.crawl4ai.com/vibe-examples/" + Path(href).name
                    elif "external-site.com" in abs_href:
                        abs_href = "https://external-site.com/" + Path(href).name

                elif href.startswith("file:"): # Keep file URLs as is
                    abs_href = href
                elif href.startswith("javascript:"):
                    abs_href = None # Skip JS links for this mock
                else:
                    abs_href = href
                
                if abs_href:
                    links.append({"href": abs_href, "text": a_tag.get_text(strip=True)})

            return CrawlResult(
                url=normalized_url,
                html_content=page_data["html_content"],
                success=True,
                status_code=200,
                response_headers=page_data.get("response_headers", {"Content-Type": "text/html"}),
                links={"internal": [l for l in links if "docs.crawl4ai.com/vibe-examples" in l["href"] or l["href"].startswith("file:")], 
                       "external": [l for l in links if "external-site.com" in l["href"]]}
            )
        else:
            # print(f"Mock Warning: URL not found in MOCK_SITE_DATA: {normalized_url} (Original: {url})")
            return CrawlResult(
                url=url, html_content="", success=False, status_code=404, error_message="Mock URL not found"
            )

    async def arun(self, url: str, config: CrawlerRunConfig = None, **kwargs):
        # This is the method called by DeepCrawlStrategy instances
        # For deep crawls, the strategy itself calls this multiple times.
        # For a single arun call with a deep_crawl_strategy, the decorator handles it.
        
        if config and config.deep_crawl_strategy:
             # The decorator usually handles this part. For direct strategy.arun() tests:
            return await config.deep_crawl_strategy.arun(
                crawler=self, # Pass the mock crawler instance
                start_url=url,
                config=config
            )
        
        # Fallback to single page fetch if no deep crawl strategy
        self.current_url = url # Set for relative path resolution in _fetch_page
        return await self._fetch_page(url, config)

    async def arun_many(self, urls: list[str], config: CrawlerRunConfig = None, **kwargs):
        results = []
        for url_item in urls:
            # In BestFirst, arun_many is called with tuples of (score, depth, url, parent_url)
            # For simplicity in mock, we assume url_item is just the URL string here or a tuple where url is at index 2
            current_url_to_crawl = url_item
            if isinstance(url_item, tuple) and len(url_item) >=3 :
                 current_url_to_crawl = url_item[2]

            self.current_url = current_url_to_crawl # Set for relative path resolution
            result = await self._fetch_page(current_url_to_crawl, config)
            results.append(result)
        if config and config.stream:
            async def result_generator():
                for res in results:
                    yield res
            return result_generator()
        return results

    async def __aenter__(self):
        # print("MockAsyncWebCrawler entered")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # print("MockAsyncWebCrawler exited")
        pass
    
    async def start(self): # Add start method
        # print("MockAsyncWebCrawler started")
        self.ready = True
        return self

    async def close(self): # Add close method
        # print("MockAsyncWebCrawler closed")
        self.ready = False

# --- End Mock ---
```

---
## 1. Introduction to Deep Crawling (`vibe`)

The `vibe` component of Crawl4ai provides powerful deep crawling capabilities, allowing you to traverse websites by following links and processing multiple pages.

### 1.1. Example: Enabling Basic Deep Crawl with `BFSDeePCrawlStrategy` via `CrawlerRunConfig`.
This example demonstrates how to enable a basic Breadth-First Search (BFS) deep crawl by setting the `deep_crawl_strategy` in `CrawlerRunConfig`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

# Using the MockAsyncWebCrawler defined in the preamble
@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def basic_bfs_deep_crawl():
    # Configure BFS to crawl up to 1 level deep from the start URL
    bfs_strategy = BFSDeePCrawlStrategy(max_depth=1)
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=bfs_strategy,
        # For mock, ensure cache is bypassed to see fresh mock results
        cache_mode=CacheMode.BYPASS 
    )

    # The actual AsyncWebCrawler is replaced by MockAsyncWebCrawler via @patch
    async with AsyncWebCrawler() as crawler: # This will be MockAsyncWebCrawler
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- Basic BFS Deep Crawl (max_depth=1) ---")
        print(f"Crawled {len(results)} pages starting from {start_url}:")
        for i, result in enumerate(results):
            if result.success:
                print(f"  {i+1}. URL: {result.url}, Depth: {result.metadata.get('depth')}, Parent: {result.metadata.get('parent_url')}")
            else:
                print(f"  {i+1}. FAILED: {result.url}, Error: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(basic_bfs_deep_crawl())
```

### 1.2. Example: Understanding `CrawlResult.metadata` (depth, parent_url, score) in Deep Crawl Results.
Each `CrawlResult` from a deep crawl contains useful metadata like the crawl `depth`, the `parent_url` from which it was discovered, and a `score` (if applicable, e.g., with `BestFirstCrawlingStrategy`).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, KeywordRelevanceScorer, BestFirstCrawlingStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def understand_metadata():
    # Using BestFirstCrawlingStrategy to demonstrate scores
    scorer = KeywordRelevanceScorer(keywords=["feature", "core"])
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=scorer)
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- Understanding CrawlResult.metadata ---")
        for result in results:
            if result.success:
                depth = result.metadata.get('depth', 'N/A')
                parent = result.metadata.get('parent_url', 'N/A')
                score = result.metadata.get('score', 'N/A') # Score comes from BestFirst strategy
                print(f"URL: {result.url}")
                print(f"  Depth: {depth}")
                print(f"  Parent URL: {parent}")
                print(f"  Score: {score if score != 'N/A' else 'N/A (not scored or BFS/DFS)'}")
                print("-" * 20)

if __name__ == "__main__":
    asyncio.run(understand_metadata())
```

### 1.3. Example: Minimal setup for deep crawling a single level deep.
This demonstrates the most straightforward way to perform a shallow deep crawl (depth 1).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def minimal_single_level_deep_crawl():
    # BFS strategy, max_depth=1 means start_url + its direct links
    strategy = BFSDeePCrawlStrategy(max_depth=1) 
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- Minimal Single Level Deep Crawl (max_depth=1) ---")
        print(f"Total pages crawled: {len(results)}")
        for result in results:
            if result.success:
                print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(minimal_single_level_deep_crawl())
```

---
## 2. Breadth-First Search (`BFSDeePCrawlStrategy`) Examples

`BFSDeePCrawlStrategy` explores the website level by level.

### 2.1. Example: Basic `BFSDeePCrawlStrategy` with default depth.
The default `max_depth` for `BFSDeePCrawlStrategy` is often 1 if not specified, meaning it crawls the start URL and its direct links.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_default_depth():
    # Default max_depth is typically 1 (start_url + its direct children)
    # but let's be explicit for clarity or test with a higher default if library changes
    strategy = BFSDeePCrawlStrategy() # Default max_depth is 1
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- BFS with Default Depth (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(bfs_default_depth())
```

### 2.2. Example: `BFSDeePCrawlStrategy` - Setting `max_depth` to control crawl depth (e.g., 3 levels).
Control how many levels deep the BFS crawler will go from the start URL. `max_depth=0` means only the start URL. `max_depth=1` means start URL + its direct links.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_set_max_depth():
    strategy = BFSDeePCrawlStrategy(max_depth=2) # Start URL (0), its links (1), and their links (2)
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- BFS with max_depth=2 ---")
        print(f"Crawled {len(results)} pages.")
        for result in sorted(results, key=lambda r: (r.metadata.get('depth', 0), r.url)):
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
        
        # Verify that no pages with depth > 2 are present
        assert all(r.metadata.get('depth', 0) <= 2 for r in results if r.success)

if __name__ == "__main__":
    asyncio.run(bfs_set_max_depth())
```

### 2.3. Example: `BFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages crawled (e.g., 10 pages).
Limit the crawl to a maximum number of pages, regardless of depth.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch
import math # for math.inf

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_set_max_pages():
    strategy = BFSDeePCrawlStrategy(
        max_depth=math.inf, # Effectively no depth limit for this test
        max_pages=3         # Limit to 3 pages
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- BFS with max_pages=3 ---")
        print(f"Crawled {len(results)} pages (should be at most 3).")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
        
        assert len(results) <= 3

if __name__ == "__main__":
    asyncio.run(bfs_set_max_pages())
```

### 2.4. Example: `BFSDeePCrawlStrategy` - Using `include_external=True` to follow links to external domains.
Allow the BFS crawler to follow links that lead to different domains than the start URL.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_include_external():
    strategy = BFSDeePCrawlStrategy(
        max_depth=1, 
        include_external=True
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- BFS with include_external=True (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        found_external = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            if "external-site.com" in result.url:
                found_external = True
        
        assert found_external, "Expected to crawl an external link."

if __name__ == "__main__":
    asyncio.run(bfs_include_external())
```

### 2.5. Example: `BFSDeePCrawlStrategy` - Using `include_external=False` (default) to stay within the starting domain.
The default behavior is to only crawl links within the same domain as the start URL.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_exclude_external():
    strategy = BFSDeePCrawlStrategy(
        max_depth=1, 
        include_external=False # Default, but explicit for clarity
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- BFS with include_external=False (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        found_external = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            if "external-site.com" in result.url:
                found_external = True
        
        assert not found_external, "Should not have crawled external links."

if __name__ == "__main__":
    asyncio.run(bfs_exclude_external())
```

### 2.6. Example: `BFSDeePCrawlStrategy` - Streaming results using `CrawlerRunConfig(stream=True)`.
Process results as they become available, useful for long crawls.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_streaming_results():
    strategy = BFSDeePCrawlStrategy(max_depth=1)
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True, # Enable streaming
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        print(f"--- BFS with Streaming Results (max_depth=1) ---")
        count = 0
        async for result in await crawler.arun(url=start_url, config=run_config):
            count += 1
            if result.success:
                print(f"  Streamed Result {count}: {result.url}, Depth: {result.metadata.get('depth')}")
            else:
                print(f"  Streamed FAILED Result {count}: {result.url}, Error: {result.error_message}")
        print(f"Total results streamed: {count}")

if __name__ == "__main__":
    asyncio.run(bfs_streaming_results())
```

### 2.7. Example: `BFSDeePCrawlStrategy` - Batch results using `CrawlerRunConfig(stream=False)` (default).
The default behavior is to return all results as a list after the crawl completes.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_batch_results():
    strategy = BFSDeePCrawlStrategy(max_depth=1)
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=False, # Default, but explicit for clarity
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config) # Returns a list
        
        print(f"--- BFS with Batch Results (max_depth=1) ---")
        print(f"Received {len(results)} pages in a batch.")
        for result in results:
            if result.success:
                print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(bfs_batch_results())
```

### 2.8. Example: `BFSDeePCrawlStrategy` - Integrating a `FilterChain` with `URLPatternFilter` to crawl specific paths.
Use filters to guide the crawler, for instance, to only explore URLs matching `/blog/*`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_with_url_pattern_filter():
    # Only crawl URLs containing '/blog/'
    url_filter = URLPatternFilter(patterns=["*/blog/*"])
    filter_chain = FilterChain(filters=[url_filter])
    
    strategy = BFSDeePCrawlStrategy(
        max_depth=1, 
        filter_chain=filter_chain
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- BFS with URLPatternFilter ('*/blog/*') ---")
        print(f"Crawled {len(results)} pages.")
        all_match_pattern = True
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            # The start URL itself might not match, but discovered links should
            if result.metadata.get('depth', 0) > 0 and "/blog/" not in result.url:
                all_match_pattern = False
        
        # The start_url itself is always processed, then its links are filtered.
        # So, we check if all *discovered* pages match the pattern.
        discovered_pages = [r for r in results if r.metadata.get('depth',0) > 0]
        if discovered_pages: # only assert if any pages beyond start_url were processed
            assert all("/blog/" in r.url for r in discovered_pages), "Not all crawled pages matched the /blog/ pattern"
        print("Filter applied successfully (start URL is always processed, subsequent links are filtered).")


if __name__ == "__main__":
    asyncio.run(bfs_with_url_pattern_filter())
```

### 2.9. Example: `BFSDeePCrawlStrategy` - Demonstrating `shutdown()` to gracefully stop an ongoing crawl.
Showcase how to stop a crawl prematurely using the strategy's `shutdown()` method.

```python
import asyncio
import time
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_demonstrate_shutdown():
    strategy = BFSDeePCrawlStrategy(
        max_depth=5, # A potentially long crawl
        max_pages=100 
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True, # Streaming is good to see partial results before shutdown
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html" # A site with enough links
        
        print(f"--- BFS with shutdown() demonstration ---")
        
        crawl_task = asyncio.create_task(crawler.arun(url=start_url, config=run_config))
        
        # Let the crawl run for a very short time
        await asyncio.sleep(0.1) 
        
        print("Attempting to shut down the crawl...")
        await strategy.shutdown() 
        
        results_list = []
        try:
            # Await the results from the crawl task
            # If streaming, this will iterate through what was processed before shutdown
            async for res in await crawl_task:
                results_list.append(res)
                print(f"  Collected result (post-shutdown signal): {res.url}")
        except asyncio.CancelledError:
            print("Crawl task was cancelled.")
        
        print(f"Crawl shut down. Processed {len(results_list)} pages before/during shutdown.")
        # The number of pages will be less than if it ran to completion
        assert len(results_list) < 10, "Crawl likely didn't shut down early enough or mock site too small."

if __name__ == "__main__":
    asyncio.run(bfs_demonstrate_shutdown())
```

### 2.10. Example: `BFSDeePCrawlStrategy` - Crawling with no `max_depth` limit but a `max_pages` limit.
Demonstrate a scenario where depth is unlimited (or very high) but the crawl stops after a certain number of pages.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch
import math

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def bfs_no_depth_limit_max_pages():
    strategy = BFSDeePCrawlStrategy(
        max_depth=math.inf, # Unlimited depth
        max_pages=4        # But only 4 pages
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- BFS with no depth limit, max_pages=4 ---")
        print(f"Crawled {len(results)} pages.")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
        
        assert len(results) <= 4, "More pages crawled than max_pages limit."

if __name__ == "__main__":
    asyncio.run(bfs_no_depth_limit_max_pages())
```

---
## 3. Depth-First Search (`DFSDeePCrawlStrategy`) Examples

`DFSDeePCrawlStrategy` explores as far down one branch as possible before backtracking.

### 3.1. Example: Basic `DFSDeePCrawlStrategy` with default depth.
The default `max_depth` for `DFSDeePCrawlStrategy` is typically 10 if not specified.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_default_depth():
    # Default max_depth for DFS is typically higher (e.g., 10)
    strategy = DFSDeePCrawlStrategy() 
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        max_pages=5, # Limit pages to keep example short with default depth
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- DFS with Default Depth (max_pages=5 to limit output) ---")
        print(f"Crawled {len(results)} pages.")
        for result in results: # Order might be less predictable than BFS for small mock
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(dfs_default_depth())
```

### 3.2. Example: `DFSDeePCrawlStrategy` - Setting `max_depth` to control how deep each branch goes.
Set `max_depth` to 2 for a DFS crawl.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_set_max_depth():
    strategy = DFSDeePCrawlStrategy(max_depth=2)
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- DFS with max_depth=2 ---")
        print(f"Crawled {len(results)} pages.")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
        assert all(r.metadata.get('depth', 0) <= 2 for r in results if r.success)


if __name__ == "__main__":
    asyncio.run(dfs_set_max_depth())
```

### 3.3. Example: `DFSDeePCrawlStrategy` - Setting `max_pages` to limit the total number of pages.
Limit the total number of pages crawled by DFS to 3.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch
import math

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_set_max_pages():
    strategy = DFSDeePCrawlStrategy(
        max_depth=math.inf, # No depth limit for this test
        max_pages=3
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- DFS with max_pages=3 ---")
        print(f"Crawled {len(results)} pages (should be at most 3).")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
        assert len(results) <= 3

if __name__ == "__main__":
    asyncio.run(dfs_set_max_pages())
```

### 3.4. Example: `DFSDeePCrawlStrategy` - Following external links with `include_external=True`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_include_external():
    strategy = DFSDeePCrawlStrategy(
        max_depth=1, 
        include_external=True,
        max_pages=5 # Limit pages as external can be vast
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- DFS with include_external=True (max_depth=1, max_pages=5) ---")
        print(f"Crawled {len(results)} pages.")
        found_external = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            if "external-site.com" in result.url:
                found_external = True
        
        assert found_external, "Expected to crawl an external link."

if __name__ == "__main__":
    asyncio.run(dfs_include_external())
```

### 3.5. Example: `DFSDeePCrawlStrategy` - Staying within the domain with `include_external=False`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_exclude_external():
    strategy = DFSDeePCrawlStrategy(
        max_depth=1, 
        include_external=False # Default
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- DFS with include_external=False (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        found_external = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            if "external-site.com" in result.url:
                found_external = True
        
        assert not found_external, "Should not have crawled external links."

if __name__ == "__main__":
    asyncio.run(dfs_exclude_external())
```

### 3.6. Example: `DFSDeePCrawlStrategy` - Streaming results.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_streaming_results():
    strategy = DFSDeePCrawlStrategy(max_depth=1)
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        print(f"--- DFS with Streaming Results (max_depth=1) ---")
        count = 0
        async for result in await crawler.arun(url=start_url, config=run_config):
            count +=1
            if result.success:
                print(f"  Streamed Result {count}: {result.url}, Depth: {result.metadata.get('depth')}")
        print(f"Total results streamed: {count}")


if __name__ == "__main__":
    asyncio.run(dfs_streaming_results())
```

### 3.7. Example: `DFSDeePCrawlStrategy` - Batch results.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_batch_results():
    strategy = DFSDeePCrawlStrategy(max_depth=1)
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=False, # Default
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- DFS with Batch Results (max_depth=1) ---")
        print(f"Received {len(results)} pages in a batch.")
        for result in results:
            if result.success:
                print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(dfs_batch_results())
```

### 3.8. Example: `DFSDeePCrawlStrategy` - Integrating a `FilterChain` with `DomainFilter` to restrict to subdomains.
This example is conceptual for subdomains as MOCK_SITE_DATA doesn't have distinct subdomains. The filter setup is key.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DFSDeePCrawlStrategy, FilterChain, DomainFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def dfs_with_domain_filter_subdomains():
    # Allow only the start domain and its subdomains
    # For this mock, 'docs.crawl4ai.com' will be the main domain.
    # If we had e.g., 'blog.docs.crawl4ai.com', this filter would allow it.
    domain_filter = DomainFilter(
        allowed_domains=["docs.crawl4ai.com"], 
        allow_subdomains=True
    )
    filter_chain = FilterChain(filters=[domain_filter])
    
    strategy = DFSDeePCrawlStrategy(
        max_depth=1, 
        filter_chain=filter_chain,
        include_external=True # Necessary to even consider other (sub)domains
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- DFS with DomainFilter (allow subdomains of docs.crawl4ai.com) ---")
        print(f"Crawled {len(results)} pages.")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            # In a real scenario, you'd assert that only allowed domains/subdomains are present.
            # Our mock data doesn't have true subdomains to test this effectively.
            assert "docs.crawl4ai.com" in result.url or "external-site.com" not in result.url

if __name__ == "__main__":
    asyncio.run(dfs_with_domain_filter_subdomains())
```

---
## 4. Best-First Crawling (`BestFirstCrawlingStrategy`) Examples

`BestFirstCrawlingStrategy` uses a priority queue, guided by scorers, to decide which URLs to crawl next.

### 4.1. Example: Basic `BestFirstCrawlingStrategy` with default parameters.
If no `url_scorer` is provided, it behaves somewhat like BFS but might have different internal queue management.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_default_params():
    strategy = BestFirstCrawlingStrategy(max_depth=1) # Default scorer (often scores 0)
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- BestFirstCrawlingStrategy with default parameters (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}, Score: {result.metadata.get('score', 0.0):.2f}")

if __name__ == "__main__":
    asyncio.run(best_first_default_params())
```

### 4.2. Example: `BestFirstCrawlingStrategy` - Setting `max_depth` to limit crawl depth.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_max_depth():
    strategy = BestFirstCrawlingStrategy(max_depth=2)
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- BestFirstCrawlingStrategy with max_depth=2 ---")
        print(f"Crawled {len(results)} pages.")
        for result in sorted(results, key=lambda r: (r.metadata.get('depth', 0), r.url)):
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}, Score: {result.metadata.get('score', 0.0):.2f}")
        assert all(r.metadata.get('depth', 0) <= 2 for r in results if r.success)

if __name__ == "__main__":
    asyncio.run(best_first_max_depth())
```

### 4.3. Example: `BestFirstCrawlingStrategy` - Setting `max_pages` to limit total pages crawled.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from unittest.mock import patch
import math

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_max_pages():
    strategy = BestFirstCrawlingStrategy(
        max_depth=math.inf, 
        max_pages=3
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- BestFirstCrawlingStrategy with max_pages=3 ---")
        print(f"Crawled {len(results)} pages.")
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}, Score: {result.metadata.get('score', 0.0):.2f}")
        assert len(results) <= 3

if __name__ == "__main__":
    asyncio.run(best_first_max_pages())
```

### 4.4. Example: `BestFirstCrawlingStrategy` - Using `include_external=True`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_include_external():
    strategy = BestFirstCrawlingStrategy(
        max_depth=1, 
        include_external=True,
        max_pages=5 # To keep it manageable
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- BestFirstCrawlingStrategy with include_external=True (max_depth=1) ---")
        print(f"Crawled {len(results)} pages.")
        found_external = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}, Score: {result.metadata.get('score', 0.0):.2f}")
            if "external-site.com" in result.url:
                found_external = True
        
        assert found_external, "Expected to crawl an external link."

if __name__ == "__main__":
    asyncio.run(best_first_include_external())
```

### 4.5. Example: `BestFirstCrawlingStrategy` - Using `KeywordRelevanceScorer` to prioritize URLs containing specific keywords.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_keyword_scorer():
    scorer = KeywordRelevanceScorer(keywords=["feature", "advanced", "core"])
    strategy = BestFirstCrawlingStrategy(
        max_depth=1, 
        url_scorer=scorer,
        max_pages=4 # Limit for example clarity
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS,
        stream=True # Stream to see order
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        print(f"--- BestFirstCrawlingStrategy with KeywordRelevanceScorer ---")
        results_list = []
        async for result in await crawler.arun(url=start_url, config=run_config):
            results_list.append(result)
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f} (Depth: {result.metadata.get('depth')})")
        
        # Check if pages with keywords like "feature" or "core" were prioritized (appeared earlier/higher score)
        # This is a soft check as actual order depends on many factors in a real crawl
        # and the mock site's link structure.
        print("\nNote: Higher scores should ideally correspond to URLs with keywords 'feature', 'advanced', 'core'.")
        feature_page_crawled = any("page2.html" in r.url for r in results_list) # page2 has "feature"
        assert feature_page_crawled, "Page with 'feature' keyword was expected."


if __name__ == "__main__":
    asyncio.run(best_first_keyword_scorer())
```

### 4.6. Example: `BestFirstCrawlingStrategy` - Using `PathDepthScorer` to influence priority based on URL path depth.
This scorer penalizes deeper paths by default.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, PathDepthScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_path_depth_scorer():
    # Penalizes deeper paths (lower score for deeper paths)
    scorer = PathDepthScorer(higher_score_is_better=False) 
    strategy = BestFirstCrawlingStrategy(
        max_depth=2, # Allow some depth to see scorer effect
        url_scorer=scorer
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS,
        stream=True
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        print(f"--- BestFirstCrawlingStrategy with PathDepthScorer (favoring shallower paths) ---")
        
        results_list = []
        async for result in await crawler.arun(url=start_url, config=run_config):
            results_list.append(result)
            if result.success:
                 print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Depth: {result.metadata.get('depth')}")
        
        # A simple check: depth 1 pages should generally have higher (less negative) scores than depth 2
        # (if scores are negative due to penalty) or simply appear earlier if scores are positive.
        # With default scoring, higher score_is_better = True, so higher depth = lower score.
        # With higher_score_is_better=False, higher depth = higher (less negative) score.
        # The mock PathDepthScorer will need to be implemented or this test adjusted based on actual scorer logic.
        # For now, let's assume the scorer penalizes, so deeper paths have lower (more negative) scores.
        print("\nNote: Shallower pages should ideally have higher scores.")


if __name__ == "__main__":
    asyncio.run(best_first_path_depth_scorer())
```

### 4.7. Example: `BestFirstCrawlingStrategy` - Using `ContentTypeScorer` to prioritize HTML pages over PDFs.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, ContentTypeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_content_type_scorer():
    # Prioritize HTML, penalize PDF
    scorer = ContentTypeScorer(content_type_weights={"text/html": 1.0, "application/pdf": -0.5})
    strategy = BestFirstCrawlingStrategy(
        max_depth=1, 
        url_scorer=scorer
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS,
        stream=True
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # This page links to HTML and PDF
        print(f"--- BestFirstCrawlingStrategy with ContentTypeScorer (HTML > PDF) ---")
        
        results_list = []
        async for result in await crawler.arun(url=start_url, config=run_config):
            results_list.append(result)
            if result.success:
                 print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Content-Type: {result.response_headers.get('Content-Type')}")

        html_page_score = next((r.metadata.get('score') for r in results_list if "page1_sub1.html" in r.url), None)
        pdf_page_score = next((r.metadata.get('score') for r in results_list if "page1_sub2.pdf" in r.url), None)

        print(f"HTML page score: {html_page_score}, PDF page score: {pdf_page_score}")
        if html_page_score is not None and pdf_page_score is not None:
            assert html_page_score > pdf_page_score, "HTML page should have a higher score than PDF."
        elif html_page_score is None or pdf_page_score is None:
            print("Warning: Could not find both HTML and PDF pages in results to compare scores.")


if __name__ == "__main__":
    asyncio.run(best_first_content_type_scorer())
```

### 4.8. Example: `BestFirstCrawlingStrategy` - Using `CompositeScorer` to combine `KeywordRelevanceScorer` and `PathDepthScorer`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer, PathDepthScorer, CompositeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_composite_scorer():
    keyword_scorer = KeywordRelevanceScorer(keywords=["feature", "core"], weight=0.7)
    path_scorer = PathDepthScorer(weight=0.3, higher_score_is_better=False) # Penalize depth slightly
    
    composite_scorer = CompositeScorer(scorers=[keyword_scorer, path_scorer])
    
    strategy = BestFirstCrawlingStrategy(
        max_depth=2, 
        url_scorer=composite_scorer,
        max_pages=6
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS,
        stream=True
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        print(f"--- BestFirstCrawlingStrategy with CompositeScorer ---")
        
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Depth: {result.metadata.get('depth')}")
        print("\nNote: Scores are a combination of keyword relevance and path depth penalty.")

if __name__ == "__main__":
    asyncio.run(best_first_composite_scorer())
```

### 4.9. Example: `BestFirstCrawlingStrategy` - Integrating a `FilterChain` with `ContentTypeFilter` to only process HTML.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, FilterChain, ContentTypeFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_with_content_type_filter():
    content_filter = ContentTypeFilter(allowed_types=["text/html"])
    filter_chain = FilterChain(filters=[content_filter])
    
    # Scorer is optional here, just demonstrating filter integration
    strategy = BestFirstCrawlingStrategy(
        max_depth=1, 
        filter_chain=filter_chain
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # This page links to HTML and PDF
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- BestFirstCrawlingStrategy with ContentTypeFilter (HTML only) ---")
        print(f"Crawled {len(results)} pages.")
        all_html = True
        for result in results:
            content_type = result.response_headers.get('Content-Type', '')
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}, Content-Type: {content_type}")
            if result.metadata.get('depth',0) > 0 and "text/html" not in content_type : # Start URL is not filtered
                 all_html = False
        
        discovered_pages = [r for r in results if r.metadata.get('depth',0) > 0]
        if discovered_pages:
            assert all("text/html" in r.response_headers.get('Content-Type','') for r in discovered_pages), "Non-HTML page found among discovered pages."
        print("Filter for HTML content type applied successfully to discovered pages.")

if __name__ == "__main__":
    asyncio.run(best_first_with_content_type_filter())
```

### 4.10. Example: `BestFirstCrawlingStrategy` - Streaming results and observing the order based on scores.
This example will use a scorer and stream results to demonstrate that higher-scored URLs are (generally) processed earlier.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_streaming_order():
    scorer = KeywordRelevanceScorer(keywords=["feature", "advanced"])
    strategy = BestFirstCrawlingStrategy(
        max_depth=1, 
        url_scorer=scorer,
        max_pages=5
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        print(f"--- BestFirstCrawlingStrategy - Streaming and Observing Order ---")
        
        previous_score = float('inf') # Assuming scores are positive and higher is better
        processed_urls = []
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                current_score = result.metadata.get('score', 0.0)
                print(f"  Streamed: {result.url}, Score: {current_score:.2f}, Depth: {result.metadata.get('depth')}")
                # Note: Due to batching (BATCH_SIZE) and async nature, strict descending order isn't guaranteed
                # but generally higher scored items should appear earlier.
                # assert current_score <= previous_score + 1e-9, f"Scores not in generally descending order: {previous_score} then {current_score}"
                # previous_score = current_score
                processed_urls.append((result.url, current_score))

        print("\nProcessed URLs and their scores (order of processing):")
        for url, score in processed_urls:
            print(f"  {url} (Score: {score:.2f})")
        print("Note: Higher scored URLs are prioritized but strict order depends on batching and concurrency.")

if __name__ == "__main__":
    asyncio.run(best_first_streaming_order())
```

### 4.11. Example: `BestFirstCrawlingStrategy` - Batch results and analyzing scores post-crawl.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_batch_analysis():
    scorer = KeywordRelevanceScorer(keywords=["feature", "core"])
    strategy = BestFirstCrawlingStrategy(
        max_depth=1, 
        url_scorer=scorer,
        max_pages=5
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=False, # Batch mode
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- BestFirstCrawlingStrategy - Batch Results Analysis ---")
        print(f"Received {len(results)} pages.")
        
        # Sort by score for analysis (higher score first)
        sorted_results = sorted(results, key=lambda r: r.metadata.get('score', 0.0), reverse=True)
        
        for result in sorted_results:
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Depth: {result.metadata.get('depth')}")

if __name__ == "__main__":
    asyncio.run(best_first_batch_analysis())
```

### 4.12. Example: `BestFirstCrawlingStrategy` - Accessing and interpreting `score`, `depth`, and `parent_url` from `CrawlResult.metadata`.
This explicitly shows how to get these specific metadata fields.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_access_metadata():
    scorer = KeywordRelevanceScorer(keywords=["feature"])
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=scorer)
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- BestFirstCrawlingStrategy - Accessing Metadata ---")
        for result in results:
            if result.success:
                url = result.url
                metadata = result.metadata
                depth = metadata.get('depth', 'N/A')
                parent_url = metadata.get('parent_url', 'N/A')
                score = metadata.get('score', 'N/A')
                
                print(f"URL: {url}")
                print(f"  Depth: {depth}")
                print(f"  Parent URL: {parent_url}")
                print(f"  Score: {score:.2f}" if isinstance(score, float) else f"  Score: {score}")
                print("-" * 10)

if __name__ == "__main__":
    asyncio.run(best_first_access_metadata())
```

### 4.13. Example: `BestFirstCrawlingStrategy` - Demonstrating `shutdown()` to stop an ongoing prioritized crawl.

```python
import asyncio
import time
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_demonstrate_shutdown():
    scorer = KeywordRelevanceScorer(keywords=["feature", "core", "example"])
    strategy = BestFirstCrawlingStrategy(
        max_depth=5, # A potentially long crawl
        max_pages=100,
        url_scorer=scorer
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True, 
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        
        print(f"--- BestFirstCrawlingStrategy with shutdown() demonstration ---")
        
        crawl_task = asyncio.create_task(crawler.arun(url=start_url, config=run_config))
        
        await asyncio.sleep(0.1) 
        
        print("Attempting to shut down the BestFirst crawl...")
        await strategy.shutdown() 
        
        results_list = []
        try:
            async for res in await crawl_task:
                results_list.append(res)
                print(f"  Collected result (post-shutdown signal): {res.url} (Score: {res.metadata.get('score', 0.0):.2f})")
        except asyncio.CancelledError:
            print("Crawl task was cancelled.")
        
        print(f"Crawl shut down. Processed {len(results_list)} pages before/during shutdown.")
        assert len(results_list) < 10, "Crawl likely didn't shut down early enough or mock site too small."

if __name__ == "__main__":
    asyncio.run(best_first_demonstrate_shutdown())
```

### 4.14. Example: `BestFirstCrawlingStrategy` - Explaining the effect of `BATCH_SIZE` on `arun_many`.
`BATCH_SIZE` is an internal constant in `bbf_strategy.py` (typically 10). This example explains its role rather than making it directly configurable by the user through the strategy's constructor, as it's an internal implementation detail of how the strategy uses `crawler.arun_many`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

# Note: BATCH_SIZE is internal to BestFirstCrawlingStrategy, usually 10.
# We can't directly set it, but we can explain its effect.

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def best_first_batch_size_effect():
    print("--- Explaining BATCH_SIZE in BestFirstCrawlingStrategy ---")
    print("BestFirstCrawlingStrategy processes URLs in batches for efficiency.")
    print("Internally, it retrieves a batch of highest-priority URLs (typically up to BATCH_SIZE, e.g., 10) from its queue.")
    print("It then calls `crawler.arun_many()` with this batch.")
    print("This means that while URLs are prioritized, the order within a small batch might not be strictly descending by score,")
    print("especially if `stream=True`, as results from `arun_many` can arrive slightly out of strict submission order.")
    print("The overall crawl still heavily favors higher-scored URLs first over many batches.")

    # To simulate observing this, let's run a crawl and see if groups of results are processed.
    scorer = KeywordRelevanceScorer(keywords=["feature", "core", "page1", "page2"])
    strategy = BestFirstCrawlingStrategy(
        max_depth=2, 
        url_scorer=scorer,
        max_pages=6 # Small enough to potentially see batching effects if BATCH_SIZE was smaller
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        
        print("\n--- Crawl Example (max_pages=6) ---")
        results_in_order = []
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                results_in_order.append(result.metadata.get('score',0.0))
                print(f"  Streamed: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}")
        
        # This assertion is hard to make definitively without knowing the exact internal BATCH_SIZE
        # and perfect mock site behavior. The print statements are more illustrative.
        print("\nScores in order of processing:", [f"{s:.2f}" for s in results_in_order])
        print("Observe if there are small groups where order might not be strictly descending due to batch processing.")


if __name__ == "__main__":
    asyncio.run(best_first_batch_size_effect())
```

---
## 5. Configuring Filters (`FilterChain`) for Deep Crawling

Filters allow you to control which URLs are processed during a deep crawl. They are applied *before* a URL is added to the crawl queue (except for the start URL).

### 5.1. `URLPatternFilter`

#### 5.1.1. Example: Using `URLPatternFilter` to allow URLs matching specific patterns (e.g., `/blog/*`).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allow_pattern():
    # Allow only URLs containing '/blog/'
    url_filter = URLPatternFilter(patterns=["*/blog/*"])
    filter_chain = FilterChain(filters=[url_filter])
    
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- URLPatternFilter: Allowing '*/blog/*' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url} (Depth: {r.metadata.get('depth')})")
            if r.metadata.get('depth', 0) > 0: # Check discovered URLs
                assert "/blog/" in r.url, f"Page {r.url} does not match pattern."
        print("All discovered pages match the allowed pattern.")

if __name__ == "__main__":
    asyncio.run(filter_allow_pattern())
```

#### 5.1.2. Example: Using `URLPatternFilter` to block URLs matching specific patterns (e.g., `*/login/*`, `*/archive/*`).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_block_pattern():
    # Block URLs containing '/login/' or '/archive/'
    url_filter = URLPatternFilter(patterns=["*/login/*", "*/archive/*"], block_list=True)
    filter_chain = FilterChain(filters=[url_filter])
    
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- URLPatternFilter: Blocking '*/login/*' and '*/archive/*' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url} (Depth: {r.metadata.get('depth')})")
            assert "/login/" not in r.url, f"Page {r.url} should have been blocked (login)."
            assert "/archive/" not in r.url, f"Page {r.url} should have been blocked (archive)."
        print("No pages matching blocked patterns were crawled.")

if __name__ == "__main__":
    asyncio.run(filter_block_pattern())
```

#### 5.1.3. Example: `URLPatternFilter` with `case_sensitive=True` vs. `case_sensitive=False`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter
from unittest.mock import patch

# Add a case-specific URL to MOCK_SITE_DATA
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/Page1.html"] = {
    "html_content": "<html><head><title>Page 1 Case Test</title></head><body><p>Content for case test.</p></body></html>",
    "response_headers": {"Content-Type": "text/html"}
}
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] += '<a href="Page1.html">Page 1 Case Test</a>'


@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_pattern_case_sensitivity():
    start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"

    # Case-sensitive: should only match 'page1.html'
    print("\n--- URLPatternFilter: Case Sensitive (Allow '*/page1.html*') ---")
    url_filter_sensitive = URLPatternFilter(patterns=["*/page1.html*"], case_sensitive=True)
    filter_chain_sensitive = FilterChain(filters=[url_filter_sensitive])
    strategy_sensitive = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain_sensitive)
    run_config_sensitive = CrawlerRunConfig(deep_crawl_strategy=strategy_sensitive, cache_mode=CacheMode.BYPASS)
    
    async with AsyncWebCrawler() as crawler:
        results_sensitive = await crawler.arun(url=start_url, config=run_config_sensitive)
        print(f"Crawled {len(results_sensitive)} pages.")
        for r in results_sensitive:
            print(f"  URL: {r.url}")
            if r.metadata.get('depth',0) > 0:
                assert "page1.html" in r.url and "Page1.html" not in r.url, "Case-sensitive filter failed."
    
    # Case-insensitive: should match both 'page1.html' and 'Page1.html'
    print("\n--- URLPatternFilter: Case Insensitive (Allow '*/page1.html*') ---")
    url_filter_insensitive = URLPatternFilter(patterns=["*/page1.html*"], case_sensitive=False)
    filter_chain_insensitive = FilterChain(filters=[url_filter_insensitive])
    strategy_insensitive = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain_insensitive)
    run_config_insensitive = CrawlerRunConfig(deep_crawl_strategy=strategy_insensitive, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        results_insensitive = await crawler.arun(url=start_url, config=run_config_insensitive)
        print(f"Crawled {len(results_insensitive)} pages.")
        found_page1_lower = False
        found_page1_upper = False
        for r in results_insensitive:
            print(f"  URL: {r.url}")
            if "page1.html" in r.url.lower(): # Check lower to catch both
                 if "page1.html" == Path(r.url).name: found_page1_lower = True
                 if "Page1.html" == Path(r.url).name: found_page1_upper = True
        
        assert found_page1_lower and found_page1_upper, "Case-insensitive filter should have matched both cases."

if __name__ == "__main__":
    asyncio.run(filter_pattern_case_sensitivity())
```

### 5.2. `DomainFilter`

#### 5.2.1. Example: Using `DomainFilter` with `allowed_domains` to restrict crawling to a list of specific domains.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, DomainFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allowed_domains():
    # Only crawl within 'docs.crawl4ai.com'
    domain_filter = DomainFilter(allowed_domains=["docs.crawl4ai.com"])
    filter_chain = FilterChain(filters=[domain_filter])
    
    # include_external needs to be True for DomainFilter to even consider other domains for blocking/allowing
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain, include_external=True)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html" # This links to external-site.com
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- DomainFilter: Allowing only 'docs.crawl4ai.com' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url}")
            assert "docs.crawl4ai.com" in r.url, f"Page {r.url} is not from an allowed domain."
        print("All crawled pages are from 'docs.crawl4ai.com'.")

if __name__ == "__main__":
    asyncio.run(filter_allowed_domains())
```

#### 5.2.2. Example: Using `DomainFilter` with `blocked_domains` to avoid crawling certain domains.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, DomainFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_blocked_domains():
    # Block 'external-site.com'
    domain_filter = DomainFilter(blocked_domains=["external-site.com"])
    filter_chain = FilterChain(filters=[domain_filter])
    
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain, include_external=True)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- DomainFilter: Blocking 'external-site.com' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url}")
            assert "external-site.com" not in r.url, f"Page {r.url} from blocked domain was crawled."
        print("No pages from 'external-site.com' were crawled.")

if __name__ == "__main__":
    asyncio.run(filter_blocked_domains())
```

#### 5.2.3. Example: `DomainFilter` configured to allow subdomains (`allow_subdomains=True`).
(Conceptual as MOCK_SITE_DATA doesn't have subdomains for `docs.crawl4ai.com`.)

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, DomainFilter
from unittest.mock import patch

# Imagine MOCK_SITE_DATA also has:
# "https://blog.docs.crawl4ai.com/vibe-examples/post.html": { ... }
# And index.html links to it.

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allow_subdomains():
    domain_filter = DomainFilter(allowed_domains=["docs.crawl4ai.com"], allow_subdomains=True)
    filter_chain = FilterChain(filters=[domain_filter])
    
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain, include_external=True)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- DomainFilter: Allowing subdomains of 'docs.crawl4ai.com' (Conceptual) ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url}")
            # In a real test, you'd check if blog.docs.crawl4ai.com was included
        print("This example is conceptual; for a real test, ensure mock data includes subdomains.")

if __name__ == "__main__":
    asyncio.run(filter_allow_subdomains())
```

#### 5.2.4. Example: `DomainFilter` configured to disallow subdomains (`allow_subdomains=False`).
(Conceptual as MOCK_SITE_DATA doesn't have subdomains for `docs.crawl4ai.com`.)

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, DomainFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_disallow_subdomains():
    domain_filter = DomainFilter(allowed_domains=["docs.crawl4ai.com"], allow_subdomains=False) # Default
    filter_chain = FilterChain(filters=[domain_filter])
    
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain, include_external=True)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- DomainFilter: Disallowing subdomains of 'docs.crawl4ai.com' (Conceptual) ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url}")
            # In a real test, you'd check if blog.docs.crawl4ai.com was NOT included
        print("This example is conceptual; for a real test, ensure mock data includes subdomains to be excluded.")

if __name__ == "__main__":
    asyncio.run(filter_disallow_subdomains())
```

### 5.3. `ContentTypeFilter`

#### 5.3.1. Example: Using `ContentTypeFilter` to allow only `text/html` pages.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, ContentTypeFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allow_html_only():
    content_filter = ContentTypeFilter(allowed_types=["text/html"])
    filter_chain = FilterChain(filters=[content_filter])
    
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # Links to HTML and PDF
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- ContentTypeFilter: Allowing only 'text/html' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            content_type = r.response_headers.get('Content-Type', '')
            print(f"  URL: {r.url}, Content-Type: {content_type}")
            if r.metadata.get('depth', 0) > 0: # Check discovered URLs
                assert "text/html" in content_type, f"Page {r.url} has wrong content type: {content_type}"
        print("All discovered pages are 'text/html'.")

if __name__ == "__main__":
    asyncio.run(filter_allow_html_only())
```

#### 5.3.2. Example: Using `ContentTypeFilter` with multiple `allowed_types` (e.g., `text/html`, `application/json`).
(Conceptual, as MOCK_SITE_DATA only has html/pdf)

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, ContentTypeFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allow_multiple_types():
    content_filter = ContentTypeFilter(allowed_types=["text/html", "application/json"])
    filter_chain = FilterChain(filters=[content_filter])
    
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" 
        # Imagine page1.html also links to a page1_sub3.json
        MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1_sub3.json"] = {
            "html_content": '{"key": "value"}',
            "response_headers": {"Content-Type": "application/json"}
        }
        MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1.html"]["html_content"] += '<a href="page1_sub3.json">JSON Data</a>'


        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- ContentTypeFilter: Allowing 'text/html', 'application/json' ---")
        print(f"Crawled {len(results)} pages.")
        found_json = False
        for r in results:
            content_type = r.response_headers.get('Content-Type', '')
            print(f"  URL: {r.url}, Content-Type: {content_type}")
            if r.metadata.get('depth',0) > 0:
                assert "text/html" in content_type or "application/json" in content_type
            if "application/json" in content_type:
                found_json = True
        assert found_json, "Expected to find a JSON page."
        print("All discovered pages are either 'text/html' or 'application/json'.")
        
        # Clean up mock data
        del MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1_sub3.json"]
        MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1.html"]["html_content"] = MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1.html"]["html_content"].replace('<a href="page1_sub3.json">JSON Data</a>', '')


if __name__ == "__main__":
    asyncio.run(filter_allow_multiple_types())
```

#### 5.3.3. Example: Using `ContentTypeFilter` with `blocked_types` (e.g., blocking `application/pdf`).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, ContentTypeFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_block_pdf():
    content_filter = ContentTypeFilter(blocked_types=["application/pdf"])
    filter_chain = FilterChain(filters=[content_filter])
    
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # Links to HTML and PDF
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- ContentTypeFilter: Blocking 'application/pdf' ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            content_type = r.response_headers.get('Content-Type', '')
            print(f"  URL: {r.url}, Content-Type: {content_type}")
            assert "application/pdf" not in content_type, f"PDF page {r.url} was not blocked."
        print("No 'application/pdf' pages were crawled (beyond start URL if it was PDF).")

if __name__ == "__main__":
    asyncio.run(filter_block_pdf())
```

### 5.4. `URLFilter` (Simple exact match)

#### 5.4.1. Example: `URLFilter` to allow a specific list of exact URLs.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_allow_exact_urls():
    allowed_urls = [
        "https://docs.crawl4ai.com/vibe-examples/page1.html",
        "https://docs.crawl4ai.com/vibe-examples/page1_sub1.html"
    ]
    url_filter = URLFilter(urls=allowed_urls, block_list=False) # Allow list
    filter_chain = FilterChain(filters=[url_filter])
    
    strategy = BFSDeePCrawlStrategy(max_depth=2, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- URLFilter: Allowing specific URLs ---")
        print(f"Crawled {len(results)} pages.")
        crawled_urls = {r.url for r in results}
        # The start URL is always crawled initially, then its links are filtered.
        # So we check that all *other* crawled URLs are in the allowed list.
        for r_url in crawled_urls:
            if r_url != start_url: # Exclude start_url from this assertion
                 assert r_url in allowed_urls, f"URL {r_url} was not in the allowed list."
        print("Only URLs from the allowed list (plus start_url) were crawled.")

if __name__ == "__main__":
    asyncio.run(filter_allow_exact_urls())
```

#### 5.4.2. Example: `URLFilter` to block a specific list of exact URLs.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLFilter
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_block_exact_urls():
    blocked_urls = [
        "https://docs.crawl4ai.com/vibe-examples/page2.html",
        "https://docs.crawl4ai.com/vibe-examples/archive/old_page.html"
    ]
    url_filter = URLFilter(urls=blocked_urls, block_list=True) # Block list
    filter_chain = FilterChain(filters=[url_filter])
    
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- URLFilter: Blocking specific URLs ---")
        print(f"Crawled {len(results)} pages.")
        crawled_urls = {r.url for r in results}
        for blocked_url in blocked_urls:
            assert blocked_url not in crawled_urls, f"URL {blocked_url} should have been blocked."
        print("Blocked URLs were not crawled.")

if __name__ == "__main__":
    asyncio.run(filter_block_exact_urls())
```

### 5.5. `ContentRelevanceFilter`
This filter uses an LLM to determine relevance. The example focuses on setup, as a full run requires an LLM.

#### 5.5.1. Example: Setting up `ContentRelevanceFilter` with target keywords (conceptual, focusing on setup).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, ContentRelevanceFilter, LLMConfig

# This is a conceptual example showing setup.
# A real run would require an LLM provider to be configured.
async def setup_content_relevance_filter():
    print("--- Setting up ContentRelevanceFilter (Conceptual) ---")
    
    # Define keywords and context for relevance
    keywords = ["artificial intelligence", "web crawling", "data extraction"]
    context_query = "Articles related to AI-powered web scraping tools and techniques."

    # Configure LLM (replace with your actual provider and API key)
    llm_config = LLMConfig(provider="openai/gpt-3.5-turbo", api_token="YOUR_OPENAI_API_KEY")
    
    relevance_filter = ContentRelevanceFilter(
        llm_config=llm_config,
        keywords=keywords,
        context_query=context_query,
        threshold=0.6 # Adjust threshold as needed
    )
    filter_chain = FilterChain(filters=[relevance_filter])
    
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    print("ContentRelevanceFilter configured. To run this example:")
    print("1. Replace 'YOUR_OPENAI_API_KEY' with your actual OpenAI API key.")
    print("2. (Optional) Install OpenAI client: pip install openai")
    print("3. Uncomment the crawler execution part below.")

    # # Example of how it would be used (requires actual LLM call)
    # async with AsyncWebCrawler() as crawler:
    #     # Mock or use a real URL that would trigger the LLM
    #     start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" 
    #     print(f"Attempting to crawl {start_url} with ContentRelevanceFilter...")
    #     # results = await crawler.arun(url=start_url, config=run_config)
    #     # print(f"Crawled {len(results)} pages after relevance filtering.")
    #     # for r in results:
    #     #     print(f"  URL: {r.url}, Relevance Score: {r.metadata.get('relevance_score')}")
    print("Conceptual setup complete.")

if __name__ == "__main__":
    asyncio.run(setup_content_relevance_filter())
```

#### 5.5.2. Example: `ContentRelevanceFilter` with a custom `threshold`.

```python
import asyncio
from crawl4ai import ContentRelevanceFilter, LLMConfig

async def content_relevance_custom_threshold():
    print("--- ContentRelevanceFilter with custom threshold (Conceptual Setup) ---")
    llm_config = LLMConfig(provider="openai/gpt-3.5-turbo", api_token="YOUR_OPENAI_API_KEY") # Replace
    
    # A higher threshold means stricter relevance checking
    strict_filter = ContentRelevanceFilter(
        llm_config=llm_config,
        keywords=["specific technical term"],
        threshold=0.8 
    )
    print(f"Strict filter created with threshold: {strict_filter.threshold}")

    # A lower threshold is more lenient
    lenient_filter = ContentRelevanceFilter(
        llm_config=llm_config,
        keywords=["general topic"],
        threshold=0.4
    )
    print(f"Lenient filter created with threshold: {lenient_filter.threshold}")
    print("Note: Actual filtering behavior depends on LLM responses to content.")

if __name__ == "__main__":
    asyncio.run(content_relevance_custom_threshold())
```

### 5.6. `SEOFilter`
This filter checks for common SEO issues. The example is conceptual, focusing on setup.

#### 5.6.1. Example: Basic `SEOFilter` with default SEO checks (conceptual, focusing on setup).

```python
import asyncio
from crawl4ai import SEOFilter

async def setup_basic_seo_filter():
    print("--- Basic SEOFilter with default checks (Conceptual Setup) ---")
    
    # Default checks might include missing title, short meta description, etc.
    seo_filter = SEOFilter() 
    
    print(f"SEOFilter created with default settings:")
    print(f"  Min Title Length: {seo_filter.min_title_length}")
    print(f"  Max Title Length: {seo_filter.max_title_length}")
    print(f"  Min Meta Description Length: {seo_filter.min_meta_description_length}")
    # ... and other default parameters
    print("This filter would be added to a FilterChain and used in a DeepCrawlStrategy.")
    print("It would then check each page against these SEO criteria.")

if __name__ == "__main__":
    asyncio.run(setup_basic_seo_filter())
```

#### 5.6.2. Example: `SEOFilter` configuring specific checks like `min_title_length`, `max_meta_description_length`, or `keyword_in_title_check` (conceptual).

```python
import asyncio
from crawl4ai import SEOFilter

async def setup_custom_seo_filter():
    print("--- SEOFilter with custom checks (Conceptual Setup) ---")
    
    custom_seo_filter = SEOFilter(
        min_title_length=20,
        max_meta_description_length=150,
        keyword_in_title_check=True,
        target_keywords_for_seo=["crawl4ai", "web scraping"] # if keyword_in_title_check is True
    )
    
    print(f"Custom SEOFilter created with:")
    print(f"  Min Title Length: {custom_seo_filter.min_title_length}")
    print(f"  Max Meta Description Length: {custom_seo_filter.max_meta_description_length}")
    print(f"  Keyword in Title Check: {custom_seo_filter.keyword_in_title_check}")
    print(f"  Target SEO Keywords: {custom_seo_filter.target_keywords_for_seo}")
    print("This filter would apply these specific criteria during a crawl.")

if __name__ == "__main__":
    asyncio.run(setup_custom_seo_filter())
```

### 5.7. `FilterChain`

#### 5.7.1. Example: Combining `URLPatternFilter` (allow `/products/*`) and `DomainFilter` (only `example.com`) in a `FilterChain`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter, DomainFilter
from unittest.mock import patch

# Add mock data for this scenario
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/products/productA.html"] = {
    "html_content": "<html><title>Product A</title><body>Product A details</body></html>",
    "response_headers": {"Content-Type": "text/html"}
}
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] += '<a href="products/productA.html">Product A</a>'


@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_chain_combination():
    product_filter = URLPatternFilter(patterns=["*/products/*"])
    domain_filter = DomainFilter(allowed_domains=["docs.crawl4ai.com"])
    
    combined_filter_chain = FilterChain(filters=[product_filter, domain_filter])
    
    strategy = BFSDeePCrawlStrategy(max_depth=2, filter_chain=combined_filter_chain, include_external=True)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- FilterChain: URLPatternFilter + DomainFilter ---")
        print(f"Crawled {len(results)} pages.")
        for r in results:
            print(f"  URL: {r.url}")
            if r.metadata.get('depth', 0) > 0: # Discovered URLs
                assert "docs.crawl4ai.com" in r.url, "Domain filter failed."
                assert "/products/" in r.url, "URL pattern filter failed."
        print("All discovered pages are from 'docs.crawl4ai.com' and match '*/products/*'.")
        
        # Clean up mock data
        del MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/products/productA.html"]
        MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] = MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"].replace('<a href="products/productA.html">Product A</a>', '')


if __name__ == "__main__":
    asyncio.run(filter_chain_combination())
```

#### 5.7.2. Example: Using `FilterChain` with `FilterStats` to retrieve and display statistics about filtered URLs.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter, FilterStats
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_chain_with_stats():
    url_filter = URLPatternFilter(patterns=["*/blog/*"], block_list=False) # Allow only blog
    filter_stats = FilterStats() # Create a stats object
    filter_chain = FilterChain(filters=[url_filter], stats=filter_stats) # Pass stats to chain
    
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- FilterChain with FilterStats ---")
        print(f"Crawled {len(results)} pages.")
        
        print("\nFilter Statistics:")
        print(f"  Total URLs considered by filters: {filter_stats.total_considered}")
        print(f"  Total URLs allowed: {filter_stats.total_allowed}")
        print(f"  Total URLs blocked: {filter_stats.total_blocked}")
        
        # Based on MOCK_SITE_DATA, index links to one /blog/ page and several non-blog pages.
        # Start URL itself is not subject to filter_chain in this strategy logic.
        # Links from start URL: page1, page2, external, archive, blog, login
        # Only /blog/post1.html should pass. 5 should be blocked.
        assert filter_stats.total_considered >= 5 # Links from index.html
        assert filter_stats.total_allowed >= 1    # /blog/post1.html
        assert filter_stats.total_blocked >= 4    # page1, page2, external (if not implicitly blocked), archive, login

if __name__ == "__main__":
    asyncio.run(filter_chain_with_stats())
```

#### 5.7.3. Example: `FilterChain` with `allow_empty=True` vs `allow_empty=False`.
This shows how `allow_empty` on the `FilterChain` itself works. If `allow_empty=True` (default), an empty chain allows all URLs. If `False`, an empty chain blocks all.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def filter_chain_allow_empty():
    start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
    
    # Case 1: allow_empty=True (default) - empty chain allows all
    print("\n--- FilterChain with allow_empty=True (empty chain) ---")
    empty_chain_allow = FilterChain(filters=[], allow_empty=True)
    strategy_allow = BFSDeePCrawlStrategy(max_depth=1, filter_chain=empty_chain_allow)
    run_config_allow = CrawlerRunConfig(deep_crawl_strategy=strategy_allow, cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler() as crawler:
        results_allow = await crawler.arun(url=start_url, config=run_config_allow)
        print(f"Crawled {len(results_allow)} pages. (Expected > 1 as all links from index should be allowed)")
        assert len(results_allow) > 1 # Start URL + its links

    # Case 2: allow_empty=False - empty chain blocks all (except start URL)
    print("\n--- FilterChain with allow_empty=False (empty chain) ---")
    empty_chain_block = FilterChain(filters=[], allow_empty=False)
    strategy_block = BFSDeePCrawlStrategy(max_depth=1, filter_chain=empty_chain_block)
    run_config_block = CrawlerRunConfig(deep_crawl_strategy=strategy_block, cache_mode=CacheMode.BYPASS)
    async with AsyncWebCrawler() as crawler:
        results_block = await crawler.arun(url=start_url, config=run_config_block)
        print(f"Crawled {len(results_block)} pages. (Expected 1, only start URL)")
        assert len(results_block) == 1 # Only start_url, as all its links are blocked by empty chain


if __name__ == "__main__":
    asyncio.run(filter_chain_allow_empty())
```

---
## 6. Configuring Scorers (`URLScorer`) for `BestFirstCrawlingStrategy`

Scorers are used by `BestFirstCrawlingStrategy` to prioritize URLs in its crawl queue.

### 6.1. `KeywordRelevanceScorer`

#### 6.1.1. Example: `KeywordRelevanceScorer` with a list of keywords and default weight.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_keyword_default_weight():
    scorer = KeywordRelevanceScorer(keywords=["feature", "core concepts"]) # Default weight is 1.0
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=scorer, max_pages=4)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- KeywordRelevanceScorer with default weight ---")
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun("https://docs.crawl4ai.com/vibe-examples/index.html", config=run_config):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}")
    print("Pages containing 'feature' or 'core concepts' in their URL should have higher scores.")

if __name__ == "__main__":
    asyncio.run(scorer_keyword_default_weight())
```

#### 6.1.2. Example: `KeywordRelevanceScorer` adjusting the `weight` parameter to influence its importance.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer, PathDepthScorer, CompositeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_keyword_custom_weight():
    # High weight for keywords, low for path depth
    keyword_scorer = KeywordRelevanceScorer(keywords=["feature"], weight=2.0) 
    path_scorer = PathDepthScorer(weight=0.1, higher_score_is_better=False) # Less penalty
    
    composite_scorer = CompositeScorer(scorers=[keyword_scorer, path_scorer])
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=composite_scorer, max_pages=4)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- KeywordRelevanceScorer with adjusted weight (weight=2.0) in CompositeScorer ---")
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun("https://docs.crawl4ai.com/vibe-examples/index.html", config=run_config):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}")
    print("Keyword relevance should have a stronger impact on the final score.")

if __name__ == "__main__":
    asyncio.run(scorer_keyword_custom_weight())
```

#### 6.1.3. Example: `KeywordRelevanceScorer` with `case_sensitive=True`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

# Modify mock data to have case-specific keywords in URLs
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/FEATUREpage.html"] = {
    "html_content": "<html><title>FEATURE Page</title><body>Uppercase FEATURE</body></html>",
    "response_headers": {"Content-Type": "text/html"}
}
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] += '<a href="FEATUREpage.html">FEATURE Page</a>'


@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_keyword_case_sensitive():
    # Case-sensitive: will only score URLs with 'feature' (lowercase)
    scorer_sensitive = KeywordRelevanceScorer(keywords=["feature"], case_sensitive=True)
    strategy_sensitive = BestFirstCrawlingStrategy(max_depth=1, url_scorer=scorer_sensitive, max_pages=5)
    run_config_sensitive = CrawlerRunConfig(deep_crawl_strategy=strategy_sensitive, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- KeywordRelevanceScorer with case_sensitive=True (keyword: 'feature') ---")
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun("https://docs.crawl4ai.com/vibe-examples/index.html", config=run_config_sensitive):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}")
                if "FEATUREpage.html" in result.url: # Uppercase 'FEATURE'
                    assert result.metadata.get('score', 0.0) == 0.0, "Uppercase keyword should not be scored."
                elif "page2.html" in result.url: # Contains lowercase 'feature' in title/mock
                     assert result.metadata.get('score', 0.0) > 0.0, "Lowercase keyword should be scored."

    # Clean up mock data
    del MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/FEATUREpage.html"]
    MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] = MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"].replace('<a href="FEATUREpage.html">FEATURE Page</a>', '')


if __name__ == "__main__":
    asyncio.run(scorer_keyword_case_sensitive())
```

### 6.2. `PathDepthScorer`

#### 6.2.1. Example: `PathDepthScorer` with default behavior (penalizing deeper paths).
By default, `PathDepthScorer` gives higher scores to shallower paths (depth 0 > depth 1 > depth 2).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, PathDepthScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_path_depth_default():
    scorer = PathDepthScorer() # Default: higher_score_is_better=True, depth_penalty_factor=0.1
    strategy = BestFirstCrawlingStrategy(max_depth=2, url_scorer=scorer, max_pages=6)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- PathDepthScorer with default behavior (shallower is better) ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        
        depth_scores = {}
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                depth = result.metadata.get('depth')
                score = result.metadata.get('score', 0.0)
                print(f"  URL: {result.url}, Depth: {depth}, Score: {score:.2f}")
                if depth not in depth_scores:
                    depth_scores[depth] = []
                depth_scores[depth].append(score)
        
        if 1 in depth_scores and 2 in depth_scores and depth_scores[1] and depth_scores[2]:
           avg_score_depth1 = sum(depth_scores[1]) / len(depth_scores[1])
           avg_score_depth2 = sum(depth_scores[2]) / len(depth_scores[2])
           print(f"Avg score depth 1: {avg_score_depth1:.2f}, Avg score depth 2: {avg_score_depth2:.2f}")
           assert avg_score_depth1 > avg_score_depth2, "Shallower paths should have higher scores."

if __name__ == "__main__":
    asyncio.run(scorer_path_depth_default())
```

#### 6.2.2. Example: `PathDepthScorer` with custom `depth_penalty_factor`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, PathDepthScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_path_depth_custom_penalty():
    # Higher penalty factor means deeper paths are penalized more severely
    scorer = PathDepthScorer(depth_penalty_factor=0.5, higher_score_is_better=True) 
    strategy = BestFirstCrawlingStrategy(max_depth=2, url_scorer=scorer, max_pages=6)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- PathDepthScorer with custom depth_penalty_factor=0.5 ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        
        depth_scores = {}
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                depth = result.metadata.get('depth')
                score = result.metadata.get('score', 0.0)
                print(f"  URL: {result.url}, Depth: {depth}, Score: {score:.2f}")
                if depth not in depth_scores:
                    depth_scores[depth] = []
                depth_scores[depth].append(score)

        if 1 in depth_scores and 2 in depth_scores and depth_scores[1] and depth_scores[2]:
           avg_score_depth1 = sum(depth_scores[1]) / len(depth_scores[1])
           avg_score_depth2 = sum(depth_scores[2]) / len(depth_scores[2])
           print(f"Avg score depth 1: {avg_score_depth1:.2f}, Avg score depth 2: {avg_score_depth2:.2f}")
           # Expect a larger difference due to higher penalty
           assert (avg_score_depth1 - avg_score_depth2) > 0.05, "Higher penalty factor should result in a larger score drop for deeper paths."


if __name__ == "__main__":
    asyncio.run(scorer_path_depth_custom_penalty())
```

#### 6.2.3. Example: `PathDepthScorer` with `higher_score_is_better=False` (to favor deeper paths).

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, PathDepthScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_path_depth_favor_deep():
    # Now, deeper paths will get higher (less negative or more positive) scores
    scorer = PathDepthScorer(higher_score_is_better=False) 
    strategy = BestFirstCrawlingStrategy(max_depth=2, url_scorer=scorer, max_pages=6)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- PathDepthScorer with higher_score_is_better=False (favoring deeper paths) ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        
        depth_scores = {}
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                depth = result.metadata.get('depth')
                score = result.metadata.get('score', 0.0)
                print(f"  URL: {result.url}, Depth: {depth}, Score: {score:.2f}")
                if depth not in depth_scores:
                    depth_scores[depth] = []
                depth_scores[depth].append(score)
        
        if 1 in depth_scores and 2 in depth_scores and depth_scores[1] and depth_scores[2]:
           avg_score_depth1 = sum(depth_scores[1]) / len(depth_scores[1])
           avg_score_depth2 = sum(depth_scores[2]) / len(depth_scores[2])
           print(f"Avg score depth 1: {avg_score_depth1:.2f}, Avg score depth 2: {avg_score_depth2:.2f}")
           assert avg_score_depth2 > avg_score_depth1, "Deeper paths should have higher scores with higher_score_is_better=False."

if __name__ == "__main__":
    asyncio.run(scorer_path_depth_favor_deep())
```

### 6.3. `ContentTypeScorer`

#### 6.3.1. Example: `ContentTypeScorer` prioritizing `text/html` and penalizing `application/pdf`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, ContentTypeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_content_type_html_vs_pdf():
    scorer = ContentTypeScorer(
        content_type_weights={"text/html": 1.0, "application/pdf": -1.0, "image/jpeg": 0.2}
    )
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=scorer, max_pages=5)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- ContentTypeScorer (HTML: 1.0, PDF: -1.0) ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # Links to HTML and PDF
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                content_type = result.response_headers.get('Content-Type', 'unknown')
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Type: {content_type}")

if __name__ == "__main__":
    asyncio.run(scorer_content_type_html_vs_pdf())
```

#### 6.3.2. Example: `ContentTypeScorer` with custom `content_type_weights`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, ContentTypeScorer
from unittest.mock import patch

# Add a JSON page to mock data
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/data.json"] = {
    "html_content": '{"data": "sample"}', "response_headers": {"Content-Type": "application/json"}
}
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] += '<a href="data.json">JSON Data</a>'


@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def scorer_content_type_custom_weights():
    scorer = ContentTypeScorer(
        content_type_weights={
            "application/json": 2.0, # Highly prioritize JSON
            "text/html": 0.5,
            "application/pdf": -2.0 # Strongly penalize PDF
        }
    )
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=scorer, max_pages=5)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- ContentTypeScorer with custom weights (JSON: 2.0, HTML: 0.5, PDF: -2.0) ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/page1.html" # Links to HTML, PDF. Index links to JSON.
        
        # We'll crawl index to ensure JSON is discoverable
        async for result in await crawler.arun("https://docs.crawl4ai.com/vibe-examples/index.html", config=run_config):
            if result.success:
                content_type = result.response_headers.get('Content-Type', 'unknown')
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Type: {content_type}")
    
    del MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/data.json"]
    MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] = MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"].replace('<a href="data.json">JSON Data</a>', '')

if __name__ == "__main__":
    asyncio.run(scorer_content_type_custom_weights())
```

### 6.4. `DomainAuthorityScorer`

#### 6.4.1. Example: Setting up `DomainAuthorityScorer` (conceptual, as DA often requires an external API or dataset).
This example shows how to instantiate and potentially use it, but actual scoring depends on external data.

```python
import asyncio
from crawl4ai import DomainAuthorityScorer

async def setup_domain_authority_scorer():
    print("--- DomainAuthorityScorer (Conceptual Setup) ---")
    
    # Conceptual: imagine you have a way to get DA scores
    # da_scores = {"example.com": 90, "anotherexample.net": 70}
    # scorer = DomainAuthorityScorer(domain_authority_map=da_scores, weight=1.5)
    
    # For this example, we'll just instantiate it
    scorer = DomainAuthorityScorer(weight=1.5)
    print(f"DomainAuthorityScorer created with weight: {scorer.weight}")
    print("To use this scorer effectively, you'd need a 'domain_authority_map' or a way to fetch DA scores.")
    print("Example URL score (conceptual): ", scorer.score("https://highly-authoritative-site.com/page"))

if __name__ == "__main__":
    asyncio.run(setup_domain_authority_scorer())
```

### 6.5. `FreshnessScorer`

#### 6.5.1. Example: Setting up `FreshnessScorer` (conceptual, as freshness often requires parsing dates from content or headers).
This example focuses on instantiation. Actual scoring would need date extraction.

```python
import asyncio
from crawl4ai import FreshnessScorer
from datetime import datetime, timedelta

async def setup_freshness_scorer():
    print("--- FreshnessScorer (Conceptual Setup) ---")
    
    # Conceptual: the scorer would need a way to get the publication date of a URL
    # For this example, we'll just instantiate it
    scorer = FreshnessScorer(
        max_age_days=30,      # Pages older than 30 days get lower scores
        date_penalty_factor=0.1 # How much to penalize per day older
    )
    print(f"FreshnessScorer created with max_age_days: {scorer.max_age_days}")
    print("To use this, the crawling process or a pre-processor would need to extract and provide publication dates for URLs.")
    
    # Conceptual scoring:
    # recent_date = datetime.now() - timedelta(days=5)
    # old_date = datetime.now() - timedelta(days=60)
    # print(f"Score for recent page (mock date): {scorer.score('https://example.com/recent', publication_date=recent_date)}")
    # print(f"Score for old page (mock date): {scorer.score('https://example.com/old', publication_date=old_date)}")


if __name__ == "__main__":
    asyncio.run(setup_freshness_scorer())
```

### 6.6. `CompositeScorer`

#### 6.6.1. Example: Combining `KeywordRelevanceScorer` and `PathDepthScorer` using `CompositeScorer` with equal weights.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from crawl4ai import KeywordRelevanceScorer, PathDepthScorer, CompositeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def composite_scorer_equal_weights():
    keyword_scorer = KeywordRelevanceScorer(keywords=["feature"]) # Default weight 1.0
    path_scorer = PathDepthScorer(higher_score_is_better=False)  # Default weight 1.0, penalizes depth
    
    # Equal weighting by default if weights list not provided or all weights are same
    composite_scorer = CompositeScorer(scorers=[keyword_scorer, path_scorer])
    
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=composite_scorer, max_pages=5)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- CompositeScorer with equal weights for Keyword and PathDepth ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Depth: {result.metadata.get('depth')}")
    print("Scores are an equal combination of keyword relevance and path depth penalty.")

if __name__ == "__main__":
    asyncio.run(composite_scorer_equal_weights())
```

#### 6.6.2. Example: `CompositeScorer` assigning different `weights` to prioritize one scorer over another.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from crawl4ai import KeywordRelevanceScorer, PathDepthScorer, CompositeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def composite_scorer_different_weights():
    # Keyword relevance is more important
    keyword_scorer = KeywordRelevanceScorer(keywords=["feature"]) 
    path_scorer = PathDepthScorer(higher_score_is_better=False)
    
    composite_scorer = CompositeScorer(
        scorers=[keyword_scorer, path_scorer],
        weights=[0.8, 0.2] # Keyword scorer has 80% influence, PathDepth 20%
    )
    
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=composite_scorer, max_pages=5)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- CompositeScorer with different weights (Keyword: 0.8, PathDepth: 0.2) ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Depth: {result.metadata.get('depth')}")
    print("Keyword relevance should more heavily influence scores.")

if __name__ == "__main__":
    asyncio.run(composite_scorer_different_weights())
```

#### 6.6.3. Example: Nesting `CompositeScorer` for more complex scoring logic.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy
from crawl4ai import KeywordRelevanceScorer, PathDepthScorer, ContentTypeScorer, CompositeScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def composite_scorer_nesting():
    keyword_scorer = KeywordRelevanceScorer(keywords=["feature"])
    path_scorer = PathDepthScorer(higher_score_is_better=False)
    content_type_scorer = ContentTypeScorer(content_type_weights={"text/html": 1.0, "application/pdf": -1.0})

    # First level composite: keyword and path
    relevance_and_structure_scorer = CompositeScorer(
        scorers=[keyword_scorer, path_scorer],
        weights=[0.7, 0.3]
    )

    # Second level composite: combine above with content type
    final_scorer = CompositeScorer(
        scorers=[relevance_and_structure_scorer, content_type_scorer],
        weights=[0.8, 0.2] # Relevance/structure is 80%, content type 20%
    )
    
    strategy = BestFirstCrawlingStrategy(max_depth=1, url_scorer=final_scorer, max_pages=5)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- Nested CompositeScorer ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                 print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}, Depth: {result.metadata.get('depth')}, Type: {result.response_headers.get('Content-Type')}")
    print("Scores reflect a nested combination of keyword, path, and content type.")

if __name__ == "__main__":
    asyncio.run(composite_scorer_nesting())
```

---
## 7. General Deep Crawl Configuration and Usage

### 7.1. Example: Deep crawling a site that relies heavily on JavaScript for link generation.
This example demonstrates the setup. A real JS-heavy site would be needed for full verification.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, BrowserConfig
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_js_heavy_site():
    # BrowserConfig enables JS by default.
    # For very JS-heavy sites, ensure headless=False if debugging, and consider timeouts.
    browser_cfg = BrowserConfig(headless=True) # Keep headless for automated tests

    # CrawlerRunConfig might need adjustments for JS execution time
    run_cfg = CrawlerRunConfig(
        page_timeout=30000, # 30 seconds, might need more for complex JS
        # js_code can be used to trigger actions if needed before link discovery
        # js_code="window.scrollTo(0, document.body.scrollHeight);", # Example to scroll
        deep_crawl_strategy=BFSDeePCrawlStrategy(max_depth=1, max_pages=3),
        cache_mode=CacheMode.BYPASS
    )

    print("--- Deep Crawling a JS-Heavy Site (Conceptual: JS execution is enabled by default) ---")
    # Using index.html which has a JS-triggered link via onclick
    start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        results = await crawler.arun(url=start_url, config=run_cfg)
        
        print(f"Crawled {len(results)} pages.")
        js_link_found = False
        for result in results:
            print(f"  URL: {result.url}")
            if "js_page.html" in result.url:
                js_link_found = True
        
        # This assertion relies on the MockAsyncWebCrawler's _fetch_page
        # correctly parsing links from html_content, even if added by mock JS.
        # A more robust test would involve Playwright's own JS execution.
        # For now, we assume the mock crawler finds links from the final HTML state.
        # To truly test JS-driven links, one would need to modify MockAsyncWebCrawler
        # to simulate JS execution or use a real browser test.
        # This example mainly shows the configuration for enabling JS.
        print("Note: True JS-link discovery depends on Playwright's execution within the crawler.")
        print("The mock crawler simulates link finding from final HTML state.")
        # assert js_link_found, "JS-generated link was not found. Mock might need adjustment or real browser test."


if __name__ == "__main__":
    asyncio.run(deep_crawl_js_heavy_site())
```

### 7.2. Example: How `CrawlerRunConfig` parameters (e.g., `page_timeout`) and `BrowserConfig` (e.g., `user_agent`, `proxy_config`) affect underlying page fetches.
This shows how `BrowserConfig` (passed to `AsyncWebCrawler`) and `CrawlerRunConfig` (passed to `arun`) influence individual page fetches.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, BrowserConfig, ProxyConfig
from unittest.mock import patch

# Mocking a proxy server check - in reality, you'd use a real proxy
async def mock_check_ip_via_proxy(url, config):
    # This function would normally make a request through the proxy
    # and return the perceived IP. For mock, we'll just simulate.
    if config and config.proxy_config and config.proxy_config.server == "http://mockproxy.com:8080":
        return "1.2.3.4" # Mocked IP if proxy is used
    return "9.8.7.6" # Mocked direct IP

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_with_configs():
    browser_cfg = BrowserConfig(
        user_agent="MyCustomDeepCrawler/1.0",
        proxy_config=ProxyConfig(server="http://mockproxy.com:8080") # This should be used by crawler
    )
    
    # For deep crawl, the page_timeout in CrawlerRunConfig applies to each page fetch
    run_cfg = CrawlerRunConfig(
        page_timeout=15000, # 15s timeout for each page in the deep crawl
        deep_crawl_strategy=BFSDeePCrawlStrategy(max_depth=0), # Just the start URL
        cache_mode=CacheMode.BYPASS
    )

    print("--- Deep Crawl with Custom Browser & Run Configs ---")
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        # The crawler instance now has the browser_cfg settings.
        # We expect its internal page fetches to use these.
        
        # We'd need to inspect logs or mock `crawler.strategy._fetch_page` to truly verify user_agent/proxy.
        # For this example, we'll conceptually check based on setup.
        print(f"Browser User-Agent set to: {crawler.browser_config.user_agent}")
        if crawler.browser_config.proxy_config:
            print(f"Browser Proxy set to: {crawler.browser_config.proxy_config.server}")
        
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_cfg)
        
        if results and results[0].success:
            print(f"Crawled {results[0].url} successfully with page_timeout={run_cfg.page_timeout}ms")
            # In a real scenario with a proxy, you'd verify the source IP.
            # For mock:
            # perceived_ip = await mock_check_ip_via_proxy(start_url, browser_cfg) 
            # print(f"Perceived IP (mocked): {perceived_ip}")
            # assert perceived_ip == "1.2.3.4" # Assuming proxy was used
        else:
            print(f"Crawl failed for {start_url}")

if __name__ == "__main__":
    asyncio.run(deep_crawl_with_configs())
```

### 7.3. Example: Iterating through deep crawl results and handling cases where some pages failed to crawl or were filtered out.
A robust deep crawl should handle partial failures gracefully.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain, URLPatternFilter
from unittest.mock import patch

# Add a URL that will "fail" in our mock
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/failing_page.html"] = {
    "html_content": None, # Simulate failure by not providing content
    "success": False,
    "status_code": 500,
    "error_message": "Mock Server Error"
}
MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] += '<a href="failing_page.html">Failing Page</a>'


@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_handling_failures():
    # Filter out '/archive/' pages, and one page will fail
    url_filter = URLPatternFilter(patterns=["*/archive/*"], block_list=True)
    filter_chain = FilterChain(filters=[url_filter])
    
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"--- Deep Crawl - Handling Failures and Filtered Pages ---")
        successful_pages = 0
        failed_pages = 0
        
        for result in results:
            if result.success:
                successful_pages += 1
                print(f"  SUCCESS: {result.url} (Depth: {result.metadata.get('depth')})")
                assert "/archive/" not in result.url
            else:
                failed_pages += 1
                print(f"  FAILURE: {result.url} (Error: {result.error_message}, Status: {result.status_code})")
        
        print(f"\nTotal Successful: {successful_pages}, Total Failed/Filtered Out by crawler: {failed_pages}")
        # Start URL + index links (page1, page2, external, blog, login, failing) = 7 initial candidates
        # - external might be skipped by default include_external=False (depends on strategy)
        # - /archive/ is filtered by URLPatternFilter
        # - failing_page.html will fail
        # So, we expect start_url + page1, page2, blog, login. Failing page is in results but success=False.
        # The number of results includes the start_url and pages that were attempted.
        # Filters apply to links *discovered* from a page.
        
        # One page (/archive/old_page.html) should be filtered by the filter chain.
        # One page (failing_page.html) should be in results but with success=False.
        assert any("failing_page.html" in r.url and not r.success for r in results)
        assert not any("/archive/" in r.url for r in results)

    # Clean up mock data
    del MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/failing_page.html"]
    MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"] = MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/index.html"]["html_content"].replace('<a href="failing_page.html">Failing Page</a>', '')

if __name__ == "__main__":
    asyncio.run(deep_crawl_handling_failures())
```

### 7.4. Example: Using a custom `logger` instance passed to a `DeepCrawlStrategy`.

```python
import asyncio
import logging
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, AsyncLogger
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_custom_logger():
    # Setup a custom logger
    custom_logger = AsyncLogger(log_file="custom_deep_crawl.log", name="MyDeepCrawler", level="DEBUG")
    
    strategy = BFSDeePCrawlStrategy(max_depth=0, logger=custom_logger) # Pass logger to strategy
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    print("--- Deep Crawl with Custom Logger ---")
    async with AsyncWebCrawler() as crawler: # Main crawler logger can be default
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        await crawler.arun(url=start_url, config=run_config)
        
    print("Crawl complete. Check 'custom_deep_crawl.log' for logs from the strategy.")
    # You can verify the log file content here if needed
    # e.g., with open("custom_deep_crawl.log", "r") as f: assert "MyDeepCrawler" in f.read()
    # For this example, just visual confirmation is sufficient.

if __name__ == "__main__":
    asyncio.run(deep_crawl_custom_logger())
```

### 7.5. Example: Deep crawling starting from a local HTML file that contains links to other local files or web URLs.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch
from pathlib import Path
import os

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_from_local_file():
    # Ensure the mock local files exist for the test
    local_index_path = Path(os.getcwd()) / "test_local_index.html"
    local_page1_path = Path(os.getcwd()) / "test_local_page1.html"
    
    # If not created by preamble, create them
    if not local_index_path.exists():
        local_index_path.write_text(MOCK_SITE_DATA[f"file://{local_index_path}"]["html_content"])
    if not local_page1_path.exists():
        local_page1_path.write_text(MOCK_SITE_DATA[f"file://{local_page1_path}"]["html_content"])

    start_file_url = f"file://{local_index_path.resolve()}"
    
    strategy = BFSDeePCrawlStrategy(max_depth=1, include_external=True) # Allow following to web URLs
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    print(f"--- Deep Crawling from Local File: {start_file_url} ---")
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(url=start_file_url, config=run_config)
        
        print(f"Crawled {len(results)} pages.")
        found_local_link = False
        found_web_link = False
        for result in results:
            print(f"  URL: {result.url}, Depth: {result.metadata.get('depth')}")
            if result.url == f"file://{local_page1_path.resolve()}":
                found_local_link = True
            if result.url == "https://docs.crawl4ai.com/vibe-examples/index.html":
                found_web_link = True
        
        assert found_local_link, "Did not follow local file link."
        assert found_web_link, "Did not follow web link from local file."
    
    # Clean up dummy files
    if local_index_path.exists(): os.remove(local_index_path)
    if local_page1_path.exists(): os.remove(local_page1_path)


if __name__ == "__main__":
    asyncio.run(deep_crawl_from_local_file())
```

### 7.6. Example: Comparing outputs from `BFSDeePCrawlStrategy`, `DFSDeePCrawlStrategy`, and `BestFirstCrawlingStrategy`.
This example runs all three main strategies with similar settings to highlight differences in traversal and results.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai import BFSDeePCrawlStrategy, DFSDeePCrawlStrategy, BestFirstCrawlingStrategy, KeywordRelevanceScorer
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def compare_deep_crawl_strategies():
    start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
    max_depth = 2
    max_pages = 7 # Keep it manageable for comparison
    
    common_config_params = {
        "max_depth": max_depth,
        "max_pages": max_pages,
        "include_external": False, # Keep it simple for comparison
    }
    
    scorer = KeywordRelevanceScorer(keywords=["feature", "core"])

    strategies_to_compare = {
        "BFS": BFSDeePCrawlStrategy(**common_config_params),
        "DFS": DFSDeePCrawlStrategy(**common_config_params),
        "Best-First": BestFirstCrawlingStrategy(**common_config_params, url_scorer=scorer)
    }

    print(f"--- Comparing Deep Crawl Strategies (max_depth={max_depth}, max_pages={max_pages}) ---")

    async with AsyncWebCrawler() as crawler:
        for name, strategy_instance in strategies_to_compare.items():
            print(f"\n-- Running {name} Strategy --")
            run_config = CrawlerRunConfig(
                deep_crawl_strategy=strategy_instance,
                cache_mode=CacheMode.BYPASS,
                stream=False # Batch for easier comparison of final set
            )
            
            start_time = time.perf_counter()
            results = await crawler.arun(url=start_url, config=run_config)
            duration = time.perf_counter() - start_time
            
            print(f"  {name} crawled {len(results)} pages in {duration:.2f}s.")
            # Sort by depth then URL for consistent output for BFS/DFS
            # For Best-First, sort by score (desc) then depth then URL
            if name == "Best-First":
                 sorted_results = sorted(results, key=lambda r: (r.metadata.get('score', 0.0), -r.metadata.get('depth', 0), r.url), reverse=True)
            else:
                 sorted_results = sorted(results, key=lambda r: (r.metadata.get('depth', 0), r.url))


            for i, r in enumerate(sorted_results):
                if i < 5 or i > len(sorted_results) - 3 : # Show first 5 and last 2
                    score_str = f", Score: {r.metadata.get('score', 0.0):.2f}" if name == "Best-First" else ""
                    print(f"    URL: {r.url} (Depth: {r.metadata.get('depth')}{score_str})")
                elif i == 5:
                    print(f"    ... ({len(sorted_results) - 5 -2 } more results) ...")
            print("-" * 30)

if __name__ == "__main__":
    asyncio.run(compare_deep_crawl_strategies())
```

---
## 8. Advanced Scenarios & Customization

### 8.1. Example: Implementing a custom `DeepCrawlStrategy` by subclassing `DeepCrawlStrategy`.
This provides a skeleton for creating your own crawl logic.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, DeepCrawlStrategy, CrawlResult
from typing import List, Set, Dict, AsyncGenerator, Tuple
from unittest.mock import patch

class MyCustomDeepCrawlStrategy(DeepCrawlStrategy):
    def __init__(self, max_depth=1, **kwargs):
        self.max_depth = max_depth
        # Potentially other custom init params
        super().__init__(**kwargs) # Pass along other kwargs if base class uses them
        print("MyCustomDeepCrawlStrategy Initialized")

    async def _arun_batch(self, start_url: str, crawler: AsyncWebCrawler, config: CrawlerRunConfig) -> List[CrawlResult]:
        print(f"[Custom Strategy] _arun_batch called for: {start_url}")
        # Implement batch crawling logic (e.g., BFS-like)
        # This is a simplified version. A real one needs queue, visited set, depth tracking etc.
        results = []
        initial_result_container = await crawler.arun(url=start_url, config=config.clone(deep_crawl_strategy=None))
        initial_result = initial_result_container[0] # arun returns a list
        
        if not initial_result.success: return [initial_result]
        results.append(initial_result)
        
        if self.max_depth > 0 and initial_result.links.get("internal"):
            for link_info in initial_result.links["internal"][:2]: # Crawl first 2 internal links
                link_url = link_info["href"]
                # Pass metadata for depth and parent
                link_config = config.clone(deep_crawl_strategy=None)
                
                # In a real strategy, you'd manage metadata directly or pass it for crawler.arun
                # For this mock, we simplify as crawler.arun normally doesn't take depth/parent for single page
                print(f"  [Custom Strategy] Crawling linked URL: {link_url} at depth 1")
                linked_result_container = await crawler.arun(url=link_url, config=link_config)
                linked_result = linked_result_container[0]
                # Manually add metadata for this example
                if linked_result.metadata is None: linked_result.metadata = {}
                linked_result.metadata['depth'] = 1
                linked_result.metadata['parent_url'] = start_url
                results.append(linked_result)
        return results

    async def _arun_stream(self, start_url: str, crawler: AsyncWebCrawler, config: CrawlerRunConfig) -> AsyncGenerator[CrawlResult, None]:
        print(f"[Custom Strategy] _arun_stream called for: {start_url}")
        # Implement streaming crawling logic
        # Simplified: yields results from a batch-like process for this example
        batch_results = await self._arun_batch(start_url, crawler, config)
        for result in batch_results:
            yield result
            
    async def can_process_url(self, url: str, depth: int) -> bool:
        # Example: only process URLs not containing "archive" and within max_depth
        print(f"[Custom Strategy] can_process_url called for: {url}, depth: {depth}")
        if "archive" in url:
            return False
        return depth <= self.max_depth

    async def link_discovery(
        self, result: CrawlResult, source_url: str, current_depth: int, 
        visited: Set[str], next_level: List[Tuple[str, str]], depths: Dict[str, int]
    ) -> None:
        # This method is crucial for discovering and queuing new links.
        # The base class might have a default implementation, or you might need to call
        # crawler.arun to get links if result.links is not populated.
        # For this example, we'll assume result.links is populated by the crawler.
        print(f"[Custom Strategy] link_discovery for: {source_url} at depth {current_depth}")
        new_depth = current_depth + 1
        if new_depth > self.max_depth:
            return

        for link_info in result.links.get("internal", [])[:3]: # Limit for example
            link_url = link_info["href"]
            if link_url not in visited and await self.can_process_url(link_url, new_depth):
                next_level.append((link_url, source_url)) # (url, parent_url)
                depths[link_url] = new_depth
                print(f"  [Custom Strategy] Discovered and added to queue: {link_url}")
    
    async def shutdown(self):
        print("[Custom Strategy] Shutdown called.")
        # Implement any cleanup or signal to stop crawling loops


@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def custom_deep_crawl_strategy_example():
    custom_strategy = MyCustomDeepCrawlStrategy(max_depth=1)
    run_config = CrawlerRunConfig(deep_crawl_strategy=custom_strategy, cache_mode=CacheMode.BYPASS)

    print("--- Using Custom DeepCrawlStrategy ---")
    async with AsyncWebCrawler() as crawler: # This will be MockAsyncWebCrawler
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"\nCustom strategy crawled {len(results)} pages:")
        for r in results:
            print(f"  URL: {r.url}, Success: {r.success}, Depth: {r.metadata.get('depth') if r.metadata else 'N/A'}")

if __name__ == "__main__":
    asyncio.run(custom_deep_crawl_strategy_example())
```

### 8.2. Example: Implementing a custom `URLFilter`.
`URLFilter` itself is a concrete class, but you can create custom logic by making a callable class or function that adheres to the expected filter signature `(url: str) -> bool`. For more complex stateful filters, subclassing a base might be an option if one is provided or creating your own structure.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, FilterChain
from unittest.mock import patch

class MyCustomURLFilter:
    def __init__(self, forbidden_keyword: str):
        self.forbidden_keyword = forbidden_keyword.lower()
        print(f"MyCustomURLFilter initialized to block URLs with '{self.forbidden_keyword}'")

    async def __call__(self, url: str) -> bool: # Filters must be async
        """Return True if URL should be allowed, False if blocked."""
        if self.forbidden_keyword in url.lower():
            print(f"[CustomFilter] Blocking URL: {url} (contains '{self.forbidden_keyword}')")
            return False # Block if keyword found
        print(f"[CustomFilter] Allowing URL: {url}")
        return True # Allow otherwise

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def custom_url_filter_example():
    custom_filter = MyCustomURLFilter(forbidden_keyword="archive")
    filter_chain = FilterChain(filters=[custom_filter])
    
    strategy = BFSDeePCrawlStrategy(max_depth=1, filter_chain=filter_chain)
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS)

    print("--- Using Custom URLFilter (blocking 'archive') ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"\nCustom filter crawl resulted in {len(results)} pages:")
        for r in results:
            print(f"  URL: {r.url}")
            assert "archive" not in r.url.lower(), f"Custom filter failed to block {r.url}"
        print("Successfully blocked URLs containing 'archive'.")

if __name__ == "__main__":
    asyncio.run(custom_url_filter_example())
```

### 8.3. Example: Implementing a custom `URLScorer` for `BestFirstCrawlingStrategy`.
Subclass `URLScorer` and implement the `score` method.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BestFirstCrawlingStrategy, URLScorer
from urllib.parse import urlparse
from unittest.mock import patch

class MyCustomURLScorer(URLScorer):
    def __init__(self, preferred_domain: str, weight: float = 1.0):
        super().__init__(weight)
        self.preferred_domain = preferred_domain
        print(f"MyCustomURLScorer initialized, preferring domain: {self.preferred_domain}")

    def score(self, url: str, **kwargs) -> float:
        """Scores URL based on whether it matches the preferred domain."""
        parsed_url = urlparse(url)
        score = 0.0
        if parsed_url.netloc == self.preferred_domain:
            score = 1.0 * self.weight
            print(f"[CustomScorer] URL {url} matches preferred domain. Score: {score}")
        else:
            score = 0.1 * self.weight # Lower score for other domains
            print(f"[CustomScorer] URL {url} does NOT match preferred domain. Score: {score}")
        return score

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def custom_url_scorer_example():
    custom_scorer = MyCustomURLScorer(preferred_domain="docs.crawl4ai.com", weight=2.0)
    
    strategy = BestFirstCrawlingStrategy(
        max_depth=1, 
        url_scorer=custom_scorer,
        include_external=True, # To allow scoring external domains differently
        max_pages=5
    )
    run_config = CrawlerRunConfig(deep_crawl_strategy=strategy, cache_mode=CacheMode.BYPASS, stream=True)

    print("--- Using Custom URLScorer (preferring 'docs.crawl4ai.com') ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        async for result in await crawler.arun(url=start_url, config=run_config):
            if result.success:
                print(f"  URL: {result.url}, Score: {result.metadata.get('score', 0.0):.2f}")
    print("Pages from 'docs.crawl4ai.com' should generally have higher scores.")

if __name__ == "__main__":
    asyncio.run(custom_url_scorer_example())
```

### 8.4. Example: Deep crawling a site with very large number of pages efficiently using `max_pages` and streaming.
This combines `max_pages` to limit the scope and `stream=True` to process results incrementally, which is crucial for very large crawls to manage memory and get feedback sooner.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy
from unittest.mock import patch

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_large_site_efficiently():
    # Simulate a large site by setting a high conceptual depth,
    # but limit actual work with max_pages.
    strategy = BFSDeePCrawlStrategy(
        max_depth=10,      # Imagine this could lead to thousands of pages
        max_pages=10,      # But we only want the first 10 found by BFS
        include_external=False 
    )
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True,       # Process results as they come
        cache_mode=CacheMode.BYPASS # Or CacheMode.ENABLED for subsequent partial crawls
    )

    print("--- Efficiently Crawling a 'Large' Site (max_pages=10, stream=True) ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html" # Use our mock site
        
        crawled_count = 0
        async for result in await crawler.arun(url=start_url, config=run_config):
            crawled_count += 1
            if result.success:
                print(f"  Processed ({crawled_count}/{strategy.max_pages}): {result.url} at depth {result.metadata.get('depth')}")
            else:
                print(f"  Failed ({crawled_count}/{strategy.max_pages}): {result.url} - {result.error_message}")
            
            if crawled_count >= strategy.max_pages:
                print(f"Reached max_pages limit of {strategy.max_pages}. Stopping.")
                # In a real scenario, you might need to call strategy.shutdown() if the crawler
                # doesn't automatically stop precisely at max_pages when streaming.
                # However, strategies are designed to respect max_pages.
                break 
                
        print(f"\nTotal pages processed: {crawled_count}")
        assert crawled_count <= strategy.max_pages

if __name__ == "__main__":
    asyncio.run(deep_crawl_large_site_efficiently())
```

### 8.5. Example: Combining deep crawling with `LLMExtractionStrategy` to extract structured data from each crawled page.
This example shows setting up a deep crawl where each successfully crawled page's content is then passed to an `LLMExtractionStrategy`.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, LLMExtractionStrategy, LLMConfig
from pydantic import BaseModel, Field
from unittest.mock import patch

class PageSummary(BaseModel):
    title: str = Field(description="The main title of the page.")
    brief_summary: str = Field(description="A one-sentence summary of the page content.")

# Mock the LLM call within the extraction strategy for this example
async def mock_llm_extract(self, url: str, sections: list[str]):
    print(f"[Mock LLM] Extracting from {url}, first section: {sections[0][:50]}...")
    # Based on the URL from MOCK_SITE_DATA, return a plausible mock summary
    if "index.html" in url:
        return [{"title": "Index", "brief_summary": "This is the main page."}]
    elif "page1.html" in url:
        return [{"title": "Page 1", "brief_summary": "Content about crawl strategies."}]
    elif "page2.html" in url:
        return [{"title": "Page 2 - Feature Rich", "brief_summary": "Discusses a key feature."}]
    return [{"title": "Unknown Title", "brief_summary": "Could not summarize."}]

@patch('crawl4ai.extraction_strategy.LLMExtractionStrategy.run', side_effect=mock_llm_extract)
@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def deep_crawl_with_llm_extraction(mock_llm_run): # mock_llm_run is from the patch
    llm_config = LLMConfig(provider="mock/mock-model") # Mock provider
    
    extraction_strategy = LLMExtractionStrategy(
        llm_config=llm_config,
        schema=PageSummary.model_json_schema(), # Use Pydantic model for schema
        extraction_type="schema",
        instruction="Extract the title and a brief summary for the provided HTML content."
    )
    
    deep_crawl_config = BFSDeePCrawlStrategy(max_depth=1, max_pages=3)
    
    run_config = CrawlerRunConfig(
        deep_crawl_strategy=deep_crawl_config,
        extraction_strategy=extraction_strategy, # Apply this to each crawled page
        cache_mode=CacheMode.BYPASS
    )

    print("--- Deep Crawl with LLM Extraction on Each Page ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        for result in results:
            if result.success:
                print(f"\nCrawled URL: {result.url}")
                if result.extracted_content:
                    print(f"  Extracted Data: {result.extracted_content}")
                else:
                    print("  No data extracted (or LLM mock returned empty).")
            else:
                print(f"\nFailed to crawl URL: {result.url} - {result.error_message}")
        
        assert mock_llm_run.called, "LLM Extraction strategy's run method was not called."

if __name__ == "__main__":
    asyncio.run(deep_crawl_with_llm_extraction())
```

### 8.6. Example: Scenario for using `can_process_url` within a strategy to dynamically decide if a URL should be added to the queue.
Override `can_process_url` in a custom strategy to implement dynamic filtering logic based on URL and current depth.

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeePCrawlStrategy, CrawlResult
from typing import List, Set, Dict, Tuple
from unittest.mock import patch

class DepthAndPatternAwareBFSStrategy(BFSDeePCrawlStrategy):
    async def can_process_url(self, url: str, depth: int) -> bool:
        # Standard checks from parent (like filter_chain)
        if not await super().can_process_url(url, depth):
            print(f"[Custom can_process_url] Blocked by parent: {url}")
            return False
        
        # Custom logic: Do not process '/archive/' pages if depth is > 1
        if depth > 1 and "/archive/" in url:
            print(f"[Custom can_process_url] Blocking deep archive page: {url} at depth {depth}")
            return False
        
        print(f"[Custom can_process_url] Allowing: {url} at depth {depth}")
        return True

@patch('crawl4ai.AsyncWebCrawler', MockAsyncWebCrawler)
async def custom_can_process_url_example():
    # Add a deeper archive link for testing
    MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1.html"]["html_content"] += '<a href="archive/deep_archive.html">Deep Archive</a>'
    MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/archive/deep_archive.html"] = {
        "html_content": "<html><title>Deep Archive</title><body>Very old stuff.</body></html>",
        "response_headers": {"Content-Type": "text/html"}
    }

    custom_strategy = DepthAndPatternAwareBFSStrategy(max_depth=2) # Crawl up to depth 2
    run_config = CrawlerRunConfig(deep_crawl_strategy=custom_strategy, cache_mode=CacheMode.BYPASS)

    print("--- Custom Strategy with Dynamic can_process_url ---")
    async with AsyncWebCrawler() as crawler:
        start_url = "https://docs.crawl4ai.com/vibe-examples/index.html"
        results = await crawler.arun(url=start_url, config=run_config)
        
        print(f"\nCrawled {len(results)} pages:")
        archive_at_depth_1_crawled = False
        deep_archive_blocked = True

        for r in results:
            print(f"  URL: {r.url}, Depth: {r.metadata.get('depth')}")
            if "/archive/old_page.html" in r.url and r.metadata.get('depth') == 1:
                archive_at_depth_1_crawled = True
            if "/archive/deep_archive.html" in r.url and r.metadata.get('depth') == 2:
                 # This should not happen due to our custom can_process_url
                deep_archive_blocked = False 
        
        assert archive_at_depth_1_crawled, "Archive page at depth 1 should have been crawled."
        assert deep_archive_blocked, "Deep archive page at depth 2 should have been blocked by custom can_process_url."
        print("Dynamic URL processing logic worked as expected.")

    # Clean up mock data
    MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1.html"]["html_content"] = MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/page1.html"]["html_content"].replace('<a href="archive/deep_archive.html">Deep Archive</a>', '')
    del MOCK_SITE_DATA["https://docs.crawl4ai.com/vibe-examples/archive/deep_archive.html"]


if __name__ == "__main__":
    asyncio.run(custom_can_process_url_example())
    # Clean up dummy files after all examples run
    if (Path(os.getcwd()) / "test_local_index.html").exists():
        os.remove(Path(os.getcwd()) / "test_local_index.html")
    if (Path(os.getcwd()) / "test_local_page1.html").exists():
        os.remove(Path(os.getcwd()) / "test_local_page1.html")
    if Path("custom_deep_crawl.log").exists():
        os.remove("custom_deep_crawl.log")

```
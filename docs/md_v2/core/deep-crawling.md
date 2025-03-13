# Deep Crawling

One of Crawl4AI's most powerful features is its ability to perform **configurable deep crawling** that can explore websites beyond a single page. With fine-tuned control over crawl depth, domain boundaries, and content filtering, Crawl4AI gives you the tools to extract precisely the content you need.

In this tutorial, you'll learn:

1. How to set up a **Basic Deep Crawler** with BFS strategy  
2. Understanding the difference between **streamed and non-streamed** output  
3. Implementing **filters and scorers** to target specific content  
4. Creating **advanced filtering chains** for sophisticated crawls  
5. Using **BestFirstCrawling** for intelligent exploration prioritization  

> **Prerequisites**  
> - You’ve completed or read [AsyncWebCrawler Basics](../core/simple-crawling.md) to understand how to run a simple crawl.  
> - You know how to configure `CrawlerRunConfig`.

---

## 1. Quick Example

Here's a minimal code snippet that implements a basic deep crawl using the **BFSDeepCrawlStrategy**:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

async def main():
    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=2, 
            include_external=False
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        verbose=True
    )
    
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun("https://example.com", config=config)
        
        print(f"Crawled {len(results)} pages in total")
        
        # Access individual results
        for result in results[:3]:  # Show first 3 results
            print(f"URL: {result.url}")
            print(f"Depth: {result.metadata.get('depth', 0)}")

if __name__ == "__main__":
    asyncio.run(main())
```

**What's happening?**  
- `BFSDeepCrawlStrategy(max_depth=2, include_external=False)` instructs Crawl4AI to:
  - Crawl the starting page (depth 0) plus 2 more levels
  - Stay within the same domain (don't follow external links)
- Each result contains metadata like the crawl depth
- Results are returned as a list after all crawling is complete

---

## 2. Understanding Deep Crawling Strategy Options

### 2.1 BFSDeepCrawlStrategy (Breadth-First Search)

The **BFSDeepCrawlStrategy** uses a breadth-first approach, exploring all links at one depth before moving deeper:

```python
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

# Basic configuration
strategy = BFSDeepCrawlStrategy(
    max_depth=2,               # Crawl initial page + 2 levels deep
    include_external=False,    # Stay within the same domain
    max_pages=50,              # Maximum number of pages to crawl (optional)
    score_threshold=0.3,       # Minimum score for URLs to be crawled (optional)
)
```

**Key parameters:**
- **`max_depth`**: Number of levels to crawl beyond the starting page
- **`include_external`**: Whether to follow links to other domains
- **`max_pages`**: Maximum number of pages to crawl (default: infinite)
- **`score_threshold`**: Minimum score for URLs to be crawled (default: -inf)
- **`filter_chain`**: FilterChain instance for URL filtering
- **`url_scorer`**: Scorer instance for evaluating URLs

### 2.2 DFSDeepCrawlStrategy (Depth-First Search)

The **DFSDeepCrawlStrategy** uses a depth-first approach, explores as far down a branch as possible before backtracking.

```python
from crawl4ai.deep_crawling import DFSDeepCrawlStrategy

# Basic configuration
strategy = DFSDeepCrawlStrategy(
    max_depth=2,               # Crawl initial page + 2 levels deep
    include_external=False,    # Stay within the same domain
    max_pages=30,              # Maximum number of pages to crawl (optional)
    score_threshold=0.5,       # Minimum score for URLs to be crawled (optional)
)
```

**Key parameters:**
- **`max_depth`**: Number of levels to crawl beyond the starting page
- **`include_external`**: Whether to follow links to other domains
- **`max_pages`**: Maximum number of pages to crawl (default: infinite)
- **`score_threshold`**: Minimum score for URLs to be crawled (default: -inf)
- **`filter_chain`**: FilterChain instance for URL filtering
- **`url_scorer`**: Scorer instance for evaluating URLs

### 2.3 BestFirstCrawlingStrategy (⭐️ - Recommended Deep crawl strategy)

For more intelligent crawling, use **BestFirstCrawlingStrategy** with scorers to prioritize the most relevant pages:

```python
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

# Create a scorer
scorer = KeywordRelevanceScorer(
    keywords=["crawl", "example", "async", "configuration"],
    weight=0.7
)

# Configure the strategy
strategy = BestFirstCrawlingStrategy(
    max_depth=2,
    include_external=False,
    url_scorer=scorer,
    max_pages=25,              # Maximum number of pages to crawl (optional)
)
```

This crawling approach:
- Evaluates each discovered URL based on scorer criteria
- Visits higher-scoring pages first
- Helps focus crawl resources on the most relevant content
- Can limit total pages crawled with `max_pages`
- Does not need `score_threshold` as it naturally prioritizes by score

---

## 3. Streaming vs. Non-Streaming Results

Crawl4AI can return results in two modes:

### 3.1 Non-Streaming Mode (Default)

```python
config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=1),
    stream=False  # Default behavior
)

async with AsyncWebCrawler() as crawler:
    # Wait for ALL results to be collected before returning
    results = await crawler.arun("https://example.com", config=config)
    
    for result in results:
        process_result(result)
```

**When to use non-streaming mode:**
- You need the complete dataset before processing
- You're performing batch operations on all results together
- Crawl time isn't a critical factor

### 3.2 Streaming Mode

```python
config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(max_depth=1),
    stream=True  # Enable streaming
)

async with AsyncWebCrawler() as crawler:
    # Returns an async iterator
    async for result in await crawler.arun("https://example.com", config=config):
        # Process each result as it becomes available
        process_result(result)
```

**Benefits of streaming mode:**
- Process results immediately as they're discovered
- Start working with early results while crawling continues
- Better for real-time applications or progressive display
- Reduces memory pressure when handling many pages

---

## 4. Filtering Content with Filter Chains

Filters help you narrow down which pages to crawl. Combine multiple filters using **FilterChain** for powerful targeting.

### 4.1 Basic URL Pattern Filter

```python
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter

# Only follow URLs containing "blog" or "docs"
url_filter = URLPatternFilter(patterns=["*blog*", "*docs*"])

config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=1,
        filter_chain=FilterChain([url_filter])
    )
)
```

### 4.2 Combining Multiple Filters

```python
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    URLPatternFilter,
    DomainFilter,
    ContentTypeFilter
)

# Create a chain of filters
filter_chain = FilterChain([
    # Only follow URLs with specific patterns
    URLPatternFilter(patterns=["*guide*", "*tutorial*"]),
    
    # Only crawl specific domains
    DomainFilter(
        allowed_domains=["docs.example.com"],
        blocked_domains=["old.docs.example.com"]
    ),
    
    # Only include specific content types
    ContentTypeFilter(allowed_types=["text/html"])
])

config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=2,
        filter_chain=filter_chain
    )
)
```

### 4.3 Available Filter Types

Crawl4AI includes several specialized filters:

- **`URLPatternFilter`**: Matches URL patterns using wildcard syntax
- **`DomainFilter`**: Controls which domains to include or exclude
- **`ContentTypeFilter`**: Filters based on HTTP Content-Type
- **`ContentRelevanceFilter`**: Uses similarity to a text query
- **`SEOFilter`**: Evaluates SEO elements (meta tags, headers, etc.)

---

## 5. Using Scorers for Prioritized Crawling

Scorers assign priority values to discovered URLs, helping the crawler focus on the most relevant content first.

### 5.1 KeywordRelevanceScorer

```python
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy

# Create a keyword relevance scorer
keyword_scorer = KeywordRelevanceScorer(
    keywords=["crawl", "example", "async", "configuration"],
    weight=0.7  # Importance of this scorer (0.0 to 1.0)
)

config = CrawlerRunConfig(
    deep_crawl_strategy=BestFirstCrawlingStrategy(
        max_depth=2,
        url_scorer=keyword_scorer
    ),
    stream=True  # Recommended with BestFirstCrawling
)

# Results will come in order of relevance score
async with AsyncWebCrawler() as crawler:
    async for result in await crawler.arun("https://example.com", config=config):
        score = result.metadata.get("score", 0)
        print(f"Score: {score:.2f} | {result.url}")
```

**How scorers work:**
- Evaluate each discovered URL before crawling
- Calculate relevance based on various signals
- Help the crawler make intelligent choices about traversal order

---

## 6. Advanced Filtering Techniques

### 6.1 SEO Filter for Quality Assessment

The **SEOFilter** helps you identify pages with strong SEO characteristics:

```python
from crawl4ai.deep_crawling.filters import FilterChain, SEOFilter

# Create an SEO filter that looks for specific keywords in page metadata
seo_filter = SEOFilter(
    threshold=0.5,  # Minimum score (0.0 to 1.0)
    keywords=["tutorial", "guide", "documentation"]
)

config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=1,
        filter_chain=FilterChain([seo_filter])
    )
)
```

### 6.2 Content Relevance Filter

The **ContentRelevanceFilter** analyzes the actual content of pages:

```python
from crawl4ai.deep_crawling.filters import FilterChain, ContentRelevanceFilter

# Create a content relevance filter
relevance_filter = ContentRelevanceFilter(
    query="Web crawling and data extraction with Python",
    threshold=0.7  # Minimum similarity score (0.0 to 1.0)
)

config = CrawlerRunConfig(
    deep_crawl_strategy=BFSDeepCrawlStrategy(
        max_depth=1,
        filter_chain=FilterChain([relevance_filter])
    )
)
```

This filter:
- Measures semantic similarity between query and page content
- It's a BM25-based relevance filter using head section content

---

## 7. Building a Complete Advanced Crawler

This example combines multiple techniques for a sophisticated crawl:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    DomainFilter,
    URLPatternFilter,
    ContentTypeFilter
)
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer

async def run_advanced_crawler():
    # Create a sophisticated filter chain
    filter_chain = FilterChain([
        # Domain boundaries
        DomainFilter(
            allowed_domains=["docs.example.com"],
            blocked_domains=["old.docs.example.com"]
        ),
        
        # URL patterns to include
        URLPatternFilter(patterns=["*guide*", "*tutorial*", "*blog*"]),
        
        # Content type filtering
        ContentTypeFilter(allowed_types=["text/html"])
    ])

    # Create a relevance scorer
    keyword_scorer = KeywordRelevanceScorer(
        keywords=["crawl", "example", "async", "configuration"],
        weight=0.7
    )

    # Set up the configuration
    config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=2,
            include_external=False,
            filter_chain=filter_chain,
            url_scorer=keyword_scorer
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        stream=True,
        verbose=True
    )

    # Execute the crawl
    results = []
    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun("https://docs.example.com", config=config):
            results.append(result)
            score = result.metadata.get("score", 0)
            depth = result.metadata.get("depth", 0)
            print(f"Depth: {depth} | Score: {score:.2f} | {result.url}")

    # Analyze the results
    print(f"Crawled {len(results)} high-value pages")
    print(f"Average score: {sum(r.metadata.get('score', 0) for r in results) / len(results):.2f}")

    # Group by depth
    depth_counts = {}
    for result in results:
        depth = result.metadata.get("depth", 0)
        depth_counts[depth] = depth_counts.get(depth, 0) + 1

    print("Pages crawled by depth:")
    for depth, count in sorted(depth_counts.items()):
        print(f"  Depth {depth}: {count} pages")

if __name__ == "__main__":
    asyncio.run(run_advanced_crawler())
```

---


## 8. Limiting and Controlling Crawl Size

### 8.1 Using max_pages

You can limit the total number of pages crawled with the `max_pages` parameter:

```python
# Limit to exactly 20 pages regardless of depth
strategy = BFSDeepCrawlStrategy(
    max_depth=3,
    max_pages=20
)
```

This feature is useful for:
- Controlling API costs
- Setting predictable execution times
- Focusing on the most important content
- Testing crawl configurations before full execution

### 8.2 Using score_threshold

For BFS and DFS strategies, you can set a minimum score threshold to only crawl high-quality pages:

```python
# Only follow links with scores above 0.4
strategy = DFSDeepCrawlStrategy(
    max_depth=2,
    url_scorer=KeywordRelevanceScorer(keywords=["api", "guide", "reference"]),
    score_threshold=0.4  # Skip URLs with scores below this value
)
```

Note that for BestFirstCrawlingStrategy, score_threshold is not needed since pages are already processed in order of highest score first.

## 9. Common Pitfalls & Tips

1.**Set realistic limits.** Be cautious with `max_depth` values > 3, which can exponentially increase crawl size. Use `max_pages` to set hard limits.

2.**Don't neglect the scoring component.** BestFirstCrawling works best with well-tuned scorers. Experiment with keyword weights for optimal prioritization.

3.**Be a good web citizen.**  Respect robots.txt. (disabled by default)
  
4.**Handle page errors gracefully.** Not all pages will be accessible. Check `result.status` when processing results.

5.**Balance breadth vs. depth.** Choose your strategy wisely - BFS for comprehensive coverage, DFS for deep exploration, BestFirst for focused relevance-based crawling.

---

## 10. Summary & Next Steps

In this **Deep Crawling with Crawl4AI** tutorial, you learned to:

- Configure **BFSDeepCrawlStrategy**, **DFSDeepCrawlStrategy**, and **BestFirstCrawlingStrategy**
- Process results in streaming or non-streaming mode
- Apply filters to target specific content
- Use scorers to prioritize the most relevant pages
- Limit crawls with `max_pages` and `score_threshold` parameters
- Build a complete advanced crawler with combined techniques

With these tools, you can efficiently extract structured data from websites at scale, focusing precisely on the content you need for your specific use case.

Deep Crawling
=============

One of Crawl4AI's most powerful features is its ability to perform **configurable deep crawling** that can explore websites beyond a single page. With fine-tuned control over crawl depth, domain boundaries, and content filtering, Crawl4AI gives you the tools to extract precisely the content you need.

In this tutorial, you'll learn:

1. How to set up a **Basic Deep Crawler** with BFS strategy
2. Understanding the difference between **streamed and non-streamed** output
3. Implementing **filters and scorers** to target specific content
4. Creating **advanced filtering chains** for sophisticated crawls
5. Using **BestFirstCrawling** for intelligent exploration prioritization

> **Prerequisites**
> - You’ve completed or read [AsyncWebCrawler Basics](../simple-crawling/) to understand how to run a simple crawl.
> - You know how to configure `CrawlerRunConfig`.

---

1. Quick Example
----------------

Here's a minimal code snippet that implements a basic deep crawl using the **BFSDeepCrawlStrategy**:

```
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
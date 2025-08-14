Markdown Generation Basics
==========================

One of Crawl4AI’s core features is generating **clean, structured markdown** from web pages. Originally built to solve the problem of extracting only the “actual” content and discarding boilerplate or noise, Crawl4AI’s markdown system remains one of its biggest draws for AI workflows.

In this tutorial, you’ll learn:

1. How to configure the **Default Markdown Generator**
2. How **content filters** (BM25 or Pruning) help you refine markdown and discard junk
3. The difference between raw markdown (`result.markdown`) and filtered markdown (`fit_markdown`)

> **Prerequisites**
> - You’ve completed or read [AsyncWebCrawler Basics](../simple-crawling/) to understand how to run a simple crawl.
> - You know how to configure `CrawlerRunConfig`.

---

1. Quick Example
----------------

Here’s a minimal code snippet that uses the **DefaultMarkdownGenerator** with no additional filtering:

```
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    config = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator()
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=config)

        if result.success:
            print("Raw Markdown Output:\n")
            print(result.markdown)  # The unfiltered markdown from the page
        else:
            print("Crawl failed:", result.error_message)

if __name__ == "__main__":
    asyncio.run(main())
```

**What’s happening?**
- `CrawlerRunConfig( markdown_generator = DefaultMarkdownGenerator() )` instructs Crawl4AI to convert the final HTML into markdown at the end of each crawl.
- The resulting markdown is accessible via `result.markdown`.

---
[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/core/content-selection/)


[ unclecode/crawl4ai ](https://github.com/unclecode/crawl4ai)
×
  * [Home](https://docs.crawl4ai.com/)
  * [Ask AI](https://docs.crawl4ai.com/core/ask-ai/)
  * [Quick Start](https://docs.crawl4ai.com/core/quickstart/)
  * [Code Examples](https://docs.crawl4ai.com/core/examples/)
  * Apps
    * [Demo Apps](https://docs.crawl4ai.com/apps/)
    * [C4A-Script Editor](https://docs.crawl4ai.com/apps/c4a-script/)
    * [LLM Context Builder](https://docs.crawl4ai.com/apps/llmtxt/)
  * Setup & Installation
    * [Installation](https://docs.crawl4ai.com/core/installation/)
    * [Docker Deployment](https://docs.crawl4ai.com/core/docker-deployment/)
  * Blog & Changelog
    * [Blog Home](https://docs.crawl4ai.com/blog/)
    * [Changelog](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md)
  * Core
    * [Command Line Interface](https://docs.crawl4ai.com/core/cli/)
    * [Simple Crawling](https://docs.crawl4ai.com/core/simple-crawling/)
    * [Deep Crawling](https://docs.crawl4ai.com/core/deep-crawling/)
    * [Adaptive Crawling](https://docs.crawl4ai.com/core/adaptive-crawling/)
    * [URL Seeding](https://docs.crawl4ai.com/core/url-seeding/)
    * [C4A-Script](https://docs.crawl4ai.com/core/c4a-script/)
    * [Crawler Result](https://docs.crawl4ai.com/core/crawler-result/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/core/browser-crawler-config/)
    * [Markdown Generation](https://docs.crawl4ai.com/core/markdown-generation/)
    * [Fit Markdown](https://docs.crawl4ai.com/core/fit-markdown/)
    * [Page Interaction](https://docs.crawl4ai.com/core/page-interaction/)
    * Content Selection
    * [Cache Modes](https://docs.crawl4ai.com/core/cache-modes/)
    * [Local Files & Raw HTML](https://docs.crawl4ai.com/core/local-files/)
    * [Link & Media](https://docs.crawl4ai.com/core/link-media/)
  * Advanced
    * [Overview](https://docs.crawl4ai.com/advanced/advanced-features/)
    * [Adaptive Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/)
    * [Virtual Scroll](https://docs.crawl4ai.com/advanced/virtual-scroll/)
    * [File Downloading](https://docs.crawl4ai.com/advanced/file-downloading/)
    * [Lazy Loading](https://docs.crawl4ai.com/advanced/lazy-loading/)
    * [Hooks & Auth](https://docs.crawl4ai.com/advanced/hooks-auth/)
    * [Proxy & Security](https://docs.crawl4ai.com/advanced/proxy-security/)
    * [Undetected Browser](https://docs.crawl4ai.com/advanced/undetected-browser/)
    * [Session Management](https://docs.crawl4ai.com/advanced/session-management/)
    * [Multi-URL Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling/)
    * [Crawl Dispatcher](https://docs.crawl4ai.com/advanced/crawl-dispatcher/)
    * [Identity Based Crawling](https://docs.crawl4ai.com/advanced/identity-based-crawling/)
    * [SSL Certificate](https://docs.crawl4ai.com/advanced/ssl-certificate/)
    * [Network & Console Capture](https://docs.crawl4ai.com/advanced/network-console-capture/)
    * [PDF Parsing](https://docs.crawl4ai.com/advanced/pdf-parsing/)
  * Extraction
    * [LLM-Free Strategies](https://docs.crawl4ai.com/extraction/no-llm-strategies/)
    * [LLM Strategies](https://docs.crawl4ai.com/extraction/llm-strategies/)
    * [Clustering Strategies](https://docs.crawl4ai.com/extraction/clustring-strategies/)
    * [Chunking](https://docs.crawl4ai.com/extraction/chunking/)
  * API Reference
    * [AsyncWebCrawler](https://docs.crawl4ai.com/api/async-webcrawler/)
    * [arun()](https://docs.crawl4ai.com/api/arun/)
    * [arun_many()](https://docs.crawl4ai.com/api/arun_many/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/api/parameters/)
    * [CrawlResult](https://docs.crawl4ai.com/api/crawl-result/)
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [Content Selection](https://docs.crawl4ai.com/core/content-selection/#content-selection)
  * [1. CSS-Based Selection](https://docs.crawl4ai.com/core/content-selection/#1-css-based-selection)
  * [2. Content Filtering & Exclusions](https://docs.crawl4ai.com/core/content-selection/#2-content-filtering-exclusions)
  * [3. Handling Iframes](https://docs.crawl4ai.com/core/content-selection/#3-handling-iframes)
  * [4. Structured Extraction Examples](https://docs.crawl4ai.com/core/content-selection/#4-structured-extraction-examples)
  * [5. Comprehensive Example](https://docs.crawl4ai.com/core/content-selection/#5-comprehensive-example)
  * [6. Scraping Modes](https://docs.crawl4ai.com/core/content-selection/#6-scraping-modes)
  * [7. Combining CSS Selection Methods](https://docs.crawl4ai.com/core/content-selection/#7-combining-css-selection-methods)
  * [8. Conclusion](https://docs.crawl4ai.com/core/content-selection/#8-conclusion)


# Content Selection
Crawl4AI provides multiple ways to **select** , **filter** , and **refine** the content from your crawls. Whether you need to target a specific CSS region, exclude entire tags, filter out external links, or remove certain domains and images, **`CrawlerRunConfig`**offers a wide range of parameters.
Below, we show how to configure these parameters and combine them for precise control.
* * *
## 1. CSS-Based Selection
There are two ways to select content from a page: using `css_selector` or the more flexible `target_elements`.
### 1.1 Using `css_selector`
A straightforward way to **limit** your crawl results to a certain region of the page is **`css_selector`**in**`CrawlerRunConfig`**:
```
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    config = CrawlerRunConfig(
        # e.g., first 30 items from Hacker News
        css_selector=".athing:nth-child(-n+30)"
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com/newest",
            config=config
        )
        print("Partial HTML length:", len(result.cleaned_html))

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

**Result** : Only elements matching that selector remain in `result.cleaned_html`.
### 1.2 Using `target_elements`
The `target_elements` parameter provides more flexibility by allowing you to target **multiple elements** for content extraction while preserving the entire page context for other features:
```
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    config = CrawlerRunConfig(
        # Target article body and sidebar, but not other content
        target_elements=["article.main-content", "aside.sidebar"]
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com/blog-post",
            config=config
        )
        print("Markdown focused on target elements")
        print("Links from entire page still available:", len(result.links.get("internal", [])))

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

**Key difference** : With `target_elements`, the markdown generation and structural data extraction focus on those elements, but other page elements (like links, images, and tables) are still extracted from the entire page. This gives you fine-grained control over what appears in your markdown content while preserving full page context for link analysis and media collection.
* * *
## 2. Content Filtering & Exclusions
### 2.1 Basic Overview
```
config = CrawlerRunConfig(
    # Content thresholds
    word_count_threshold=10,        # Minimum words per block

    # Tag exclusions
    excluded_tags=['form', 'header', 'footer', 'nav'],

    # Link filtering
    exclude_external_links=True,
    exclude_social_media_links=True,
    # Block entire domains
    exclude_domains=["adtrackers.com", "spammynews.org"],
    exclude_social_media_domains=["facebook.com", "twitter.com"],

    # Media filtering
    exclude_external_images=True
)
Copy
```

**Explanation** :
  * **`word_count_threshold`**: Ignores text blocks under X words. Helps skip trivial blocks like short nav or disclaimers.
  * **`excluded_tags`**: Removes entire tags (`<form>` , `<header>`, `<footer>`, etc.).
  * **Link Filtering** :
  * `exclude_external_links`: Strips out external links and may remove them from `result.links`.
  * `exclude_social_media_links`: Removes links pointing to known social media domains.
  * `exclude_domains`: A custom list of domains to block if discovered in links.
  * `exclude_social_media_domains`: A curated list (override or add to it) for social media sites.
  * **Media Filtering** :
  * `exclude_external_images`: Discards images not hosted on the same domain as the main page (or its subdomains).


By default in case you set `exclude_social_media_links=True`, the following social media domains are excluded:
```
[
    'facebook.com',
    'twitter.com',
    'x.com',
    'linkedin.com',
    'instagram.com',
    'pinterest.com',
    'tiktok.com',
    'snapchat.com',
    'reddit.com',
]
Copy
```

### 2.2 Example Usage
```
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    config = CrawlerRunConfig(
        css_selector="main.content",
        word_count_threshold=10,
        excluded_tags=["nav", "footer"],
        exclude_external_links=True,
        exclude_social_media_links=True,
        exclude_domains=["ads.com", "spammytrackers.net"],
        exclude_external_images=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://news.ycombinator.com", config=config)
        print("Cleaned HTML length:", len(result.cleaned_html))

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

**Note** : If these parameters remove too much, reduce or disable them accordingly.
* * *
## 3. Handling Iframes
Some sites embed content in `<iframe>` tags. If you want that inline:
```
config = CrawlerRunConfig(
    # Merge iframe content into the final output
    process_iframes=True,
    remove_overlay_elements=True
)
Copy
```

**Usage** :
```
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def main():
    config = CrawlerRunConfig(
        process_iframes=True,
        remove_overlay_elements=True
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.org/iframe-demo",
            config=config
        )
        print("Iframe-merged length:", len(result.cleaned_html))

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

* * *
## 4. Structured Extraction Examples
You can combine content selection with a more advanced extraction strategy. For instance, a **CSS-based** or **LLM-based** extraction strategy can run on the filtered HTML.
### 4.1 Pattern-Based with `JsonCssExtractionStrategy`
```
import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy

async def main():
    # Minimal schema for repeated items
    schema = {
        "name": "News Items",
        "baseSelector": "tr.athing",
        "fields": [
            {"name": "title", "selector": "span.titleline a", "type": "text"},
            {
                "name": "link",
                "selector": "span.titleline a",
                "type": "attribute",
                "attribute": "href"
            }
        ]
    }

    config = CrawlerRunConfig(
        # Content filtering
        excluded_tags=["form", "header"],
        exclude_domains=["adsite.com"],

        # CSS selection or entire page
        css_selector="table.itemlist",

        # No caching for demonstration
        cache_mode=CacheMode.BYPASS,

        # Extraction strategy
        extraction_strategy=JsonCssExtractionStrategy(schema)
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://news.ycombinator.com/newest",
            config=config
        )
        data = json.loads(result.extracted_content)
        print("Sample extracted item:", data[:1])  # Show first item

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

### 4.2 LLM-Based Extraction
```
import asyncio
import json
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LLMConfig
from crawl4ai import LLMExtractionStrategy

class ArticleData(BaseModel):
    headline: str
    summary: str

async def main():
    llm_strategy = LLMExtractionStrategy(
        llm_config = LLMConfig(provider="openai/gpt-4",api_token="sk-YOUR_API_KEY")
        schema=ArticleData.schema(),
        extraction_type="schema",
        instruction="Extract 'headline' and a short 'summary' from the content."
    )

    config = CrawlerRunConfig(
        exclude_external_links=True,
        word_count_threshold=20,
        extraction_strategy=llm_strategy
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://news.ycombinator.com", config=config)
        article = json.loads(result.extracted_content)
        print(article)

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

Here, the crawler:
  * Filters out external links (`exclude_external_links=True`).
  * Ignores very short text blocks (`word_count_threshold=20`).
  * Passes the final HTML to your LLM strategy for an AI-driven parse.


* * *
## 5. Comprehensive Example
Below is a short function that unifies **CSS selection** , **exclusion** logic, and a pattern-based extraction, demonstrating how you can fine-tune your final data:
```
import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy

async def extract_main_articles(url: str):
    schema = {
        "name": "ArticleBlock",
        "baseSelector": "div.article-block",
        "fields": [
            {"name": "headline", "selector": "h2", "type": "text"},
            {"name": "summary", "selector": ".summary", "type": "text"},
            {
                "name": "metadata",
                "type": "nested",
                "fields": [
                    {"name": "author", "selector": ".author", "type": "text"},
                    {"name": "date", "selector": ".date", "type": "text"}
                ]
            }
        ]
    }

    config = CrawlerRunConfig(
        # Keep only #main-content
        css_selector="#main-content",

        # Filtering
        word_count_threshold=10,
        excluded_tags=["nav", "footer"],
        exclude_external_links=True,
        exclude_domains=["somebadsite.com"],
        exclude_external_images=True,

        # Extraction
        extraction_strategy=JsonCssExtractionStrategy(schema),

        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        if not result.success:
            print(f"Error: {result.error_message}")
            return None
        return json.loads(result.extracted_content)

async def main():
    articles = await extract_main_articles("https://news.ycombinator.com/newest")
    if articles:
        print("Extracted Articles:", articles[:2])  # Show first 2

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

**Why This Works** : - **CSS** scoping with `#main-content`.
- Multiple **exclude_** parameters to remove domains, external images, etc.
- A **JsonCssExtractionStrategy** to parse repeated article blocks.
* * *
## 6. Scraping Modes
Crawl4AI uses `LXMLWebScrapingStrategy` (LXML-based) as the default scraping strategy for HTML content processing. This strategy offers excellent performance, especially for large HTML documents.
**Note:** For backward compatibility, `WebScrapingStrategy` is still available as an alias for `LXMLWebScrapingStrategy`.
```
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, LXMLWebScrapingStrategy

async def main():
    # Default configuration already uses LXMLWebScrapingStrategy
    config = CrawlerRunConfig()

    # Or explicitly specify it if desired
    config_explicit = CrawlerRunConfig(
        scraping_strategy=LXMLWebScrapingStrategy()
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=config
        )
Copy
```

You can also create your own custom scraping strategy by inheriting from `ContentScrapingStrategy`. The strategy must return a `ScrapingResult` object with the following structure:
```
from crawl4ai import ContentScrapingStrategy, ScrapingResult, MediaItem, Media, Link, Links

class CustomScrapingStrategy(ContentScrapingStrategy):
    def scrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
        # Implement your custom scraping logic here
        return ScrapingResult(
            cleaned_html="<html>...</html>",  # Cleaned HTML content
            success=True,                     # Whether scraping was successful
            media=Media(
                images=[                      # List of images found
                    MediaItem(
                        src="https://example.com/image.jpg",
                        alt="Image description",
                        desc="Surrounding text",
                        score=1,
                        type="image",
                        group_id=1,
                        format="jpg",
                        width=800
                    )
                ],
                videos=[],                    # List of videos (same structure as images)
                audios=[]                     # List of audio files (same structure as images)
            ),
            links=Links(
                internal=[                    # List of internal links
                    Link(
                        href="https://example.com/page",
                        text="Link text",
                        title="Link title",
                        base_domain="example.com"
                    )
                ],
                external=[]                   # List of external links (same structure)
            ),
            metadata={                        # Additional metadata
                "title": "Page Title",
                "description": "Page description"
            }
        )

    async def ascrap(self, url: str, html: str, **kwargs) -> ScrapingResult:
        # For simple cases, you can use the sync version
        return await asyncio.to_thread(self.scrap, url, html, **kwargs)
Copy
```

### Performance Considerations
The LXML strategy provides excellent performance, particularly when processing large HTML documents, offering up to 10-20x faster processing compared to BeautifulSoup-based approaches.
Benefits of LXML strategy: - Fast processing of large HTML documents (especially >100KB) - Efficient memory usage - Good handling of well-formed HTML - Robust table detection and extraction
### Backward Compatibility
For users upgrading from earlier versions: - `WebScrapingStrategy` is now an alias for `LXMLWebScrapingStrategy` - Existing code using `WebScrapingStrategy` will continue to work without modification - No changes are required to your existing code
* * *
## 7. Combining CSS Selection Methods
You can combine `css_selector` and `target_elements` in powerful ways to achieve fine-grained control over your output:
```
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    # Target specific content but preserve page context
    config = CrawlerRunConfig(
        # Focus markdown on main content and sidebar
        target_elements=["#main-content", ".sidebar"],

        # Global filters applied to entire page
        excluded_tags=["nav", "footer", "header"],
        exclude_external_links=True,

        # Use basic content thresholds
        word_count_threshold=15,

        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com/article",
            config=config
        )

        print(f"Content focuses on specific elements, but all links still analyzed")
        print(f"Internal links: {len(result.links.get('internal', []))}")
        print(f"External links: {len(result.links.get('external', []))}")

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

This approach gives you the best of both worlds: - Markdown generation and content extraction focus on the elements you care about - Links, images and other page data still give you the full context of the page - Content filtering still applies globally
## 8. Conclusion
By mixing **target_elements** or **css_selector** scoping, **content filtering** parameters, and advanced **extraction strategies** , you can precisely **choose** which data to keep. Key parameters in **`CrawlerRunConfig`**for content selection include:
  1. **`target_elements`**– Array of CSS selectors to focus markdown generation and data extraction, while preserving full page context for links and media.
  2. **`css_selector`**– Basic scoping to an element or region for all extraction processes.
  3. **`word_count_threshold`**– Skip short blocks.
  4. **`excluded_tags`**– Remove entire HTML tags.
  5. **`exclude_external_links`**,**`exclude_social_media_links`**,**`exclude_domains`**– Filter out unwanted links or domains.
  6. **`exclude_external_images`**– Remove images from external sources.
  7. **`process_iframes`**– Merge iframe content if needed.


Combine these with structured extraction (CSS, LLM-based, or others) to build powerful crawls that yield exactly the content you want, from raw or cleaned HTML up to sophisticated JSON structures. For more detail, see [Configuration Reference](https://docs.crawl4ai.com/api/parameters/). Enjoy curating your data to the max!
#### On this page
  * [1. CSS-Based Selection](https://docs.crawl4ai.com/core/content-selection/#1-css-based-selection)
  * [1.1 Using css_selector](https://docs.crawl4ai.com/core/content-selection/#11-using-css_selector)
  * [1.2 Using target_elements](https://docs.crawl4ai.com/core/content-selection/#12-using-target_elements)
  * [2. Content Filtering & Exclusions](https://docs.crawl4ai.com/core/content-selection/#2-content-filtering-exclusions)
  * [2.1 Basic Overview](https://docs.crawl4ai.com/core/content-selection/#21-basic-overview)
  * [2.2 Example Usage](https://docs.crawl4ai.com/core/content-selection/#22-example-usage)
  * [3. Handling Iframes](https://docs.crawl4ai.com/core/content-selection/#3-handling-iframes)
  * [4. Structured Extraction Examples](https://docs.crawl4ai.com/core/content-selection/#4-structured-extraction-examples)
  * [4.1 Pattern-Based with JsonCssExtractionStrategy](https://docs.crawl4ai.com/core/content-selection/#41-pattern-based-with-jsoncssextractionstrategy)
  * [4.2 LLM-Based Extraction](https://docs.crawl4ai.com/core/content-selection/#42-llm-based-extraction)
  * [5. Comprehensive Example](https://docs.crawl4ai.com/core/content-selection/#5-comprehensive-example)
  * [6. Scraping Modes](https://docs.crawl4ai.com/core/content-selection/#6-scraping-modes)
  * [Performance Considerations](https://docs.crawl4ai.com/core/content-selection/#performance-considerations)
  * [Backward Compatibility](https://docs.crawl4ai.com/core/content-selection/#backward-compatibility)
  * [7. Combining CSS Selection Methods](https://docs.crawl4ai.com/core/content-selection/#7-combining-css-selection-methods)
  * [8. Conclusion](https://docs.crawl4ai.com/core/content-selection/#8-conclusion)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")

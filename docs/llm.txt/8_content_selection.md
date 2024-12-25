# Content Selection in Crawl4AI

Crawl4AI offers flexible and powerful methods to precisely select and filter content from webpages. Whether you’re extracting articles, filtering unwanted elements, or using LLMs for structured data extraction, this guide will walk you through the essentials and advanced techniques.

**Table of Contents:**  
- [Content Selection in Crawl4AI](#content-selection-in-crawl4ai)
  - [Introduction \& Quick Start](#introduction--quick-start)
  - [CSS Selectors](#css-selectors)
  - [Content Filtering](#content-filtering)
  - [Handling Iframe Content](#handling-iframe-content)
  - [Structured Content Selection Using LLMs](#structured-content-selection-using-llms)
  - [Pattern-Based Selection](#pattern-based-selection)
  - [Comprehensive Example: Combining Techniques](#comprehensive-example-combining-techniques)
  - [Troubleshooting \& Best Practices](#troubleshooting--best-practices)
  - [Additional Resources](#additional-resources)

---

## Introduction & Quick Start

When crawling websites, you often need to isolate specific parts of a page—such as main article text, product listings, or metadata. Crawl4AI’s content selection features help you fine-tune your crawls to grab exactly what you need, while filtering out unnecessary elements.

**Quick Start Example:** Here’s a minimal example that extracts the main article content from a page:

```python
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler

async def quick_start():
    config = CrawlerRunConfig(css_selector=".main-article")
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://crawl4ai.com", config=config)
        print(result.extracted_content)
```

This snippet sets a simple CSS selector to focus on the main article area of a webpage. You can build from here, adding more advanced strategies as needed.

---

## CSS Selectors

**What are they?**  
CSS selectors let you target specific parts of a webpage’s HTML. If you can identify a unique CSS selector (such as `.main-article`, `article h1`, or `.product-listing > li`), you can precisely control what parts of the page are extracted.

**How to find selectors:**  
1. Open the page in your browser.  
2. Use browser dev tools (e.g., Chrome DevTools: right-click → "Inspect") to locate the elements you want.  
3. Copy the CSS selector for that element.

**Example:**
```python
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler

async def extract_heading_and_content(url):
    config = CrawlerRunConfig(css_selector="article h1, article .content")
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        return result.extracted_content
```

**Tip:** If your extracted content is empty, verify that your CSS selectors match existing elements on the page. Using overly generic selectors can also lead to too much content being extracted.

---

## Video and Audio Content

The library extracts video and audio elements with their metadata:

```python
from crawl4ai.async_configs import CrawlerRunConfig

config = CrawlerRunConfig()
result = await crawler.arun(url="https://example.com", config=config)

# Process videos
for video in result.media["videos"]:
    print(f"Video source: {video['src']}")
    print(f"Type: {video['type']}")
    print(f"Duration: {video.get('duration')}")
    print(f"Thumbnail: {video.get('poster')}")

# Process audio
for audio in result.media["audios"]:
    print(f"Audio source: {audio['src']}")
    print(f"Type: {audio['type']}")
    print(f"Duration: {audio.get('duration')}")
```

## Link Analysis

Crawl4AI provides sophisticated link analysis capabilities, helping you understand the relationship between pages and identify important navigation patterns.

### Link Classification

The library automatically categorizes links into:
- Internal links (same domain)
- External links (different domains)
- Social media links
- Navigation links
- Content links

```python
from crawl4ai.async_configs import CrawlerRunConfig

config = CrawlerRunConfig()
result = await crawler.arun(url="https://example.com", config=config)

# Analyze internal links
for link in result.links["internal"]:
    print(f"Internal: {link['href']}")
    print(f"Link text: {link['text']}")
    print(f"Context: {link['context']}")  # Surrounding text
    print(f"Type: {link['type']}")  # nav, content, etc.

# Analyze external links
for link in result.links["external"]:
    print(f"External: {link['href']}")
    print(f"Domain: {link['domain']}")
    print(f"Type: {link['type']}")
```

### Smart Link Filtering

Control which links are included in the results with `CrawlerRunConfig`:

```python
config = CrawlerRunConfig(
    exclude_external_links=True,          # Remove external links
    exclude_social_media_links=True,      # Remove social media links
    exclude_social_media_domains=[        # Custom social media domains
        "facebook.com", "twitter.com", "instagram.com"
    ],
    exclude_domains=["ads.example.com"]   # Exclude specific domains
)
result = await crawler.arun(url="https://example.com", config=config)
```

## Metadata Extraction

Crawl4AI automatically extracts and processes page metadata, providing valuable information about the content:

```python
from crawl4ai.async_configs import CrawlerRunConfig

config = CrawlerRunConfig()
result = await crawler.arun(url="https://example.com", config=config)

metadata = result.metadata
print(f"Title: {metadata['title']}")
print(f"Description: {metadata['description']}")
print(f"Keywords: {metadata['keywords']}")
print(f"Author: {metadata['author']}")
print(f"Published Date: {metadata['published_date']}")
print(f"Modified Date: {metadata['modified_date']}")
print(f"Language: {metadata['language']}")
```



## Content Filtering

Crawl4AI provides content filtering parameters to exclude unwanted elements and ensure that you only get meaningful data. For instance, you can remove navigation bars, ads, or other non-essential parts of the page.

**Key Parameters:**
- `word_count_threshold`: Minimum word count per extracted block. Helps skip short or irrelevant snippets.
- `excluded_tags`: List of HTML tags to omit (e.g., `['form', 'header', 'footer', 'nav']`).
- `exclude_external_links`: Strips out links pointing to external domains.
- `exclude_social_media_links`: Removes common social media links or widgets.
- `exclude_external_images`: Filters out images hosted on external domains.

**Example:**
```python
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler

async def filtered_extraction(url):
    config = CrawlerRunConfig(
        word_count_threshold=10,
        excluded_tags=['form', 'header', 'footer', 'nav'],
        exclude_external_links=True,
        exclude_social_media_links=True,
        exclude_external_images=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        return result.extracted_content
```

**Best Practice:** Start with a minimal set of exclusions and increase them as needed. If you notice no content is extracted, try lowering `word_count_threshold` or removing certain excluded tags.

---

## Handling Iframe Content

If a page embeds content in iframes (such as videos, maps, or third-party widgets), you may need to enable iframe processing. This ensures that Crawl4AI loads and extracts content displayed inside iframes.

**How to enable:**  
- Set `process_iframes=True` in your `CrawlerRunConfig` to process iframe content.
- Use `remove_overlay_elements=True` to discard popups or modals that might block iframe content.

**Example:**
```python
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler

async def extract_iframe_content(url):
    config = CrawlerRunConfig(
        process_iframes=True,
        remove_overlay_elements=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        return result.extracted_content
```

**Troubleshooting:**  
- If iframe content doesn’t load, ensure the iframe’s origin is allowed and that you have no network-related issues. Check the logs or consider using a browser-based strategy that supports multi-domain requests.

---

## Structured Content Selection Using LLMs

For more complex extraction tasks (e.g., summarizing content, extracting structured data like titles and key points), you can integrate LLMs. LLM-based extraction strategies let you define a schema and provide instructions to an LLM so it returns structured, JSON-formatted results.

**When to use LLM-based strategies:**  
- Extracting complex structures not easily captured by simple CSS selectors.  
- Summarizing or transforming data.  
- Handling varied, unpredictable page layouts.

**Example with an LLMExtractionStrategy:**
```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler
from pydantic import BaseModel
from typing import List
import json

class ArticleContent(BaseModel):
    title: str
    main_points: List[str]
    conclusion: str

async def extract_article_with_llm(url):
    strategy = LLMExtractionStrategy(
        provider="ollama/nemotron",
        schema=ArticleContent.schema(),
        instruction="Extract the main article title, key points, and conclusion"
    )

    config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        article = json.loads(result.extracted_content)
        return article
```

**Tips for LLM-based extraction:**  
- Refine your prompt in `instruction` to guide the LLM towards the desired structure.  
- If results are incomplete or incorrect, consider adjusting the schema or adding more context to the instruction.  
- Check for errors and handle edge cases where the LLM might not find certain fields.

---

## Pattern-Based Selection

When dealing with repetitive, structured patterns (like a list of articles or products), you can use `JsonCssExtractionStrategy` to define a JSON schema that maps selectors to specific fields.

**Use Cases:**  
- News article listings, product grids, directory entries.  
- Extract multiple items that follow a similar structure on the same page.

**Example JSON Schema Extraction:**
```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler
import json

schema = {
    "name": "News Articles",
    "baseSelector": "article.news-item",
    "fields": [
        {"name": "headline", "selector": "h2", "type": "text"},
        {"name": "summary", "selector": ".summary", "type": "text"},
        {"name": "category", "selector": ".category", "type": "text"},
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

async def extract_news_items(url):
    strategy = JsonCssExtractionStrategy(schema)
    config = CrawlerRunConfig(extraction_strategy=strategy)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        articles = json.loads(result.extracted_content)
        return articles
```

**Maintenance Tip:** If the site’s structure changes, update your schema accordingly. Test small changes to ensure the extracted structure still matches your expectations.

---

## Comprehensive Example: Combining Techniques

Below is a more involved example that demonstrates combining multiple strategies and filtering parameters. Here, we extract structured article content from an `article.main` section, exclude unnecessary elements, and enforce a word count threshold.

```python
from crawl4ai.async_configs import CrawlerRunConfig, AsyncWebCrawler, BrowserConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import json

async def extract_article_content(url: str):
    # Schema for structured extraction
    article_schema = {
        "name": "Article",
        "baseSelector": "article.main",
        "fields": [
            {"name": "title", "selector": "h1", "type": "text"},
            {"name": "content", "selector": ".content", "type": "text"}
        ]
    }

    config = CrawlerRunConfig(
        extraction_strategy=JsonCssExtractionStrategy(article_schema),
        word_count_threshold=10,
        excluded_tags=['nav', 'footer'],
        exclude_external_links=True
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=config)
        extracted = json.loads(result.extracted_content)
        return extracted
```

**Expanding This Example:**  
- Add pagination logic to handle multi-page extractions.  
- Introduce LLM-based extraction for a summary of the article’s main points.  
- Adjust filtering parameters to refine what content is included or excluded.

---

## Troubleshooting & Best Practices

**Common Issues & Fixes:**
- **Empty extraction result:**  
  - Verify CSS selectors and filtering parameters.  
  - Lower or remove `word_count_threshold` to see if overly strict criteria are filtering everything out.
  - Check network requests or iframe settings if content is loaded dynamically.

- **Unintended content included:**  
  - Add more tags to `excluded_tags`, or refine your CSS selectors.  
  - Use `exclude_external_links` and other filters to clean up results.

- **LLM extraction errors:**  
  - Ensure the schema matches the expected JSON structure.  
  - Refine the `instruction` prompt to guide the LLM more clearly.  
  - Validate LLM provider configuration and error logs.

**Performance Tips:**
- Start with simpler strategies (basic CSS selectors) before moving to advanced LLM-based extraction.  
- Use caching or asynchronous crawling to handle large numbers of pages efficiently.  
- Consider running headless browser extractions in Docker for consistent, reproducible environments.

---

## Additional Resources

- **GitHub Source Files:**  
  - [Async Web Crawler Implementation](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/async_webcrawler.py)  
  - [Async Crawler Strategy Implementation](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/async_crawler_strategy.py)

- **Advanced Topics:**  
  - Dockerized deployments for reproducible scraping environments.  
  - Integration with caching or proxy services for large-scale crawls.  
  - Expanding LLM strategies to perform complex transformations or summarizations.

Use these links and approaches as a starting point to refine your crawling strategies. With Crawl4AI’s flexible configuration and powerful selection methods, you’ll be able to extract exactly the content you need—no more, no less.
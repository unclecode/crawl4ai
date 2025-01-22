# Getting Started with Crawl4AI

Welcome to **Crawl4AI**, an open-source LLM-friendly Web Crawler & Scraper. In this tutorial, you’ll:

1. Run your **first crawl** using minimal configuration.  
2. Generate **Markdown** output (and learn how it’s influenced by content filters).  
3. Experiment with a simple **CSS-based extraction** strategy.  
4. See a glimpse of **LLM-based extraction** (including open-source and closed-source model options).  
5. Crawl a **dynamic** page that loads content via JavaScript.

---

## 1. Introduction

Crawl4AI provides:

- An asynchronous crawler, **`AsyncWebCrawler`**.  
- Configurable browser and run settings via **`BrowserConfig`** and **`CrawlerRunConfig`**.  
- Automatic HTML-to-Markdown conversion via **`DefaultMarkdownGenerator`** (supports optional filters).  
- Multiple extraction strategies (LLM-based or “traditional” CSS/XPath-based).

By the end of this guide, you’ll have performed a basic crawl, generated Markdown, tried out two extraction strategies, and crawled a dynamic page that uses “Load More” buttons or JavaScript updates.

---

## 2. Your First Crawl

Here’s a minimal Python script that creates an **`AsyncWebCrawler`**, fetches a webpage, and prints the first 300 characters of its Markdown output:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com")
        print(result.markdown[:300])  # Print first 300 chars

if __name__ == "__main__":
    asyncio.run(main())
```

**What’s happening?**
- **`AsyncWebCrawler`** launches a headless browser (Chromium by default).
- It fetches `https://example.com`.
- Crawl4AI automatically converts the HTML into Markdown.

You now have a simple, working crawl!

---

## 3. Basic Configuration (Light Introduction)

Crawl4AI’s crawler can be heavily customized using two main classes:

1. **`BrowserConfig`**: Controls browser behavior (headless or full UI, user agent, JavaScript toggles, etc.).  
2. **`CrawlerRunConfig`**: Controls how each crawl runs (caching, extraction, timeouts, hooking, etc.).

Below is an example with minimal usage:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def main():
    browser_conf = BrowserConfig(headless=True)  # or False to see the browser
    run_conf = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_conf
        )
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
```

> IMPORTANT: By default cache mode is set to `CacheMode.ENABLED`. So to have fresh content, you need to set it to `CacheMode.BYPASS`

We’ll explore more advanced config in later tutorials (like enabling proxies, PDF output, multi-tab sessions, etc.). For now, just note how you pass these objects to manage crawling.

---

## 4. Generating Markdown Output

By default, Crawl4AI automatically generates Markdown from each crawled page. However, the exact output depends on whether you specify a **markdown generator** or **content filter**.

- **`result.markdown`**:  
  The direct HTML-to-Markdown conversion.  
- **`result.markdown.fit_markdown`**:  
  The same content after applying any configured **content filter** (e.g., `PruningContentFilter`).

### Example: Using a Filter with `DefaultMarkdownGenerator`

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

md_generator = DefaultMarkdownGenerator(
    content_filter=PruningContentFilter(threshold=0.4, threshold_type="fixed")
)

config = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    markdown_generator=md_generator
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://news.ycombinator.com", config=config)
    print("Raw Markdown length:", len(result.markdown.raw_markdown))
    print("Fit Markdown length:", len(result.markdown.fit_markdown))
```

**Note**: If you do **not** specify a content filter or markdown generator, you’ll typically see only the raw Markdown. `PruningContentFilter` may adds around `50ms` in processing time. We’ll dive deeper into these strategies in a dedicated **Markdown Generation** tutorial.

---

## 5. Simple Data Extraction (CSS-based)

Crawl4AI can also extract structured data (JSON) using CSS or XPath selectors. Below is a minimal CSS-based example:

> **New!** Crawl4AI now provides a powerful utility to automatically generate extraction schemas using LLM. This is a one-time cost that gives you a reusable schema for fast, LLM-free extractions:

```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

# Generate a schema (one-time cost)
html = "<div class='product'><h2>Gaming Laptop</h2><span class='price'>$999.99</span></div>"

# Using OpenAI (requires API token)
schema = JsonCssExtractionStrategy.generate_schema(
    html,
    llm_provider="openai/gpt-4o",  # Default provider
    api_token="your-openai-token"  # Required for OpenAI
)

# Or using Ollama (open source, no token needed)
schema = JsonCssExtractionStrategy.generate_schema(
    html,
    llm_provider="ollama/llama3.3",  # Open source alternative
    api_token=None  # Not needed for Ollama
)

# Use the schema for fast, repeated extractions
strategy = JsonCssExtractionStrategy(schema)
```

For a complete guide on schema generation and advanced usage, see [No-LLM Extraction Strategies](../extraction/no-llm-strategies.md).

Here's a basic extraction example:

```python
import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    schema = {
        "name": "Example Items",
        "baseSelector": "div.item",
        "fields": [
            {"name": "title", "selector": "h2", "type": "text"},
            {"name": "link", "selector": "a", "type": "attribute", "attribute": "href"}
        ]
    }

    raw_html = "<div class='item'><h2>Item 1</h2><a href='https://example.com/item1'>Link 1</a></div>"

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="raw://" + raw_html,
            config=CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                extraction_strategy=JsonCssExtractionStrategy(schema)
            )
        )
        # The JSON output is stored in 'extracted_content'
        data = json.loads(result.extracted_content)
        print(data)

if __name__ == "__main__":
    asyncio.run(main())
```

**Why is this helpful?**
- Great for repetitive page structures (e.g., item listings, articles).
- No AI usage or costs.
- The crawler returns a JSON string you can parse or store.

> Tips: You can pass raw HTML to the crawler instead of a URL. To do so, prefix the HTML with `raw://`.

---

## 6. Simple Data Extraction (LLM-based)

For more complex or irregular pages, a language model can parse text intelligently into a structure you define. Crawl4AI supports **open-source** or **closed-source** providers:

- **Open-Source Models** (e.g., `ollama/llama3.3`, `no_token`)  
- **OpenAI Models** (e.g., `openai/gpt-4`, requires `api_token`)  
- Or any provider supported by the underlying library

Below is an example using **open-source** style (no token) and closed-source:

```python
import os
import json
import asyncio
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(
        ..., description="Fee for output token for the OpenAI model."
    )

async def extract_structured_data_using_llm(
    provider: str, api_token: str = None, extra_headers: Dict[str, str] = None
):
    print(f"\n--- Extracting Structured Data with {provider} ---")

    if api_token is None and provider != "ollama":
        print(f"API token is required for {provider}. Skipping this example.")
        return

    browser_config = BrowserConfig(headless=True)

    extra_args = {"temperature": 0, "top_p": 0.9, "max_tokens": 2000}
    if extra_headers:
        extra_args["extra_headers"] = extra_headers

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=1,
        page_timeout=80000,
        extraction_strategy=LLMExtractionStrategy(
            provider=provider,
            api_token=api_token,
            schema=OpenAIModelFee.model_json_schema(),
            extraction_type="schema",
            instruction="""From the crawled content, extract all mentioned model names along with their fees for input and output tokens. 
            Do not miss any models in the entire content.""",
            extra_args=extra_args,
        ),
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://openai.com/api/pricing/", config=crawler_config
        )
        print(result.extracted_content)

if __name__ == "__main__":
    # Use ollama with llama3.3
    # asyncio.run(
    #     extract_structured_data_using_llm(
    #         provider="ollama/llama3.3", api_token="no-token"
    #     )
    # )

    asyncio.run(
        extract_structured_data_using_llm(
            provider="openai/gpt-4o", api_token=os.getenv("OPENAI_API_KEY")
        )
    )
```

**What’s happening?**
- We define a Pydantic schema (`PricingInfo`) describing the fields we want.
- The LLM extraction strategy uses that schema and your instructions to transform raw text into structured JSON.
- Depending on the **provider** and **api_token**, you can use local models or a remote API.

---

## 7. Multi-URL Concurrency (Preview)

If you need to crawl multiple URLs in **parallel**, you can use `arun_many()`. By default, Crawl4AI employs a **MemoryAdaptiveDispatcher**, automatically adjusting concurrency based on system resources. Here’s a quick glimpse:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def quick_parallel_example():
    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page3"
    ]
    
    run_conf = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        stream=True  # Enable streaming mode
    )

    async with AsyncWebCrawler() as crawler:
        # Stream results as they complete
        async for result in await crawler.arun_many(urls, config=run_conf):
            if result.success:
                print(f"[OK] {result.url}, length: {len(result.markdown_v2.raw_markdown)}")
            else:
                print(f"[ERROR] {result.url} => {result.error_message}")

        # Or get all results at once (default behavior)
        run_conf = run_conf.clone(stream=False)
        results = await crawler.arun_many(urls, config=run_conf)
        for res in results:
            if res.success:
                print(f"[OK] {res.url}, length: {len(res.markdown_v2.raw_markdown)}")
            else:
                print(f"[ERROR] {res.url} => {res.error_message}")

if __name__ == "__main__":
    asyncio.run(quick_parallel_example())
```

The example above shows two ways to handle multiple URLs:
1. **Streaming mode** (`stream=True`): Process results as they become available using `async for`
2. **Batch mode** (`stream=False`): Wait for all results to complete

For more advanced concurrency (e.g., a **semaphore-based** approach, **adaptive memory usage throttling**, or customized rate limiting), see [Advanced Multi-URL Crawling](../advanced/multi-url-crawling.md).

---

## 8. Dynamic Content Example

Some sites require multiple “page clicks” or dynamic JavaScript updates. Below is an example showing how to **click** a “Next Page” button and wait for new commits to load on GitHub, using **`BrowserConfig`** and **`CrawlerRunConfig`**:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def extract_structured_data_using_css_extractor():
    print("\n--- Using JsonCssExtractionStrategy for Fast Structured Output ---")
    schema = {
        "name": "KidoCode Courses",
        "baseSelector": "section.charge-methodology .w-tab-content > div",
        "fields": [
            {
                "name": "section_title",
                "selector": "h3.heading-50",
                "type": "text",
            },
            {
                "name": "section_description",
                "selector": ".charge-content",
                "type": "text",
            },
            {
                "name": "course_name",
                "selector": ".text-block-93",
                "type": "text",
            },
            {
                "name": "course_description",
                "selector": ".course-content-text",
                "type": "text",
            },
            {
                "name": "course_icon",
                "selector": ".image-92",
                "type": "attribute",
                "attribute": "src",
            },
        ],
    }

    browser_config = BrowserConfig(headless=True, java_script_enabled=True)

    js_click_tabs = """
    (async () => {
        const tabs = document.querySelectorAll("section.charge-methodology .tabs-menu-3 > div");
        for(let tab of tabs) {
            tab.scrollIntoView();
            tab.click();
            await new Promise(r => setTimeout(r, 500));
        }
    })();
    """

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=JsonCssExtractionStrategy(schema),
        js_code=[js_click_tabs],
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.kidocode.com/degrees/technology", config=crawler_config
        )

        companies = json.loads(result.extracted_content)
        print(f"Successfully extracted {len(companies)} companies")
        print(json.dumps(companies[0], indent=2))

async def main():
    await extract_structured_data_using_css_extractor()

if __name__ == "__main__":
    asyncio.run(main())
```

**Key Points**:

- **`BrowserConfig(headless=False)`**: We want to watch it click “Next Page.”  
- **`CrawlerRunConfig(...)`**: We specify the extraction strategy, pass `session_id` to reuse the same page.  
- **`js_code`** and **`wait_for`** are used for subsequent pages (`page > 0`) to click the “Next” button and wait for new commits to load.  
- **`js_only=True`** indicates we’re not re-navigating but continuing the existing session.  
- Finally, we call `kill_session()` to clean up the page and browser session.

---

## 9. Next Steps

Congratulations! You have:

1. Performed a basic crawl and printed Markdown.  
2. Used **content filters** with a markdown generator.  
3. Extracted JSON via **CSS** or **LLM** strategies.  
4. Handled **dynamic** pages with JavaScript triggers.

If you’re ready for more, check out:

- **Installation**: A deeper dive into advanced installs, Docker usage (experimental), or optional dependencies.  
- **Hooks & Auth**: Learn how to run custom JavaScript or handle logins with cookies, local storage, etc.  
- **Deployment**: Explore ephemeral testing in Docker or plan for the upcoming stable Docker release.  
- **Browser Management**: Delve into user simulation, stealth modes, and concurrency best practices.  

Crawl4AI is a powerful, flexible tool. Enjoy building out your scrapers, data pipelines, or AI-driven extraction flows. Happy crawling!
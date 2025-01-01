# Getting Started with Crawl4AI

Welcome to **Crawl4AI**, an open-source LLM friendly Web Crawler & Scraper. In this tutorial, you’ll:

1. **Install** Crawl4AI (both via pip and Docker, with notes on platform challenges).
2. Run your **first crawl** using minimal configuration.
3. Generate **Markdown** output (and learn how it’s influenced by content filters).
4. Experiment with a simple **CSS-based extraction** strategy.
5. See a glimpse of **LLM-based extraction** (including open-source and closed-source model options).

---

## 1. Introduction

Crawl4AI provides:
- An asynchronous crawler, **`AsyncWebCrawler`**.
- Configurable browser and run settings via **`BrowserConfig`** and **`CrawlerRunConfig`**.
- Automatic HTML-to-Markdown conversion via **`DefaultMarkdownGenerator`** (supports additional filters).
- Multiple extraction strategies (LLM-based or “traditional” CSS/XPath-based).

By the end of this guide, you’ll have installed Crawl4AI, performed a basic crawl, generated Markdown, and tried out two extraction strategies.

---

## 2. Installation

### 2.1 Python + Playwright

#### Basic Pip Installation

```bash
pip install crawl4ai
crawl4ai-setup

# Verify your installation
crawl4ai-doctor
```

If you encounter any browser-related issues, you can install them manually:
```bash
python -m playwright install --with-deps chrome chromium
```

- **`crawl4ai-setup`** installs and configures Playwright (Chromium by default).

We cover advanced installation and Docker in the [Installation](#installation) section.

---

## 3. Your First Crawl

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

## 4. Basic Configuration (Light Introduction)

Crawl4AI’s crawler can be heavily customized using two main classes:

1. **`BrowserConfig`**: Controls browser behavior (headless or full UI, user agent, JavaScript toggles, etc.).
2. **`CrawlerRunConfig`**: Controls how each crawl runs (caching, extraction, timeouts, hooking, etc.).

Below is an example with minimal usage:

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    browser_conf = BrowserConfig(headless=True)  # or False to see the browser
    run_conf = CrawlerRunConfig(cache_mode="BYPASS")

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_conf
        )
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
```

We’ll explore more advanced config in later tutorials (like enabling proxies, PDF output, multi-tab sessions, etc.). For now, just note how you pass these objects to manage crawling.

---

## 5. Generating Markdown Output

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

config = CrawlerRunConfig(markdown_generator=md_generator)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://news.ycombinator.com", config=config)
    print("Raw Markdown length:", len(result.markdown.raw_markdown))
    print("Fit Markdown length:", len(result.markdown.fit_markdown))
```

**Note**: If you do **not** specify a content filter or markdown generator, you’ll typically see only the raw Markdown. We’ll dive deeper into these strategies in a dedicated **Markdown Generation** tutorial.

---

## 6. Simple Data Extraction (CSS-based)

Crawl4AI can also extract structured data (JSON) using CSS or XPath selectors. Below is a minimal CSS-based example:

```python
import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
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

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com/items",
            config=CrawlerRunConfig(
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

---

## 7. Simple Data Extraction (LLM-based)

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

class PricingInfo(BaseModel):
    model_name: str = Field(..., description="Name of the AI model")
    input_fee: str = Field(..., description="Fee for input tokens")
    output_fee: str = Field(..., description="Fee for output tokens")

async def main():
    # 1) Open-Source usage: no token required
    llm_strategy_open_source = LLMExtractionStrategy(
        provider="ollama/llama3.3",  # or "any-other-local-model"
        api_token="no_token",       # for local models, no API key is typically required
        schema=PricingInfo.schema(),
        extraction_type="schema",
        instruction="""
            From this page, extract all AI model pricing details in JSON format.
            Each entry should have 'model_name', 'input_fee', and 'output_fee'.
        """,
        temperature=0
    )

    # 2) Closed-Source usage: API key for OpenAI, for example
    openai_token = os.getenv("OPENAI_API_KEY", "sk-YOUR_API_KEY")
    llm_strategy_openai = LLMExtractionStrategy(
        provider="openai/gpt-4",
        api_token=openai_token,
        schema=PricingInfo.schema(),
        extraction_type="schema",
        instruction="""
            From this page, extract all AI model pricing details in JSON format.
            Each entry should have 'model_name', 'input_fee', and 'output_fee'.
        """,
        temperature=0
    )

    # We'll demo the open-source approach here
    config = CrawlerRunConfig(extraction_strategy=llm_strategy_open_source)

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://example.com/pricing",
            config=config
        )
        print("LLM-based extraction JSON:", result.extracted_content)

if __name__ == "__main__":
    asyncio.run(main())
```

**What’s happening?**
- We define a Pydantic schema (`PricingInfo`) describing the fields we want.
- The LLM extraction strategy uses that schema and your instructions to transform raw text into structured JSON.  
- Depending on the **provider** and **api_token**, you can use local models or a remote API.

---

## 8. Next Steps

Congratulations! You have:
1. Installed Crawl4AI (via pip, with Docker as an option).
2. Performed a simple crawl and printed Markdown.
3. Seen how adding a **markdown generator** + **content filter** can produce “fit” Markdown.
4. Experimented with **CSS-based** extraction for repetitive data.
5. Learned the basics of **LLM-based** extraction (open-source and closed-source).

If you are ready for more, check out:

- **Installation**: Learn more on how to install Crawl4AI and set up Playwright.
- **Focus on Configuration**: Learn to customize browser settings, caching modes, advanced timeouts, etc.
- **Markdown Generation Basics**: Dive deeper into content filtering and “fit markdown” usage.
- **Dynamic Pages & Hooks**: Tackle sites with “Load More” buttons, login forms, or JavaScript complexities.
- **Deployment**: Run Crawl4AI in Docker containers and scale across multiple nodes.
- **Explanations & How-To Guides**: Explore browser contexts, identity-based crawling, hooking, performance, and more.

Crawl4AI is a powerful tool for extracting data and generating Markdown from virtually any website. Enjoy exploring, and we hope you build amazing AI-powered applications with it!

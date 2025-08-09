# 🚀🤖 Crawl4AI: Open-source LLM Friendly Web Crawler & Scraper.

<div align="center">

<a href="https://trendshift.io/repositories/11716" target="_blank"><img src="https://trendshift.io/api/badge/repositories/11716" alt="unclecode%2Fcrawl4ai | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

[![GitHub Stars](https://img.shields.io/github/stars/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/network/members)

[![PyPI version](https://badge.fury.io/py/crawl4ai.svg)](https://badge.fury.io/py/crawl4ai)
[![Python Version](https://img.shields.io/pypi/pyversions/crawl4ai)](https://pypi.org/project/crawl4ai/)
[![Downloads](https://static.pepy.tech/badge/crawl4ai/month)](https://pepy.tech/project/crawl4ai)
[![GitHub Sponsors](https://img.shields.io/github/sponsors/unclecode?style=flat&logo=GitHub-Sponsors&label=Sponsors&color=pink)](https://github.com/sponsors/unclecode)

<p align="center">
    <a href="https://x.com/crawl4ai">
      <img src="https://img.shields.io/badge/Follow%20on%20X-000000?style=for-the-badge&logo=x&logoColor=white" alt="Follow on X" />
    </a>
    <a href="https://www.linkedin.com/company/crawl4ai">
      <img src="https://img.shields.io/badge/Follow%20on%20LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="Follow on LinkedIn" />
    </a>
    <a href="https://discord.gg/jP8KfhDhyN">
      <img src="https://img.shields.io/badge/Join%20our%20Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Join our Discord" />
    </a>
  </p>
</div>

Crawl4AI turns the web into clean, LLM ready Markdown for RAG, agents, and data pipelines. Fast, controllable, battle tested by a 50k+ star community.

[✨ Check out latest update v0.7.0](#-recent-updates)

✨ New in v0.7.0, Adaptive Crawling, Virtual Scroll, Link Preview scoring, Async URL Seeder, big performance gains. [Release notes →](https://github.com/unclecode/crawl4ai/blob/main/docs/blog/release-v0.7.0.md)

<details>
  <summary>🤓 <strong>My Personal Story</strong></summary>

I grew up on an Amstrad, thanks to my dad, and never stopped building. In grad school I specialized in NLP and built crawlers for research. That’s where I learned how much extraction matters.

In 2023, I needed web-to-Markdown. The “open source” option wanted an account, API token, and $16, and still under-delivered. I went turbo anger mode, built Crawl4AI in days, and it went viral. Now it’s the most-starred crawler on GitHub.

I made it open source for **availability**, anyone can use it without a gate. Now I’m building the platform for **affordability**, anyone can run serious crawls without breaking the bank. If that resonates, join in, send feedback, or just crawl something amazing.
</details>


<details>
  <summary>Why developers pick Crawl4AI</summary>

- **LLM ready output**, smart Markdown with headings, tables, code, citation hints
- **Fast in practice**, async browser pool, caching, minimal hops
- **Full control**, sessions, proxies, cookies, user scripts, hooks
- **Adaptive intelligence**, learns site patterns, explores only what matters
- **Deploy anywhere**, zero keys, CLI and Docker, cloud friendly
</details>


## 🚀 Quick Start 

1. Install Crawl4AI:
```bash
# Install the package
pip install -U crawl4ai

# For pre release versions
pip install crawl4ai --pre

# Run post-installation setup
crawl4ai-setup

# Verify your installation
crawl4ai-doctor
```

If you encounter any browser-related issues, you can install them manually:
```bash
python -m playwright install --with-deps chromium
```

2. Run a simple web crawl with Python:
```python
import asyncio
from crawl4ai import *

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
        )
        print(result.markdown)

if __name__ == "__main__":
    asyncio.run(main())
```

3. Or use the new command-line interface:
```bash
# Basic crawl with markdown output
crwl https://www.nbcnews.com/business -o markdown

# Deep crawl with BFS strategy, max 10 pages
crwl https://docs.crawl4ai.com --deep-crawl bfs --max-pages 10

# Use LLM extraction with a specific question
crwl https://www.example.com/products -q "Extract all product prices"
```

## 💖 Support Crawl4AI

> 🎉 **Sponsorship Program Now Open!** After powering 51K+ developers and 1 year of growth, Crawl4AI is launching dedicated support for **startups** and **enterprises**. Be among the first 50 **Founding Sponsors** for permanent recognition in our Hall of Fame.

Crawl4AI is the #1 trending open-source web crawler on GitHub. Your support keeps it independent, innovative, and free for the community — while giving you direct access to premium benefits.

<div align="">
  
[![Become a Sponsor](https://img.shields.io/badge/Become%20a%20Sponsor-pink?style=for-the-badge&logo=github-sponsors&logoColor=white)](https://github.com/sponsors/unclecode)  
[![Current Sponsors](https://img.shields.io/github/sponsors/unclecode?style=for-the-badge&logo=github&label=Current%20Sponsors&color=green)](https://github.com/sponsors/unclecode)

</div>

### 🤝 Sponsorship Tiers

- **🌱 Believer ($5/mo)** — Join the movement for data democratization  
- **🚀 Builder ($50/mo)** — Priority support & early access to features  
- **💼 Growing Team ($500/mo)** — Bi-weekly syncs & optimization help  
- **🏢 Data Infrastructure Partner ($2000/mo)** — Full partnership with dedicated support  
  *Custom arrangements available - see [SPONSORS.md](SPONSORS.md) for details & contact*

**Why sponsor?**  
No rate-limited APIs. No lock-in. Build and own your data pipeline with direct guidance from the creator of Crawl4AI.

[See All Tiers & Benefits →](https://github.com/sponsors/unclecode)


## ✨ Features 

<details>
<summary>📝 <strong>Markdown Generation</strong></summary>

- 🧹 **Clean Markdown**: Generates clean, structured Markdown with accurate formatting.
- 🎯 **Fit Markdown**: Heuristic-based filtering to remove noise and irrelevant parts for AI-friendly processing.
- 🔗 **Citations and References**: Converts page links into a numbered reference list with clean citations.
- 🛠️ **Custom Strategies**: Users can create their own Markdown generation strategies tailored to specific needs.
- 📚 **BM25 Algorithm**: Employs BM25-based filtering for extracting core information and removing irrelevant content. 
</details>

<details>
<summary>📊 <strong>Structured Data Extraction</strong></summary>

- 🤖 **LLM-Driven Extraction**: Supports all LLMs (open-source and proprietary) for structured data extraction.
- 🧱 **Chunking Strategies**: Implements chunking (topic-based, regex, sentence-level) for targeted content processing.
- 🌌 **Cosine Similarity**: Find relevant content chunks based on user queries for semantic extraction.
- 🔎 **CSS-Based Extraction**: Fast schema-based data extraction using XPath and CSS selectors.
- 🔧 **Schema Definition**: Define custom schemas for extracting structured JSON from repetitive patterns.

</details>

<details>
<summary>🌐 <strong>Browser Integration</strong></summary>

- 🖥️ **Managed Browser**: Use user-owned browsers with full control, avoiding bot detection.
- 🔄 **Remote Browser Control**: Connect to Chrome Developer Tools Protocol for remote, large-scale data extraction.
- 👤 **Browser Profiler**: Create and manage persistent profiles with saved authentication states, cookies, and settings.
- 🔒 **Session Management**: Preserve browser states and reuse them for multi-step crawling.
- 🧩 **Proxy Support**: Seamlessly connect to proxies with authentication for secure access.
- ⚙️ **Full Browser Control**: Modify headers, cookies, user agents, and more for tailored crawling setups.
- 🌍 **Multi-Browser Support**: Compatible with Chromium, Firefox, and WebKit.
- 📐 **Dynamic Viewport Adjustment**: Automatically adjusts the browser viewport to match page content, ensuring complete rendering and capturing of all elements.

</details>

<details>
<summary>🔎 <strong>Crawling & Scraping</strong></summary>

- 🖼️ **Media Support**: Extract images, audio, videos, and responsive image formats like `srcset` and `picture`.
- 🚀 **Dynamic Crawling**: Execute JS and wait for async or sync for dynamic content extraction.
- 📸 **Screenshots**: Capture page screenshots during crawling for debugging or analysis.
- 📂 **Raw Data Crawling**: Directly process raw HTML (`raw:`) or local files (`file://`).
- 🔗 **Comprehensive Link Extraction**: Extracts internal, external links, and embedded iframe content.
- 🛠️ **Customizable Hooks**: Define hooks at every step to customize crawling behavior.
- 💾 **Caching**: Cache data for improved speed and to avoid redundant fetches.
- 📄 **Metadata Extraction**: Retrieve structured metadata from web pages.
- 📡 **IFrame Content Extraction**: Seamless extraction from embedded iframe content.
- 🕵️ **Lazy Load Handling**: Waits for images to fully load, ensuring no content is missed due to lazy loading.
- 🔄 **Full-Page Scanning**: Simulates scrolling to load and capture all dynamic content, perfect for infinite scroll pages.

</details>

<details>
<summary>🚀 <strong>Deployment</strong></summary>

- 🐳 **Dockerized Setup**: Optimized Docker image with FastAPI server for easy deployment.
- 🔑 **Secure Authentication**: Built-in JWT token authentication for API security.
- 🔄 **API Gateway**: One-click deployment with secure token authentication for API-based workflows.
- 🌐 **Scalable Architecture**: Designed for mass-scale production and optimized server performance.
- ☁️ **Cloud Deployment**: Ready-to-deploy configurations for major cloud platforms.

</details>

<details>
<summary>🎯 <strong>Additional Features</strong></summary>

- 🕶️ **Stealth Mode**: Avoid bot detection by mimicking real users.
- 🏷️ **Tag-Based Content Extraction**: Refine crawling based on custom tags, headers, or metadata.
- 🔗 **Link Analysis**: Extract and analyze all links for detailed data exploration.
- 🛡️ **Error Handling**: Robust error management for seamless execution.
- 🔐 **CORS & Static Serving**: Supports filesystem-based caching and cross-origin requests.
- 📖 **Clear Documentation**: Simplified and updated guides for onboarding and advanced usage.
- 🙌 **Community Recognition**: Acknowledges contributors and pull requests for transparency.

</details>

## Try it Now!

✨ Play around with this [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1SgRPrByQLzjRfwoRNq1wSGE9nYY_EE8C?usp=sharing)

✨ Visit our [Documentation Website](https://docs.crawl4ai.com/)

## Installation 🛠️

Crawl4AI offers flexible installation options to suit various use cases. You can install it as a Python package or use Docker.

<details>
<summary>🐍 <strong>Using pip</strong></summary>

Choose the installation option that best fits your needs:

### Basic Installation

For basic web crawling and scraping tasks:

```bash
pip install crawl4ai
crawl4ai-setup # Setup the browser
```

By default, this will install the asynchronous version of Crawl4AI, using Playwright for web crawling.

👉 **Note**: When you install Crawl4AI, the `crawl4ai-setup` should automatically install and set up Playwright. However, if you encounter any Playwright-related errors, you can manually install it using one of these methods:

1. Through the command line:

   ```bash
   playwright install
   ```

2. If the above doesn't work, try this more specific command:

   ```bash
   python -m playwright install chromium
   ```

This second method has proven to be more reliable in some cases.

---

### Installation with Synchronous Version

The sync version is deprecated and will be removed in future versions. If you need the synchronous version using Selenium:

```bash
pip install crawl4ai[sync]
```

---

### Development Installation

For contributors who plan to modify the source code:

```bash
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai
pip install -e .                    # Basic installation in editable mode
```

Install optional features:

```bash
pip install -e ".[torch]"           # With PyTorch features
pip install -e ".[transformer]"     # With Transformer features
pip install -e ".[cosine]"          # With cosine similarity features
pip install -e ".[sync]"            # With synchronous crawling (Selenium)
pip install -e ".[all]"             # Install all optional features
```

</details>

<details>
<summary>🐳 <strong>Docker Deployment</strong></summary>

> 🚀 **Now Available!** Our completely redesigned Docker implementation is here! This new solution makes deployment more efficient and seamless than ever.

### New Docker Features

The new Docker implementation includes:
- **Browser pooling** with page pre-warming for faster response times
- **Interactive playground** to test and generate request code
- **MCP integration** for direct connection to AI tools like Claude Code
- **Comprehensive API endpoints** including HTML extraction, screenshots, PDF generation, and JavaScript execution
- **Multi-architecture support** with automatic detection (AMD64/ARM64)
- **Optimized resources** with improved memory management

### Getting Started

```bash
# Pull and run the latest release candidate
docker pull unclecode/crawl4ai:0.7.0
docker run -d -p 11235:11235 --name crawl4ai --shm-size=1g unclecode/crawl4ai:0.7.0

# Visit the playground at http://localhost:11235/playground
```

### Quick Test

Run a quick test (works for both Docker options):

```python
import requests

# Submit a crawl job
response = requests.post(
    "http://localhost:11235/crawl",
    json={"urls": ["https://example.com"], "priority": 10}
)
if response.status_code == 200:
    print("Crawl job submitted successfully.")
    
if "results" in response.json():
    results = response.json()["results"]
    print("Crawl job completed. Results:")
    for result in results:
        print(result)
else:
    task_id = response.json()["task_id"]
    print(f"Crawl job submitted. Task ID:: {task_id}")
    result = requests.get(f"http://localhost:11235/task/{task_id}")
```

For more examples, see our [Docker Examples](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/docker_example.py). For advanced configuration, environment variables, and usage examples, see our [Docker Deployment Guide](https://docs.crawl4ai.com/basic/docker-deployment/).

</details>

---

## 🔬 Advanced Usage Examples 🔬

You can check the project structure in the directory [docs/examples](https://github.com/unclecode/crawl4ai/tree/main/docs/examples). Over there, you can find a variety of examples; here, some popular examples are shared.

<details>
<summary>📝 <strong>Heuristic Markdown Generation with Clean and Fit Markdown</strong></summary>

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

async def main():
    browser_config = BrowserConfig(
        headless=True,  
        verbose=True,
    )
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.ENABLED,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.48, threshold_type="fixed", min_word_threshold=0)
        ),
        # markdown_generator=DefaultMarkdownGenerator(
        #     content_filter=BM25ContentFilter(user_query="WHEN_WE_FOCUS_BASED_ON_A_USER_QUERY", bm25_threshold=1.0)
        # ),
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://docs.micronaut.io/4.7.6/guide/",
            config=run_config
        )
        print(len(result.markdown.raw_markdown))
        print(len(result.markdown.fit_markdown))

if __name__ == "__main__":
    asyncio.run(main())
```

</details>

<details>
<summary>🖥️ <strong>Executing JavaScript & Extract Structured Data without LLMs</strong></summary>

```python
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy
import json

async def main():
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
            "attribute": "src"
        }
    }
}

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    browser_config = BrowserConfig(
        headless=False,
        verbose=True
    )
    run_config = CrawlerRunConfig(
        extraction_strategy=extraction_strategy,
        js_code=["""(async () => {const tabs = document.querySelectorAll("section.charge-methodology .tabs-menu-3 > div");for(let tab of tabs) {tab.scrollIntoView();tab.click();await new Promise(r => setTimeout(r, 500));}})();"""],
        cache_mode=CacheMode.BYPASS
    )
        
    async with AsyncWebCrawler(config=browser_config) as crawler:
        
        result = await crawler.arun(
            url="https://www.kidocode.com/degrees/technology",
            config=run_config
        )

        companies = json.loads(result.extracted_content)
        print(f"Successfully extracted {len(companies)} companies")
        print(json.dumps(companies[0], indent=2))


if __name__ == "__main__":
    asyncio.run(main())
```

</details>

<details>
<summary>📚 <strong>Extracting Structured Data with LLMs</strong></summary>

```python
import os
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai import LLMExtractionStrategy
from pydantic import BaseModel, Field

class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(..., description="Fee for output token for the OpenAI model.")

async def main():
    browser_config = BrowserConfig(verbose=True)
    run_config = CrawlerRunConfig(
        word_count_threshold=1,
        extraction_strategy=LLMExtractionStrategy(
            # Here you can use any provider that Litellm library supports, for instance: ollama/qwen2
            # provider="ollama/qwen2", api_token="no-token", 
            llm_config = LLMConfig(provider="openai/gpt-4o", api_token=os.getenv('OPENAI_API_KEY')), 
            schema=OpenAIModelFee.schema(),
            extraction_type="schema",
            instruction="""From the crawled content, extract all mentioned model names along with their fees for input and output tokens. 
            Do not miss any models in the entire content. One extracted model JSON format should look like this: 
            {"model_name": "GPT-4", "input_fee": "US$10.00 / 1M tokens", "output_fee": "US$30.00 / 1M tokens"}."""
        ),            
        cache_mode=CacheMode.BYPASS,
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url='https://openai.com/api/pricing/',
            config=run_config
        )
        print(result.extracted_content)

if __name__ == "__main__":
    asyncio.run(main())
```

</details>

<details>
<summary>🤖 <strong>Using Your own Browser with Custom User Profile</strong></summary>

```python
import os, sys
from pathlib import Path
import asyncio, time
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

async def test_news_crawl():
    # Create a persistent user data directory
    user_data_dir = os.path.join(Path.home(), ".crawl4ai", "browser_profile")
    os.makedirs(user_data_dir, exist_ok=True)

    browser_config = BrowserConfig(
        verbose=True,
        headless=True,
        user_data_dir=user_data_dir,
        use_persistent_context=True,
    )
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        url = "ADDRESS_OF_A_CHALLENGING_WEBSITE"
        
        result = await crawler.arun(
            url,
            config=run_config,
            magic=True,
        )
        
        print(f"Successfully crawled {url}")
        print(f"Content length: {len(result.markdown)}")
```

</details>

## ✨ Recent Updates

### Version 0.7.0 Release Highlights - The Adaptive Intelligence Update

- **🧠 Adaptive Crawling**: Your crawler now learns and adapts to website patterns automatically:
  ```python
  config = AdaptiveConfig(
      confidence_threshold=0.7, # Min confidence to stop crawling
      max_depth=5, # Maximum crawl depth
      max_pages=20, # Maximum number of pages to crawl
      strategy="statistical"
  )
  
  async with AsyncWebCrawler() as crawler:
      adaptive_crawler = AdaptiveCrawler(crawler, config)
      state = await adaptive_crawler.digest(
          start_url="https://news.example.com",
          query="latest news content"
      )
  # Crawler learns patterns and improves extraction over time
  ```

- **🌊 Virtual Scroll Support**: Complete content extraction from infinite scroll pages:
  ```python
  scroll_config = VirtualScrollConfig(
      container_selector="[data-testid='feed']",
      scroll_count=20,
      scroll_by="container_height",
      wait_after_scroll=1.0
  )
  
  result = await crawler.arun(url, config=CrawlerRunConfig(
      virtual_scroll_config=scroll_config
  ))
  ```

- **🔗 Intelligent Link Analysis**: 3-layer scoring system for smart link prioritization:
  ```python
  link_config = LinkPreviewConfig(
      query="machine learning tutorials",
      score_threshold=0.3,
      concurrent_requests=10
  )
  
  result = await crawler.arun(url, config=CrawlerRunConfig(
      link_preview_config=link_config,
      score_links=True
  ))
  # Links ranked by relevance and quality
  ```

- **🎣 Async URL Seeder**: Discover thousands of URLs in seconds:
  ```python
  seeder = AsyncUrlSeeder(SeedingConfig(
      source="sitemap+cc",
      pattern="*/blog/*",
      query="python tutorials",
      score_threshold=0.4
  ))
  
  urls = await seeder.discover("https://example.com")
  ```

- **⚡ Performance Boost**: Up to 3x faster with optimized resource handling and memory efficiency

Read the full details in our [0.7.0 Release Notes](https://docs.crawl4ai.com/blog/release-v0.7.0) or check the [CHANGELOG](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md).

## Version Numbering in Crawl4AI

Crawl4AI follows standard Python version numbering conventions (PEP 440) to help users understand the stability and features of each release.

<details>
<summary>📈 <strong>Version Numbers Explained</strong></summary>

Our version numbers follow this pattern: `MAJOR.MINOR.PATCH` (e.g., 0.4.3)

#### Pre-release Versions
We use different suffixes to indicate development stages:

- `dev` (0.4.3dev1): Development versions, unstable
- `a` (0.4.3a1): Alpha releases, experimental features
- `b` (0.4.3b1): Beta releases, feature complete but needs testing
- `rc` (0.4.3): Release candidates, potential final version

#### Installation
- Regular installation (stable version):
  ```bash
  pip install -U crawl4ai
  ```

- Install pre-release versions:
  ```bash
  pip install crawl4ai --pre
  ```

- Install specific version:
  ```bash
  pip install crawl4ai==0.4.3b1
  ```

#### Why Pre-releases?
We use pre-releases to:
- Test new features in real-world scenarios
- Gather feedback before final releases
- Ensure stability for production users
- Allow early adopters to try new features

For production environments, we recommend using the stable version. For testing new features, you can opt-in to pre-releases using the `--pre` flag.

</details>

## 📖 Documentation & Roadmap 

> 🚨 **Documentation Update Alert**: We're undertaking a major documentation overhaul next week to reflect recent updates and improvements. Stay tuned for a more comprehensive and up-to-date guide!

For current documentation, including installation instructions, advanced features, and API reference, visit our [Documentation Website](https://docs.crawl4ai.com/).

To check our development plans and upcoming features, visit our [Roadmap](https://github.com/unclecode/crawl4ai/blob/main/ROADMAP.md).

<details>
<summary>📈 <strong>Development TODOs</strong></summary>

- [x] 0. Graph Crawler: Smart website traversal using graph search algorithms for comprehensive nested page extraction
- [x] 1. Question-Based Crawler: Natural language driven web discovery and content extraction
- [x] 2. Knowledge-Optimal Crawler: Smart crawling that maximizes knowledge while minimizing data extraction
- [x] 3. Agentic Crawler: Autonomous system for complex multi-step crawling operations
- [x] 4. Automated Schema Generator: Convert natural language to extraction schemas
- [x] 5. Domain-Specific Scrapers: Pre-configured extractors for common platforms (academic, e-commerce)
- [x] 6. Web Embedding Index: Semantic search infrastructure for crawled content
- [x] 7. Interactive Playground: Web UI for testing, comparing strategies with AI assistance
- [x] 8. Performance Monitor: Real-time insights into crawler operations
- [ ] 9. Cloud Integration: One-click deployment solutions across cloud providers
- [x] 10. Sponsorship Program: Structured support system with tiered benefits
- [ ] 11. Educational Content: "How to Crawl" video series and interactive tutorials

</details>

## 🤝 Contributing 

We welcome contributions from the open-source community. Check out our [contribution guidelines](https://github.com/unclecode/crawl4ai/blob/main/CONTRIBUTORS.md) for more information.

I'll help modify the license section with badges. For the halftone effect, here's a version with it:

Here's the updated license section:

## 📄 License & Attribution

This project is licensed under the Apache License 2.0, attribution is recommended via the badges below. See the [Apache 2.0 License](https://github.com/unclecode/crawl4ai/blob/main/LICENSE) file for details.

### Attribution Requirements
When using Crawl4AI, you must include one of the following attribution methods:

<details>
<summary>📈 <strong>1. Badge Attribution (Recommended)</strong></summary>
Add one of these badges to your README, documentation, or website:

| Theme | Badge |
|-------|-------|
| **Disco Theme (Animated)** | <a href="https://github.com/unclecode/crawl4ai"><img src="./docs/assets/powered-by-disco.svg" alt="Powered by Crawl4AI" width="200"/></a> |
| **Night Theme (Dark with Neon)** | <a href="https://github.com/unclecode/crawl4ai"><img src="./docs/assets/powered-by-night.svg" alt="Powered by Crawl4AI" width="200"/></a> |
| **Dark Theme (Classic)** | <a href="https://github.com/unclecode/crawl4ai"><img src="./docs/assets/powered-by-dark.svg" alt="Powered by Crawl4AI" width="200"/></a> |
| **Light Theme (Classic)** | <a href="https://github.com/unclecode/crawl4ai"><img src="./docs/assets/powered-by-light.svg" alt="Powered by Crawl4AI" width="200"/></a> |
 

HTML code for adding the badges:
```html
<!-- Disco Theme (Animated) -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/powered-by-disco.svg" alt="Powered by Crawl4AI" width="200"/>
</a>

<!-- Night Theme (Dark with Neon) -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/powered-by-night.svg" alt="Powered by Crawl4AI" width="200"/>
</a>

<!-- Dark Theme (Classic) -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/powered-by-dark.svg" alt="Powered by Crawl4AI" width="200"/>
</a>

<!-- Light Theme (Classic) -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/assets/powered-by-light.svg" alt="Powered by Crawl4AI" width="200"/>
</a>

<!-- Simple Shield Badge -->
<a href="https://github.com/unclecode/crawl4ai">
  <img src="https://img.shields.io/badge/Powered%20by-Crawl4AI-blue?style=flat-square" alt="Powered by Crawl4AI"/>
</a>
```

</details>

<details>
<summary>📖 <strong>2. Text Attribution</strong></summary>
Add this line to your documentation:
```
This project uses Crawl4AI (https://github.com/unclecode/crawl4ai) for web data extraction.
```
</details>

## 📚 Citation

If you use Crawl4AI in your research or project, please cite:

```bibtex
@software{crawl4ai2024,
  author = {UncleCode},
  title = {Crawl4AI: Open-source LLM Friendly Web Crawler & Scraper},
  year = {2024},
  publisher = {GitHub},
  journal = {GitHub Repository},
  howpublished = {\url{https://github.com/unclecode/crawl4ai}},
  commit = {Please use the commit hash you're working with}
}
```

Text citation format:
```
UncleCode. (2024). Crawl4AI: Open-source LLM Friendly Web Crawler & Scraper [Computer software]. 
GitHub. https://github.com/unclecode/crawl4ai
```

## 📧 Contact 

For questions, suggestions, or feedback, feel free to reach out:

- GitHub: [unclecode](https://github.com/unclecode)
- Twitter: [@unclecode](https://twitter.com/unclecode)
- Website: [crawl4ai.com](https://crawl4ai.com)

Happy Crawling! 🕸️🚀

## 🗾 Mission

Our mission is to unlock the value of personal and enterprise data by transforming digital footprints into structured, tradeable assets. Crawl4AI empowers individuals and organizations with open-source tools to extract and structure data, fostering a shared data economy.  

We envision a future where AI is powered by real human knowledge, ensuring data creators directly benefit from their contributions. By democratizing data and enabling ethical sharing, we are laying the foundation for authentic AI advancement.

<details>
<summary>🔑 <strong>Key Opportunities</strong></summary>
 
- **Data Capitalization**: Transform digital footprints into measurable, valuable assets.  
- **Authentic AI Data**: Provide AI systems with real human insights.  
- **Shared Economy**: Create a fair data marketplace that benefits data creators.  

</details>

<details>
<summary>🚀 <strong>Development Pathway</strong></summary>

1. **Open-Source Tools**: Community-driven platforms for transparent data extraction.  
2. **Digital Asset Structuring**: Tools to organize and value digital knowledge.  
3. **Ethical Data Marketplace**: A secure, fair platform for exchanging structured data.  

For more details, see our [full mission statement](./MISSION.md).
</details>

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=unclecode/crawl4ai&type=Date)](https://star-history.com/#unclecode/crawl4ai&Date)

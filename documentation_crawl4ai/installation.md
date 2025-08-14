[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/core/installation/)


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
    * Installation
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
    * [Content Selection](https://docs.crawl4ai.com/core/content-selection/)
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
  * [Installation & Setup (2023 Edition)](https://docs.crawl4ai.com/core/installation/#installation-setup-2023-edition)
  * [1. Basic Installation](https://docs.crawl4ai.com/core/installation/#1-basic-installation)
  * [2. Initial Setup & Diagnostics](https://docs.crawl4ai.com/core/installation/#2-initial-setup-diagnostics)
  * [3. Verifying Installation: A Simple Crawl (Skip this step if you already run crawl4ai-doctor)](https://docs.crawl4ai.com/core/installation/#3-verifying-installation-a-simple-crawl-skip-this-step-if-you-already-run-crawl4ai-doctor)
  * [4. Advanced Installation (Optional)](https://docs.crawl4ai.com/core/installation/#4-advanced-installation-optional)
  * [5. Docker (Experimental)](https://docs.crawl4ai.com/core/installation/#5-docker-experimental)
  * [6. Local Server Mode (Legacy)](https://docs.crawl4ai.com/core/installation/#6-local-server-mode-legacy)
  * [Summary](https://docs.crawl4ai.com/core/installation/#summary)


# Installation & Setup (2023 Edition)
## 1. Basic Installation
```
pip install crawl4ai
Copy
```

This installs the **core** Crawl4AI library along with essential dependencies. **No** advanced features (like transformers or PyTorch) are included yet.
## 2. Initial Setup & Diagnostics
### 2.1 Run the Setup Command
After installing, call:
```
crawl4ai-setup
Copy
```

**What does it do?** - Installs or updates required browser dependencies for both regular and undetected modes - Performs OS-level checks (e.g., missing libs on Linux) - Confirms your environment is ready to crawl
### 2.2 Diagnostics
Optionally, you can run **diagnostics** to confirm everything is functioning:
```
crawl4ai-doctor
Copy
```

This command attempts to: - Check Python version compatibility - Verify Playwright installation - Inspect environment variables or library conflicts
If any issues arise, follow its suggestions (e.g., installing additional system packages) and re-run `crawl4ai-setup`.
* * *
## 3. Verifying Installation: A Simple Crawl (Skip this step if you already run `crawl4ai-doctor`)
Below is a minimal Python script demonstrating a **basic** crawl. It uses our new **`BrowserConfig`**and**`CrawlerRunConfig`**for clarity, though no custom settings are passed in this example:
```
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.example.com",
        )
        print(result.markdown[:300])  # Show the first 300 characters of extracted text

if __name__ == "__main__":
    asyncio.run(main())
Copy
```

**Expected** outcome: - A headless browser session loads `example.com` - Crawl4AI returns ~300 characters of markdown.
If errors occur, rerun `crawl4ai-doctor` or manually ensure Playwright is installed correctly.
* * *
## 4. Advanced Installation (Optional)
**Warning** : Only install these **if you truly need them**. They bring in larger dependencies, including big models, which can increase disk usage and memory load significantly.
### 4.1 Torch, Transformers, or All
  * **Text Clustering (Torch)**

```
pip install crawl4ai[torch]
crawl4ai-setup
Copy
```

Installs PyTorch-based features (e.g., cosine similarity or advanced semantic chunking).
  * **Transformers**

```
pip install crawl4ai[transformer]
crawl4ai-setup
Copy
```

Adds Hugging Face-based summarization or generation strategies.
  * **All Features**

```
pip install crawl4ai[all]
crawl4ai-setup
Copy
```



#### (Optional) Pre-Fetching Models
```
crawl4ai-download-models
Copy
```

This step caches large models locally (if needed). **Only do this** if your workflow requires them.
* * *
## 5. Docker (Experimental)
We provide a **temporary** Docker approach for testing. **It’s not stable and may break** with future releases. We plan a major Docker revamp in a future stable version, 2025 Q1. If you still want to try:
```
docker pull unclecode/crawl4ai:basic
docker run -p 11235:11235 unclecode/crawl4ai:basic
Copy
```

You can then make POST requests to `http://localhost:11235/crawl` to perform crawls. **Production usage** is discouraged until our new Docker approach is ready (planned in Jan or Feb 2025).
* * *
## 6. Local Server Mode (Legacy)
Some older docs mention running Crawl4AI as a local server. This approach has been **partially replaced** by the new Docker-based prototype and upcoming stable server release. You can experiment, but expect major changes. Official local server instructions will arrive once the new Docker architecture is finalized.
* * *
## Summary
1. **Install** with `pip install crawl4ai` and run `crawl4ai-setup`. 2. **Diagnose** with `crawl4ai-doctor` if you see errors. 3. **Verify** by crawling `example.com` with minimal `BrowserConfig` + `CrawlerRunConfig`. 4. **Advanced** features (Torch, Transformers) are **optional** —avoid them if you don’t need them (they significantly increase resource usage). 5. **Docker** is **experimental** —use at your own risk until the stable version is released. 6. **Local server** references in older docs are largely deprecated; a new solution is in progress.
**Got questions?** Check [GitHub issues](https://github.com/unclecode/crawl4ai/issues) for updates or ask the community!
#### On this page
  * [1. Basic Installation](https://docs.crawl4ai.com/core/installation/#1-basic-installation)
  * [2. Initial Setup & Diagnostics](https://docs.crawl4ai.com/core/installation/#2-initial-setup-diagnostics)
  * [2.1 Run the Setup Command](https://docs.crawl4ai.com/core/installation/#21-run-the-setup-command)
  * [2.2 Diagnostics](https://docs.crawl4ai.com/core/installation/#22-diagnostics)
  * [3. Verifying Installation: A Simple Crawl (Skip this step if you already run crawl4ai-doctor)](https://docs.crawl4ai.com/core/installation/#3-verifying-installation-a-simple-crawl-skip-this-step-if-you-already-run-crawl4ai-doctor)
  * [4. Advanced Installation (Optional)](https://docs.crawl4ai.com/core/installation/#4-advanced-installation-optional)
  * [4.1 Torch, Transformers, or All](https://docs.crawl4ai.com/core/installation/#41-torch-transformers-or-all)
  * [(Optional) Pre-Fetching Models](https://docs.crawl4ai.com/core/installation/#optional-pre-fetching-models)
  * [5. Docker (Experimental)](https://docs.crawl4ai.com/core/installation/#5-docker-experimental)
  * [6. Local Server Mode (Legacy)](https://docs.crawl4ai.com/core/installation/#6-local-server-mode-legacy)
  * [Summary](https://docs.crawl4ai.com/core/installation/#summary)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")

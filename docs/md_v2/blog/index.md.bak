# Crawl4AI Blog

Welcome to the Crawl4AI blog! Here you'll find detailed release notes, technical insights, and updates about the project. Whether you're looking for the latest improvements or want to dive deep into web crawling techniques, this is the place.

## Featured Articles

### [When to Stop Crawling: The Art of Knowing "Enough"](articles/adaptive-crawling-revolution.md)
*January 29, 2025*

Traditional crawlers are like tourists with unlimited time—they'll visit every street, every alley, every dead end. But what if your crawler could think like a researcher with a deadline? Discover how Adaptive Crawling revolutionizes web scraping by knowing when to stop. Learn about the three-layer intelligence system that evaluates coverage, consistency, and saturation to build focused knowledge bases instead of endless page collections.

[Read the full article →](articles/adaptive-crawling-revolution.md)

### [The LLM Context Protocol: Why Your AI Assistant Needs Memory, Reasoning, and Examples](articles/llm-context-revolution.md)
*January 24, 2025*

Ever wondered why your AI coding assistant struggles with your library despite comprehensive documentation? This article introduces the three-dimensional context protocol that transforms how AI understands code. Learn why memory, reasoning, and examples together create wisdom—not just information.

[Read the full article →](articles/llm-context-revolution.md)

## Latest Release

Here’s the blog index entry for **v0.6.0**, written to match the exact tone and structure of your previous entries:

---

### [Crawl4AI v0.6.0 – World-Aware Crawling, Pre-Warmed Browsers, and the MCP API](releases/0.6.0.md)
*April 23, 2025*

Crawl4AI v0.6.0 is our most powerful release yet. This update brings major architectural upgrades including world-aware crawling (set geolocation, locale, and timezone), real-time traffic capture, and a memory-efficient crawler pool with pre-warmed pages.  

The Docker server now exposes a full-featured MCP socket + SSE interface, supports streaming, and comes with a new Playground UI. Plus, table extraction is now native, and the new stress-test framework supports crawling 1,000+ URLs.  

Other key changes:  

*   Native support for `result.media["tables"]` to export DataFrames  
* Full network + console logs and MHTML snapshot per crawl  
* Browser pooling and pre-warming for faster cold starts  
* New streaming endpoints via MCP API and Playground  
* Robots.txt support, proxy rotation, and improved session handling  
* Deprecated old markdown names, legacy modules cleaned up  
* Massive repo cleanup: ~36K insertions, ~5K deletions across 121 files

[Read full release notes →](releases/0.6.0.md)

---

Let me know if you want me to auto-update the actual file or just paste this into the markdown.

### [Crawl4AI v0.5.0: Deep Crawling, Scalability, and a New CLI!](releases/0.5.0.md)

My dear friends and crawlers, there you go, this is the release of Crawl4AI v0.5.0! This release brings a wealth of new features, performance improvements, and a more streamlined developer experience.  Here's a breakdown of what's new:

**Major New Features:**

*   **Deep Crawling:** Explore entire websites with configurable strategies (BFS, DFS, Best-First).  Define custom filters and URL scoring for targeted crawls.
*   **Memory-Adaptive Dispatcher:**  Handle large-scale crawls with ease!  Our new dispatcher dynamically adjusts concurrency based on available memory and includes built-in rate limiting.
*   **Multiple Crawler Strategies:** Choose between the full-featured Playwright browser-based crawler or a new, *much* faster HTTP-only crawler for simpler tasks.
*   **Docker Deployment:**  Deploy Crawl4AI as a scalable, self-contained service with built-in API endpoints and optional JWT authentication.
*   **Command-Line Interface (CLI):**  Interact with Crawl4AI directly from your terminal.  Crawl, configure, and extract data with simple commands.
*   **LLM Configuration (`LLMConfig`):** A new, unified way to configure LLM providers (OpenAI, Anthropic, Ollama, etc.) for extraction, filtering, and schema generation.  Simplifies API key management and switching between models.

**Minor Updates & Improvements:**

*   **LXML Scraping Mode:** Faster HTML parsing with `LXMLWebScrapingStrategy`.
*   **Proxy Rotation:** Added `ProxyRotationStrategy` with a `RoundRobinProxyStrategy` implementation.
*   **PDF Processing:** Extract text, images, and metadata from PDF files.
*   **URL Redirection Tracking:**  Automatically follows and records redirects.
*   **Robots.txt Compliance:**  Optionally respect website crawling rules.
*   **LLM-Powered Schema Generation:**  Automatically create extraction schemas using an LLM.
*   **`LLMContentFilter`:** Generate high-quality, focused markdown using an LLM.
*   **Improved Error Handling & Stability:** Numerous bug fixes and performance enhancements.
*   **Enhanced Documentation:**  Updated guides and examples.

**Breaking Changes & Migration:**

This release includes several breaking changes to improve the library's structure and consistency.  Here's what you need to know:

*   **`arun_many()` Behavior:** Now uses the `MemoryAdaptiveDispatcher` by default.  The return type depends on the `stream` parameter in `CrawlerRunConfig`.  Adjust code that relied on unbounded concurrency.
*   **`max_depth` Location:** Moved to `CrawlerRunConfig` and now controls *crawl depth*.
*   **Deep Crawling Imports:**  Import `DeepCrawlStrategy` and related classes from `crawl4ai.deep_crawling`.
*   **`BrowserContext` API:**  Updated; the old `get_context` method is deprecated.
*   **Optional Model Fields:** Many data model fields are now optional.  Handle potential `None` values.
*   **`ScrapingMode` Enum:** Replaced with strategy pattern (`WebScrapingStrategy`, `LXMLWebScrapingStrategy`).
*   **`content_filter` Parameter:** Removed from `CrawlerRunConfig`. Use extraction strategies or markdown generators with filters.
*   **Removed Functionality:** The synchronous `WebCrawler`, the old CLI, and docs management tools have been removed.
*   **Docker:**  Significant changes to deployment.  See the [Docker documentation](../deploy/docker/README.md).
*   **`ssl_certificate.json`:** This file has been removed.
* **Config**: FastFilterChain has been replaced with FilterChain
* **Deep-Crawl**: DeepCrawlStrategy.arun now returns Union[CrawlResultT, List[CrawlResultT], AsyncGenerator[CrawlResultT, None]]
* **Proxy**: Removed synchronous WebCrawler support and related rate limiting configurations
*   **LLM Parameters:** Use the new `LLMConfig` object instead of passing `provider`, `api_token`, `base_url`, and `api_base` directly to `LLMExtractionStrategy` and `LLMContentFilter`.

**In short:** Update imports, adjust `arun_many()` usage, check for optional fields, and review the Docker deployment guide.

## License Change

Crawl4AI v0.5.0 updates the license to Apache 2.0 *with a required attribution clause*.  This means you are free to use, modify, and distribute Crawl4AI (even commercially), but you *must* clearly attribute the project in any public use or distribution.  See the updated `LICENSE` file for the full legal text and specific requirements.

**Get Started:**

*   **Installation:** `pip install "crawl4ai[all]"` (or use the Docker image)
*   **Documentation:** [https://docs.crawl4ai.com](https://docs.crawl4ai.com)
*   **GitHub:** [https://github.com/unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)

I'm very excited to see what you build with Crawl4AI v0.5.0!

---

### [0.4.2 - Configurable Crawlers, Session Management, and Smarter Screenshots](releases/0.4.2.md)
*December 12, 2024*

The 0.4.2 update brings massive improvements to configuration, making crawlers and browsers easier to manage with dedicated objects. You can now import/export local storage for seamless session management. Plus, long-page screenshots are faster and cleaner, and full-page PDF exports are now possible. Check out all the new features to make your crawling experience even smoother.

[Read full release notes →](releases/0.4.2.md)

---

### [0.4.1 - Smarter Crawling with Lazy-Load Handling, Text-Only Mode, and More](releases/0.4.1.md)
*December 8, 2024*

This release brings major improvements to handling lazy-loaded images, a blazing-fast Text-Only Mode, full-page scanning for infinite scrolls, dynamic viewport adjustments, and session reuse for efficient crawling. If you're looking to improve speed, reliability, or handle dynamic content with ease, this update has you covered.

[Read full release notes →](releases/0.4.1.md)

---

### [0.4.0 - Major Content Filtering Update](releases/0.4.0.md)
*December 1, 2024*

Introduced significant improvements to content filtering, multi-threaded environment handling, and user-agent generation. This release features the new PruningContentFilter, enhanced thread safety, and improved test coverage.

[Read full release notes →](releases/0.4.0.md)

## Project History

Curious about how Crawl4AI has evolved? Check out our [complete changelog](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md) for a detailed history of all versions and updates.

## Stay Updated

- Star us on [GitHub](https://github.com/unclecode/crawl4ai)
- Follow [@unclecode](https://twitter.com/unclecode) on Twitter
- Join our community discussions on GitHub


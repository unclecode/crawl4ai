Getting Started with Crawl4AI
=============================

Welcome to **Crawl4AI**, an open-source LLM-friendly Web Crawler & Scraper. In this tutorial, you’ll:

1. Run your **first crawl** using minimal configuration.
2. Generate **Markdown** output (and learn how it’s influenced by content filters).
3. Experiment with a simple **CSS-based extraction** strategy.
4. See a glimpse of **LLM-based extraction** (including open-source and closed-source model options).
5. Crawl a **dynamic** page that loads content via JavaScript.

---

1. Introduction
---------------

Crawl4AI provides:

* An asynchronous crawler, **`AsyncWebCrawler`**.
* Configurable browser and run settings via **`BrowserConfig`** and **`CrawlerRunConfig`**.
* Automatic HTML-to-Markdown conversion via **`DefaultMarkdownGenerator`** (supports optional filters).
* Multiple extraction strategies (LLM-based or “traditional” CSS/XPath-based).

By the end of this guide, you’ll have performed a basic crawl, generated Markdown, tried out two extraction strategies, and crawled a dynamic page that uses “Load More” buttons or JavaScript updates.

---
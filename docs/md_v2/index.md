# Crawl4AI

Welcome to the official documentation for Crawl4AI! 🕷️🤖 Crawl4AI is an open-source Python library designed to simplify web crawling and extract useful information from web pages. This documentation will guide you through the features, usage, and customization of Crawl4AI.

## Introduction

Crawl4AI has one clear task: to make crawling and data extraction from web pages easy and efficient, especially for large language models (LLMs) and AI applications. Whether you are using it as a REST API or a Python library, Crawl4AI offers a robust and flexible solution with full asynchronous support.

## Quick Start

Here's a quick example to show you how easy it is to use Crawl4AI with its asynchronous capabilities:

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    # Create an instance of AsyncWebCrawler
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Run the crawler on a URL
        result = await crawler.arun(url="https://www.nbcnews.com/business")

        # Print the extracted content
        print(result.markdown)

# Run the async main function
asyncio.run(main())
```

## Key Features ✨

- 🆓 Completely free and open-source
- 🚀 Blazing fast performance, outperforming many paid services
- 🤖 LLM-friendly output formats (JSON, cleaned HTML, markdown)
- 📄 Fit markdown generation for extracting main article content.
- 🌐 Multi-browser support (Chromium, Firefox, WebKit)
- 🌍 Supports crawling multiple URLs simultaneously
- 🎨 Extracts and returns all media tags (Images, Audio, and Video)
- 🔗 Extracts all external and internal links
- 📚 Extracts metadata from the page
- 🔄 Custom hooks for authentication, headers, and page modifications
- 🕵️ User-agent customization
- 🖼️ Takes screenshots of pages with enhanced error handling
- 📜 Executes multiple custom JavaScripts before crawling
- 📊 Generates structured output without LLM using JsonCssExtractionStrategy
- 📚 Various chunking strategies: topic-based, regex, sentence, and more
- 🧠 Advanced extraction strategies: cosine clustering, LLM, and more
- 🎯 CSS selector support for precise data extraction
- 📝 Passes instructions/keywords to refine extraction
- 🔒 Proxy support with authentication for enhanced access
- 🔄 Session management for complex multi-page crawling
- 🌐 Asynchronous architecture for improved performance
- 🖼️ Improved image processing with lazy-loading detection
- 🕰️ Enhanced handling of delayed content loading
- 🔑 Custom headers support for LLM interactions
- 🖼️ iframe content extraction for comprehensive analysis
- ⏱️ Flexible timeout and delayed content retrieval options

## Documentation Structure

Our documentation is organized into several sections:

### Basic Usage
- [Installation](basic/installation.md)
- [Quick Start](basic/quickstart.md)
- [Simple Crawling](basic/simple-crawling.md)
- [Browser Configuration](basic/browser-config.md)
- [Content Selection](basic/content-selection.md)
- [Output Formats](basic/output-formats.md)
- [Page Interaction](basic/page-interaction.md)

### Advanced Features
- [Magic Mode](advanced/magic-mode.md)
- [Session Management](advanced/session-management.md)
- [Hooks & Authentication](advanced/hooks.md)
- [Proxy & Security](advanced/proxy-security.md)
- [Content Processing](advanced/content-processing.md)

### Extraction & Processing
- [Extraction Strategies Overview](extraction/overview.md)
- [LLM Integration](extraction/llm.md)
- [CSS-Based Extraction](extraction/css.md)
- [Cosine Strategy](extraction/cosine.md)
- [Chunking Strategies](extraction/chunking.md)

### API Reference
- [AsyncWebCrawler](api/async-webcrawler.md)
- [CrawlResult](api/crawl-result.md)
- [Extraction Strategies](api/strategies.md)
- [arun() Method Parameters](api/arun.md)

### Examples
- Coming soon!

## Getting Started

1. Install Crawl4AI:
```bash
pip install crawl4ai
```

2. Check out our [Quick Start Guide](basic/quickstart.md) to begin crawling web pages.

3. Explore our [examples](https://github.com/unclecode/crawl4ai/tree/main/docs/examples) to see Crawl4AI in action.

## Support

For questions, suggestions, or issues:
- GitHub Issues: [Report a Bug](https://github.com/unclecode/crawl4ai/issues)
- Twitter: [@unclecode](https://twitter.com/unclecode)
- Website: [crawl4ai.com](https://crawl4ai.com)

Happy Crawling! 🕸️🚀
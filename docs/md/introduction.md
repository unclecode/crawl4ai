# Introduction

Welcome to the documentation for Crawl4AI v0.2.5! 🕷️🤖

Crawl4AI is designed to simplify the process of crawling web pages and extracting useful information for large language models (LLMs) and AI applications. Whether you're using it as a REST API, a Python library, or through a Google Colab notebook, Crawl4AI provides powerful features to make web data extraction easier and more efficient.

## Key Features ✨

- **🆓 Completely Free and Open-Source**: Crawl4AI is free to use and open-source, making it accessible for everyone.
- **🤖 LLM-Friendly Output Formats**: Supports JSON, cleaned HTML, and markdown formats.
- **🌍 Concurrent Crawling**: Crawl multiple URLs simultaneously to save time.
- **🎨 Media Extraction**: Extract all media tags including images, audio, and video.
- **🔗 Link Extraction**: Extract all external and internal links from web pages.
- **📚 Metadata Extraction**: Extract metadata from web pages for additional context.
- **🔄 Custom Hooks**: Define custom hooks for authentication, headers, and page modifications before crawling.
- **🕵️ User Agent Support**: Customize the user agent for HTTP requests.
- **🖼️ Screenshot Capability**: Take screenshots of web pages during crawling.
- **📜 JavaScript Execution**: Execute custom JavaScripts before crawling.
- **📚 Advanced Chunking and Extraction Strategies**: Utilize topic-based, regex, sentence chunking, cosine clustering, and LLM extraction strategies.
- **🎯 CSS Selector Support**: Extract specific content using CSS selectors.
- **📝 Instruction/Keyword Refinement**: Pass instructions or keywords to refine the extraction process.

## Recent Changes (v0.2.5) 🌟

- **New Hooks**: Added six important hooks to the crawler:
  - 🟢 `on_driver_created`: Called when the driver is ready for initializations.
  - 🔵 `before_get_url`: Called right before Selenium fetches the URL.
  - 🟣 `after_get_url`: Called after Selenium fetches the URL.
  - 🟠 `before_return_html`: Called when the data is parsed and ready.
  - 🟡 `on_user_agent_updated`: Called when the user changes the user agent, causing the driver to reinitialize.
- **New Example**: Added an example in [`quickstart.py`](https://github.com/unclecode/crawl4ai/blob/main/docs/examples/quickstart.py) in the example folder under the docs.
- **Improved Semantic Context**: Maintaining the semantic context of inline tags (e.g., abbreviation, DEL, INS) for improved LLM-friendliness.
- **Dockerfile Update**: Updated Dockerfile to ensure compatibility across multiple platforms.

Check the [Changelog](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md) for more details.

## Power and Simplicity of Crawl4AI 🚀

Crawl4AI provides an easy way to crawl and extract data from web pages without installing any library. You can use the REST API on our server or run the local server on your machine. For more advanced control, use the Python library to customize your crawling and extraction strategies.

Explore the documentation to learn more about the features, installation process, usage examples, and how to contribute to Crawl4AI. Let's make the web more accessible and useful for AI applications! 💪🌐🤖

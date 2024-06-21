# Crawl4AI v0.2.5 🕷️🤖

[![GitHub Stars](https://img.shields.io/github/stars/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/pulls)
[![License](https://img.shields.io/github/license/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/blob/main/LICENSE)

Crawl4AI simplifies web crawling and data extraction, making it accessible for large language models (LLMs) and AI applications. 🆓🌐

## Try it Now!

- Use as REST API: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1zODYjhemJ5bUmYceWpVoBMVpd0ofzNBZ?usp=sharing)
- Use as Python library: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1wz8u30rvbq6Scodye9AGCw8Qg_Z8QGsk)

✨ visit our [Documentation Website](https://crawl4ai.com/mkdocs/)

## Features ✨

- 🆓 Completely free and open-source
- 🤖 LLM-friendly output formats (JSON, cleaned HTML, markdown)
- 🌍 Supports crawling multiple URLs simultaneously
- 🎨 Extracts and returns all media tags (Images, Audio, and Video)
- 🔗 Extracts all external and internal links
- 📚 Extracts metadata from the page
- 🔄 Custom hooks for authentication, headers, and page modifications before crawling
- 🕵️ User-agent customization
- 🖼️ Takes screenshots of the page
- 📜 Executes multiple custom JavaScripts before crawling
- 📚 Various chunking strategies: topic-based, regex, sentence, and more
- 🧠 Advanced extraction strategies: cosine clustering, LLM, and more
- 🎯 CSS selector support
- 📝 Passes instructions/keywords to refine extraction

## Cool Examples 🚀

### Quick Start

```python
from crawl4ai import WebCrawler

# Create an instance of WebCrawler
crawler = WebCrawler()

# Warm up the crawler (load necessary models)
crawler.warmup()

# Run the crawler on a URL
result = crawler.run(url="https://www.nbcnews.com/business")

# Print the extracted content
print(result.markdown)
```

### Extract Structured Data from Web Pages 📊

Crawl all OpenAI models and their fees from the official page.

```python
import os
from crawl4ai import WebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

url = 'https://openai.com/api/pricing/'
crawler = WebCrawler()
crawler.warmup()

result = crawler.run(
    url=url,
    extraction_strategy=LLMExtractionStrategy(
        provider="openai/gpt-4",
        api_token=os.getenv('OPENAI_API_KEY'),
        instruction="Extract all model names and their fees for input and output tokens."
    ),
)

print(result.extracted_content)
```

### Execute JS, Filter Data with CSS Selector, and Clustering

```python
from crawl4ai import WebCrawler
from crawl4ai.chunking_strategy import CosineStrategy

js_code = ["const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"]

crawler = WebCrawler()
crawler.warmup()

result = crawler.run(
    url="https://www.nbcnews.com/business",
    js=js_code,
    css_selector="p",
    extraction_strategy=CosineStrategy(semantic_filter="technology")
)

print(result.extracted_content)
```

## Documentation 📚

For detailed documentation, including installation instructions, advanced features, and API reference, visit our [Documentation Website](https://crawl4ai.com/mkdocs/).

## Contributing 🤝

We welcome contributions from the open-source community. Check out our [contribution guidelines](https://github.com/unclecode/crawl4ai/blob/main/CONTRIBUTING.md) for more information.

## License 📄

Crawl4AI is released under the [Apache 2.0 License](https://github.com/unclecode/crawl4ai/blob/main/LICENSE).

## Contact 📧

For questions, suggestions, or feedback, feel free to reach out:

- GitHub: [unclecode](https://github.com/unclecode)
- Twitter: [@unclecode](https://twitter.com/unclecode)
- Website: [crawl4ai.com](https://crawl4ai.com)

Happy Crawling! 🕸️🚀

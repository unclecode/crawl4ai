# Crawl4AI v0.2.77 🕷️🤖

[![GitHub Stars](https://img.shields.io/github/stars/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/pulls)
[![License](https://img.shields.io/github/license/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/blob/main/LICENSE)

Crawl4AI simplifies web crawling and data extraction, making it accessible for large language models (LLMs) and AI applications. 🆓🌐

#### [v0.2.77] - 2024-08-02

Major improvements in functionality, performance, and cross-platform compatibility! 🚀

- 🐳 **Docker enhancements**:
  - Significantly improved Dockerfile for easy installation on Linux, Mac, and Windows.
- 🌐 **Official Docker Hub image**:
  - Launched our first official image on Docker Hub for streamlined deployment (unclecode/crawl4ai).
- 🔧 **Selenium upgrade**:
  - Removed dependency on ChromeDriver, now using Selenium's built-in capabilities for better compatibility.
- 🖼️ **Image description**:
  - Implemented ability to generate textual descriptions for extracted images from web pages.
- ⚡ **Performance boost**:
  - Various improvements to enhance overall speed and performance.
  
## Try it Now!

✨ Play around with this [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1sJPAmeLj5PMrg2VgOwMJ2ubGIcK0cJeX?usp=sharing)

✨ visit our [Documentation Website](https://crawl4ai.com/mkdocs/)

✨ Check [Demo](https://crawl4ai.com/mkdocs/demo)

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

# Crawl4AI

## 🌟 Shoutout to Contributors of v0.2.77!

A big thank you to the amazing contributors who've made this release possible:

- [@aravindkarnam](https://github.com/aravindkarnam) for the new image description feature
- [@FractalMind](https://github.com/FractalMind) for our official Docker Hub image
- [@ketonkss4](https://github.com/ketonkss4) for helping streamline our Selenium setup

Your contributions are driving Crawl4AI forward! 🚀

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

## How to install 🛠 

### Using pip 🐍
```bash
virtualenv venv
source venv/bin/activate
pip install "crawl4ai @ git+https://github.com/unclecode/crawl4ai.git"
```

### Using Docker 🐳

```bash
# For Mac users (M1/M2)
# docker build --platform linux/amd64 -t crawl4ai .
docker build -t crawl4ai .
docker run -d -p 8000:80 crawl4ai
```

### Using Docker Hub 🐳

```bash
docker pull unclecode/crawl4ai:latest
docker run -d -p 8000:80 unclecode/crawl4ai:latest
```


## Speed-First Design 🚀

Perhaps the most important design principle for this library is speed. We need to ensure it can handle many links and resources in parallel as quickly as possible. By combining this speed with fast LLMs like Groq, the results will be truly amazing.

```python
import time
from crawl4ai.web_crawler import WebCrawler
crawler = WebCrawler()
crawler.warmup()

start = time.time()
url = r"https://www.nbcnews.com/business"
result = crawler.run( url, word_count_threshold=10, bypass_cache=True)
end = time.time()
print(f"Time taken: {end - start}")
```

Let's take a look the calculated time for the above code snippet:

```bash
[LOG] 🚀 Crawling done, success: True, time taken: 1.3623387813568115 seconds
[LOG] 🚀 Content extracted, success: True, time taken: 0.05715131759643555 seconds
[LOG] 🚀 Extraction, time taken: 0.05750393867492676 seconds.
Time taken: 1.439958095550537
```
Fetching the content from the page took 1.3623 seconds, and extracting the content took 0.0575 seconds. 🚀

### Extract Structured Data from Web Pages 📊

Crawl all OpenAI models and their fees from the official page.

```python
import os
from crawl4ai import WebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field

class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(..., description="Fee for output token ßfor the OpenAI model.")

url = 'https://openai.com/api/pricing/'
crawler = WebCrawler()
crawler.warmup()

result = crawler.run(
        url=url,
        word_count_threshold=1,
        extraction_strategy= LLMExtractionStrategy(
            provider= "openai/gpt-4o", api_token = os.getenv('OPENAI_API_KEY'), 
            schema=OpenAIModelFee.schema(),
            extraction_type="schema",
            instruction="""From the crawled content, extract all mentioned model names along with their fees for input and output tokens. 
            Do not miss any models in the entire content. One extracted model JSON format should look like this: 
            {"model_name": "GPT-4", "input_fee": "US$10.00 / 1M tokens", "output_fee": "US$30.00 / 1M tokens"}."""
        ),            
        bypass_cache=True,
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

### Extract Structured Data from Web Pages With Proxy and BaseUrl

```python
from crawl4ai import WebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

def create_crawler():
    crawler = WebCrawler(verbose=True, proxy="http://127.0.0.1:7890")
    crawler.warmup()
    return crawler

crawler = create_crawler()

crawler.warmup()

result = crawler.run(
    url="https://www.nbcnews.com/business",
    extraction_strategy=LLMExtractionStrategy(
        provider="openai/gpt-4o",
        api_token="sk-",
        base_url="https://api.openai.com/v1"
    )
)

print(result.markdown)
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

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=unclecode/crawl4ai&type=Date)](https://star-history.com/#unclecode/crawl4ai&Date)
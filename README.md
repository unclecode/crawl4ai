# Crawl4AI v0.2.3 🕷️🤖

[![GitHub Stars](https://img.shields.io/github/stars/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/pulls)
[![License](https://img.shields.io/github/license/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/blob/main/LICENSE)

Crawl4AI has one clear task: to simplify crawling and extract useful information from web pages, making it accessible for large language models (LLMs) and AI applications. 🆓🌐

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1wz8u30rvbq6Scodye9AGCw8Qg_Z8QGsk)

## Recent Changes 

### v0.2.3
- 🎨 Extract and return all media tags (Images, Audio, and Video). Check `result.media`
- 🖼️ Take [screenshots](#taking-screenshots) of the page.

### v0.2.2
- Support multiple JS scripts
- Fixed some of bugs
- Resolved a few issue relevant to Colab installation

### v0.2.0
- 🚀 10x faster!!
- 📜 Execute custom JavaScript before crawling!
- 🤝 Colab friendly!
- 📚 Chunking strategies: topic-based, regex, sentence, and more!
- 🧠 Extraction strategies: cosine clustering, LLM, and more!
- 🎯 CSS selector support
- 📝 Pass instructions/keywords to refine extraction

## Power and Simplicity of Crawl4AI 🚀

The most easy way! If you don't want to install any library, you can use the REST API on my server. But remember, this is just a simple server. I may improve its capacity if I see there is demand.

```
import requests

data = {
  "urls": [
    "https://www.nbcnews.com/business"
  ],
  "word_count_threshold": 5,
  "screenshot": True
}

response = requests.post("https://crawl4ai.com/crawl", json=data) # OR local host if your run locally 
response_data = response.json()
print(response_data['results'][0].keys())
```

To show the simplicity take a look at the first example:

```python
from crawl4ai import WebCrawler

# Create the WebCrawler instance 
crawler = WebCrawler() 

# Run the crawler with keyword filtering and CSS selector
result = crawler.run(url="https://www.nbcnews.com/business")
print(result) # {url, html, markdown, extracted_content, metadata}
```

If you don't want to install Selenium, you can use the REST API or local server. 

```python
import requests

data = {
  "urls": [
    "https://www.nbcnews.com/business"
  ],
  "word_count_threshold": 10,
  "extraction_strategy": "NoExtractionStrategy",
}

response = requests.post("https://crawl4ai.com/crawl", json=data) # OR local host if your run locally 
print(response.json())
```

Now let's try a complex task. Below is an example of how you can execute JavaScript, filter data using keywords, and use a CSS selector to extract specific content—all in one go!

1. Instantiate a WebCrawler object.
2. Execute custom JavaScript to click a "Load More" button.
3. Extract semantical chunks of content and filter the data to include only content related to technology.
4. Use a CSS selector to extract only paragraphs (`<p>` tags).

```python
# Import necessary modules
from crawl4ai import WebCrawler
from crawl4ai.chunking_strategy import *
from crawl4ai.extraction_strategy import *
from crawl4ai.crawler_strategy import *

# Define the JavaScript code to click the "Load More" button
js_code = """
const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More'));
loadMoreButton && loadMoreButton.click();
"""

# Define the crawling strategy
crawler_strategy = LocalSeleniumCrawlerStrategy(js_code=js_code)

# Create the WebCrawler instance with the defined strategy
crawler = WebCrawler(crawler_strategy=crawler_strategy)

# Run the crawler with keyword filtering and CSS selector
result = crawler.run(
    url="https://www.nbcnews.com/business",
    extraction_strategy=CosineStrategy(
        semantic_filter="technology",
    ),
)

# Run the crawler with LLM extraction strategy
result = crawler.run(
    url="https://www.nbcnews.com/business",
    extraction_strategy=LLMExtractionStrategy(
        provider="openai/gpt-4o",
        api_token=os.getenv('OPENAI_API_KEY'),
        instruction="Extract only content related to technology"
    ),
    css_selector="p"
)

# Display the extracted result
print(result)
```

With Crawl4AI, you can perform advanced web crawling and data extraction tasks with just a few lines of code. This example demonstrates how you can harness the power of Crawl4AI to simplify your workflow and get the data you need efficiently.

---

*Continue reading to learn more about the features, installation process, usage, and more.*


## Table of Contents

1. [Features](#features-)
2. [Installation](#installation-)
3. [REST API/Local Server](#using-the-local-server-ot-rest-api-)
4. [Python Library Usage](#python-library-usage-)
5. [Parameters](#parameters-)
6. [Chunking Strategies](#chunking-strategies-)
7. [Extraction Strategies](#extraction-strategies-)
8. [Contributing](#contributing-)
9. [License](#license-)
10. [Contact](#contact-)


## Features ✨

- 🕷️ Efficient web crawling to extract valuable data from websites
- 🤖 LLM-friendly output formats (JSON, cleaned HTML, markdown)
- 🌍 Supports crawling multiple URLs simultaneously
- 🌃 Replace media tags with ALT.
- 🆓 Completely free to use and open-source
- 📜 Execute custom JavaScript before crawling
- 📚 Chunking strategies: topic-based, regex, sentence, and more
- 🧠 Extraction strategies: cosine clustering, LLM, and more
- 🎯 CSS selector support
- 📝 Pass instructions/keywords to refine extraction

## Installation 💻

There are three ways to use Crawl4AI:
1. As a library (Recommended)
2. As a local server (Docker) or using the REST API
4. As a Google Colab notebook. [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1wz8u30rvbq6Scodye9AGCw8Qg_Z8QGsk)

To install Crawl4AI as a library, follow these steps:

1. Install the package from GitHub:
```bash
virtualenv venv
source venv/bin/activate
pip install "crawl4ai[all] @ git+https://github.com/unclecode/crawl4ai.git"
```

💡 Better to run the following CLI-command to load the required models. This is optional, but it will boost the performance and speed of the crawler. You need to do this only once.

    crawl4ai-download-models

2. Alternatively, you can clone the repository and install the package locally:
```bash
virtualenv venv
source venv/bin/activate
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai
pip install -e .[all]
```

3. Use docker to run the local server:
```bash
# For Mac users
# docker build --platform linux/amd64 -t crawl4ai .
# For other users
# docker build -t crawl4ai .
docker run -d -p 8000:80 crawl4ai
```



## Using the Local server ot REST API 🌐

You can also use Crawl4AI through the REST API. This method allows you to send HTTP requests to the Crawl4AI server and receive structured data in response. The base URL for the API is `https://crawl4ai.com/crawl` [Available now, on a CPU server, of course will be faster on GPU]. If you run the local server, you can use `http://localhost:8000/crawl`. (Port is dependent on your docker configuration)

### Example Usage

To use the REST API, send a POST request to `http://localhost:8000/crawl` with the following parameters in the request body.

**Example Request:**
```json
{
    "urls": ["https://www.nbcnews.com/business"],
    "include_raw_html": false,
    "bypass_cache": true,
    "word_count_threshold": 5,
    "extraction_strategy": "CosineStrategy",
    "chunking_strategy": "RegexChunking",
    "css_selector": "p",
    "verbose": true,
    "extraction_strategy_args": {
        "semantic_filter": "finance economy and stock market",
        "word_count_threshold": 20,
        "max_dist": 0.2,
        "linkage_method": "ward",
        "top_k": 3
    },
    "chunking_strategy_args": {
        "patterns": ["\n\n"]
    }
}
```

**Example Response:**
```json
{
    "status": "success",
    "data": [
        {
            "url": "https://www.nbcnews.com/business",
            "extracted_content": "...",
            "html": "...",
            "markdown": "...",
            "metadata": {...}
        }
    ]
}
```

For more information about the available parameters and their descriptions, refer to the [Parameters](#parameters-) section.


## Python Library Usage 🚀

🔥 A great way to try out Crawl4AI is to run `quickstart.py` in the `docs/examples` directory. This script demonstrates how to use Crawl4AI to crawl a website and extract content from it.

### Quickstart Guide

Create an instance of WebCrawler and call the `warmup()` function.
```python
crawler = WebCrawler()
crawler.warmup()
```

### Understanding 'bypass_cache' and 'include_raw_html' parameters

First crawl (caches the result):
```python
result = crawler.run(url="https://www.nbcnews.com/business")
```

Second crawl (Force to crawl again):
```python
result = crawler.run(url="https://www.nbcnews.com/business", bypass_cache=True)
```
    💡 Don't forget to set `bypass_cache` to True if you want to try different strategies for the same URL. Otherwise, the cached result will be returned. You can also set `always_by_pass_cache` in constructor to True to always bypass the cache.

Crawl result without raw HTML content:
```python
result = crawler.run(url="https://www.nbcnews.com/business", include_raw_html=False)
```

### Taking Screenshots

```python
result = crawler.run(url="https://www.nbcnews.com/business", screenshot=True)
with open("screenshot.png", "wb") as f:
    f.write(base64.b64decode(result.screenshot))
```

### Adding a chunking strategy: RegexChunking

Using RegexChunking:
```python
result = crawler.run(
    url="https://www.nbcnews.com/business",
    chunking_strategy=RegexChunking(patterns=["\n\n"])
)
```

Using NlpSentenceChunking:
```python
result = crawler.run(
    url="https://www.nbcnews.com/business",
    chunking_strategy=NlpSentenceChunking()
)
```

### Extraction strategy: CosineStrategy

So far, the extracted content is just the result of chunking. To extract meaningful content, you can use extraction strategies. These strategies cluster consecutive chunks into meaningful blocks, keeping the same order as the text in the HTML. This approach is perfect for use in RAG applications and semantical search queries.

Using CosineStrategy:
```python
result = crawler.run(
    url="https://www.nbcnews.com/business",
    extraction_strategy=CosineStrategy(
        semantic_filter="",
        word_count_threshold=10, 
        max_dist=0.2, 
        linkage_method="ward", 
        top_k=3
    )
)
```

You can set `semantic_filter` to filter relevant documents before clustering. Documents are filtered based on their cosine similarity to the keyword filter embedding. 

```python
result = crawler.run(
    url="https://www.nbcnews.com/business",
    extraction_strategy=CosineStrategy(
        semantic_filter="finance economy and stock market",
        word_count_threshold=10, 
        max_dist=0.2, 
        linkage_method="ward", 
        top_k=3
    )
)
```

### Using LLMExtractionStrategy

Without instructions:
```python
result = crawler.run(
    url="https://www.nbcnews.com/business",
    extraction_strategy=LLMExtractionStrategy(
        provider="openai/gpt-4o", 
        api_token=os.getenv('OPENAI_API_KEY')
    )
)
```

With instructions:
```python
result = crawler.run(
    url="https://www.nbcnews.com/business",
    extraction_strategy=LLMExtractionStrategy(
        provider="openai/gpt-4o",
        api_token=os.getenv('OPENAI_API_KEY'),
        instruction="I am interested in only financial news"
    )
)
```

### Targeted extraction using CSS selector

Extract only H2 tags:
```python
result = crawler.run(
    url="https://www.nbcnews.com/business",
    css_selector="h2"
)
```

### Passing JavaScript code to click 'Load More' button

Using JavaScript to click 'Load More' button:
```python
js_code = """
const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More'));
loadMoreButton && loadMoreButton.click();
"""
crawler_strategy = LocalSeleniumCrawlerStrategy(js_code=js_code)
crawler = WebCrawler(crawler_strategy=crawler_strategy, always_by_pass_cache=True)
result = crawler.run(url="https://www.nbcnews.com/business")
```

## Parameters 📖

| Parameter             | Description                                                                                           | Required | Default Value       |
|-----------------------|-------------------------------------------------------------------------------------------------------|----------|---------------------|
| `urls`                | A list of URLs to crawl and extract data from.                                                        | Yes      | -                   |
| `include_raw_html`    | Whether to include the raw HTML content in the response.                                              | No       | `false`             |
| `bypass_cache`        | Whether to force a fresh crawl even if the URL has been previously crawled.                           | No       | `false`             |
| `screenshots`         | Whether to take screenshots of the page.                                                              | No       | `false`             |
| `word_count_threshold`| The minimum number of words a block must contain to be considered meaningful (minimum value is 5).    | No       | `5`                 |
| `extraction_strategy` | The strategy to use for extracting content from the HTML (e.g., "CosineStrategy").                    | No       | `NoExtractionStrategy`    |
| `chunking_strategy`   | The strategy to use for chunking the text before processing (e.g., "RegexChunking").                  | No       | `RegexChunking`     |
| `css_selector`        | The CSS selector to target specific parts of the HTML for extraction.                                 | No       | `None`              |
| `verbose`             | Whether to enable verbose logging.                                                                    | No       | `true`              |

## Chunking Strategies 📚

### RegexChunking

`RegexChunking` is a text chunking strategy that splits a given text into smaller parts using regular expressions. This is useful for preparing large texts for processing by language models, ensuring they are divided into manageable segments.

**Constructor Parameters:**
- `patterns` (list, optional): A list of regular expression patterns used to split the text. Default is to split by double newlines (`['\n\n']`).

**Example usage:**
```python
chunker = RegexChunking(patterns=[r'\n\n', r'\. '])
chunks = chunker.chunk("This is a sample text. It will be split into chunks.")
```

### NlpSentenceChunking

`NlpSentenceChunking` uses a natural language processing model to chunk a given text into sentences. This approach leverages SpaCy to accurately split text based on sentence boundaries.

**Constructor Parameters:**
- None.

**Example usage:**
```python
chunker = NlpSentenceChunking()
chunks = chunker.chunk("This is a sample text. It will be split into sentences.")
```

### TopicSegmentationChunking

`TopicSegmentationChunking` uses the TextTiling algorithm to segment a given text into topic-based chunks. This method identifies thematic boundaries in the text.

**Constructor Parameters:**
- `num_keywords` (int, optional): The number of keywords to extract for each topic segment. Default is `3`.

**Example usage:**
```python
chunker = TopicSegmentationChunking(num_keywords=3)
chunks = chunker.chunk("This is a sample text. It will be split into topic-based segments.")
```

### FixedLengthWordChunking

`FixedLengthWordChunking` splits a given text into chunks of fixed length, based on the number of words.

**Constructor Parameters:**
- `chunk_size` (int, optional): The number of words in each chunk. Default is `100`.

**Example usage:**
```python
chunker = FixedLengthWordChunking(chunk_size=100)
chunks = chunker.chunk("This is a sample text. It will be split into fixed-length word chunks.")
```

### SlidingWindowChunking

`SlidingWindowChunking` uses a sliding window approach to chunk a given text. Each chunk has a fixed length, and the window slides by a specified step size.

**Constructor Parameters:**
- `window_size` (int, optional): The number of words in each chunk. Default is `100`.
- `step` (int, optional): The number of words to slide the window. Default is `50`.

**Example usage:**
```python
chunker = SlidingWindowChunking(window_size=100, step=50)
chunks = chunker.chunk("This is a sample text. It will be split using a sliding window approach.")
```

## Extraction Strategies 🧠

### NoExtractionStrategy

`NoExtractionStrategy` is a basic extraction strategy that returns the entire HTML content without any modification. It is useful for cases where no specific extraction is required.

**Constructor Parameters:**
None.

**Example usage:**
```python
extractor = NoExtractionStrategy()
extracted_content = extractor.extract(url, html)
```

### LLMExtractionStrategy

`LLMExtractionStrategy` uses a Language Model (LLM) to extract meaningful blocks or chunks from the given HTML content. This strategy leverages an external provider for language model completions.

**Constructor Parameters:**
- `provider` (str, optional): The provider to use for the language model completions. Default is `DEFAULT_PROVIDER` (e.g., openai/gpt-4).
- `api_token` (str, optional): The API token for the provider. If not provided, it will try to load from the environment variable `OPENAI_API_KEY`.
- `instruction` (str, optional): An instruction to guide the LLM on how to perform the extraction. This allows users to specify the type of data they are interested in or set the tone of the response. Default is `None`.

**Example usage:**
```python
extractor = LLMExtractionStrategy(provider='openai', api_token='your_api_token', instruction='Extract only news about AI.')
extracted_content = extractor.extract(url, html)
```

### CosineStrategy

`CosineStrategy` uses hierarchical clustering based on cosine similarity to extract clusters of text from the given HTML content. This strategy is suitable for identifying related content sections.

**Constructor Parameters:**
- `semantic_filter` (str, optional): A string containing keywords for filtering relevant documents before clustering. If provided, documents are filtered based on their cosine similarity to the keyword filter embedding. Default is `None`.
- `word_count_threshold` (int, optional): Minimum number of words per cluster. Default is `20`.
- `max_dist` (float, optional): The maximum cophenetic distance on the dendrogram to form clusters. Default is `0.2`.
- `linkage_method` (str, optional): The linkage method for hierarchical clustering. Default is `'ward'`.
- `top_k` (int, optional): Number of top categories to extract. Default is `3`.
- `model_name` (str, optional): The model name for embedding generation. Default is `'BAAI/bge-small-en-v1.5'`.

**Example usage:**
```python
extractor = CosineStrategy(semantic_filter='finance rental prices', word_count_threshold=10, max_dist=0.2, linkage_method='ward', top_k=3, model_name='BAAI/bge-small-en-v1.5')
extracted_content = extractor.extract(url, html)
```

### TopicExtractionStrategy

`TopicExtractionStrategy` uses the TextTiling algorithm to segment the HTML content into topics and extracts keywords for each segment. This strategy is useful for identifying and summarizing thematic content.

**Constructor Parameters:**
- `num_keywords` (int, optional): Number of keywords to represent each topic segment. Default is `3`.

**Example usage:**
```python
extractor = TopicExtractionStrategy(num_keywords=3)
extracted_content = extractor.extract(url, html)
```

## Contributing 🤝

We welcome contributions from the open-source community to help improve Crawl4AI and make it even more valuable for AI enthusiasts and developers. To contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with descriptive messages.
4. Push your changes to your forked repository.
5. Submit a pull request to the main repository.

For more information on contributing, please see our [contribution guidelines](https://github.com/unclecode/crawl4ai/blob/main/CONTRIBUTING.md).

## License 📄

Crawl4AI is released under the [Apache 2.0 License](https://github.com/unclecode/crawl4ai/blob/main/LICENSE).

## Contact 📧

If you have any questions, suggestions, or feedback, please feel free to reach out to us:

- GitHub: [unclecode](https://github.com/unclecode)
- Twitter: [@unclecode](https://twitter.com/unclecode)
- Website: [crawl4ai.com](https://crawl4ai.com)

Let's work together to make the web more accessible and useful for AI applications! 💪🌐🤖

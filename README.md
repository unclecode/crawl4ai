# Crawl4AI 🕷️🤖

[![GitHub Stars](https://img.shields.io/github/stars/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/pulls)
[![License](https://img.shields.io/github/license/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/blob/main/LICENSE)

Crawl4AI is a powerful, free web crawling service designed to extract useful information from web pages and make it accessible for large language models (LLMs) and AI applications. 🆓🌐

## 🚧 Work in Progress 👷‍♂️

- 🔧 Separate Crawl and Extract Semantic Chunk: Enhancing efficiency in large-scale tasks.
- 🔍 Colab Integration: Exploring integration with Google Colab for easy experimentation.
- 🎯 XPath and CSS Selector Support: Adding support for selective retrieval of specific elements.
- 📷 Image Captioning: Incorporating image captioning capabilities to extract descriptions from images.
- 💾 Embedding Vector Data: Generate and store embedding data for each crawled website.
- 🔍 Semantic Search Engine: Building a semantic search engine that fetches content, performs vector search similarity, and generates labeled chunk data based on user queries and URLs.

For more details, refer to the [CHANGELOG.md](https://github.com/unclecode/crawl4ai/edit/main/CHANGELOG.md) file.

## Features ✨

- 🕷️ Efficient web crawling to extract valuable data from websites
- 🤖 LLM-friendly output formats (JSON, cleaned HTML, markdown)
- 🌍 Supports crawling multiple URLs simultaneously
- 🌃 Replace media tags with ALT.
- 🆓 Completely free to use and open-source

## Getting Started 🚀

To get started with Crawl4AI, simply visit our web application at [https://crawl4ai.uccode.io](https://crawl4ai.uccode.io) (Available now!) and enter the URL(s) you want to crawl. The application will process the URLs and provide you with the extracted data in various formats.

## Installation 💻

There are two ways to use Crawl4AI: as a library in your Python projects or as a standalone local server.

### Using Crawl4AI as a Library 📚

To install Crawl4AI as a library, follow these steps:

1. Install the package from GitHub:
```sh
pip install git+https://github.com/unclecode/crawl4ai.git
```

Alternatively, you can clone the repository and install the package locally:
```sh
virtualenv venv
source venv/bin/activate
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai
pip install -e .
```

2. Import the necessary modules in your Python script:
```python
from crawl4ai.web_crawler import WebCrawler
from crawl4ai.chunking_strategy import *
from crawl4ai.extraction_strategy import *
import os

crawler = WebCrawler()
crawler.warmup() # IMPORTANT: Warmup the engine before running the first crawl

# Single page crawl
result = crawler.run(
    url='https://www.nbcnews.com/business',
    word_count_threshold=5, # Minimum word count for a HTML tag to be considered as a worthy block
    chunking_strategy= RegexChunking( patterns = ["\n\n"]), # Default is RegexChunking
    extraction_strategy= CosineStrategy(word_count_threshold=20, max_dist=0.2, linkage_method='ward', top_k=3) # Default is CosineStrategy
    # extraction_strategy= LLMExtractionStrategy(provider= "openai/gpt-4o", api_token = os.getenv('OPENAI_API_KEY')),
    bypass_cache=False,
    extract_blocks =True, # Whether to extract semantical blocks of text from the HTML
    css_selector = "", # Eg: "div.article-body"
    verbose=True,
    include_raw_html=True, # Whether to include the raw HTML content in the response
)

print(result.model_dump())
```

Running for the first time will download the chrome driver for selenium. Also creates a SQLite database file `crawler_data.db` in the current directory. This file will store the crawled data for future reference.

The response model is a `CrawlResponse` object that contains the following attributes:
```python
class CrawlResult(BaseModel):
    url: str
    html: str
    success: bool
    cleaned_html: str = None
    markdown: str = None
    parsed_json: str = None
    error_message: str = None
```

### Running Crawl4AI as a Local Server 🚀

To run Crawl4AI as a standalone local server, follow these steps:

1. Clone the repository:
```sh
git clone https://github.com/unclecode/crawl4ai.git
```

2. Navigate to the project directory:
```sh
cd crawl4ai
```

3. Open `crawler/config.py` and set your favorite LLM provider and API token.

4. Build the Docker image:
```sh
docker build -t crawl4ai .
```
   For Mac users, use the following command instead:
```sh
docker build --platform linux/amd64 -t crawl4ai .
```

5. Run the Docker container:
```sh
docker run -d -p 8000:80 crawl4ai
```

6. Access the application at `http://localhost:8000`.

- CURL Example:
Set the api_token to your OpenAI API key or any other provider you are using.
```sh
curl -X POST -H "Content-Type: application/json" -d '{"urls":["https://techcrunch.com/"],"provider_model":"openai/gpt-3.5-turbo","api_token":"your_api_token","include_raw_html":true,"forced":false,"extract_blocks_flag":false,"word_count_threshold":10}' http://localhost:8000/crawl
```
Set `extract_blocks_flag` to True to enable the LLM to generate semantically clustered chunks and return them as JSON. Depending on the model and data size, this may take up to 1 minute. Without this setting, it will take between 5 to 20 seconds.

- Python Example:
```python
import requests
import os

data = {
  "urls": [
    "https://www.nbcnews.com/business"
  ],
  "provider_model": "groq/llama3-70b-8192",
  "include_raw_html": true,
  "bypass_cache": false,
  "extract_blocks": true,
  "word_count_threshold": 10,
  "extraction_strategy": "CosineStrategy",
  "chunking_strategy": "RegexChunking",
  "css_selector": "",
  "verbose": true
}

response = requests.post("http://crawl4ai.uccode.io/crawl", json=data) # OR http://localhost:8000 if your run locally 

if response.status_code == 200:
    result = response.json()["results"][0]
    print("Parsed JSON:")
    print(result["parsed_json"])
    print("\nCleaned HTML:")
    print(result["cleaned_html"])
    print("\nMarkdown:")
    print(result["markdown"])
else:
    print("Error:", response.status_code, response.text)
```

This code sends a POST request to the Crawl4AI server running on localhost, specifying the target URL (`http://crawl4ai.uccode.io/crawl`) and the desired options. The server processes the request and returns the crawled data in JSON format.

The response from the server includes the semantical clusters, cleaned HTML, and markdown representations of the crawled webpage. You can access and use this data in your Python application as needed.

Make sure to replace `"http://localhost:8000/crawl"` with the appropriate server URL if your Crawl4AI server is running on a different host or port.

Choose the approach that best suits your needs. If you want to integrate Crawl4AI into your existing Python projects, installing it as a library is the way to go. If you prefer to run Crawl4AI as a standalone service and interact with it via API endpoints, running it as a local server using Docker is the recommended approach.

**Make sure to check the config.py tp set required environment variables.**

That's it! You can now integrate Crawl4AI into your Python projects and leverage its web crawling capabilities. 🎉

## 📖 Parameters

| Parameter             | Description                                                                                           | Required | Default Value       |
|-----------------------|-------------------------------------------------------------------------------------------------------|----------|---------------------|
| `urls`                | A list of URLs to crawl and extract data from.                                                        | Yes      | -                   |
| `include_raw_html`    | Whether to include the raw HTML content in the response.                                              | No       | `false`             |
| `bypass_cache`        | Whether to force a fresh crawl even if the URL has been previously crawled.                           | No       | `false`             |
| `extract_blocks`      | Whether to extract semantical blocks of text from the HTML.                                           | No       | `true`              |
| `word_count_threshold`| The minimum number of words a block must contain to be considered meaningful (minimum value is 5).    | No       | `5`                 |
| `extraction_strategy` | The strategy to use for extracting content from the HTML (e.g., "CosineStrategy").                    | No       | `CosineStrategy`    |
| `chunking_strategy`   | The strategy to use for chunking the text before processing (e.g., "RegexChunking").                  | No       | `RegexChunking`     |
| `css_selector`        | The CSS selector to target specific parts of the HTML for extraction.                                 | No       | `None`              |
| `verbose`             | Whether to enable verbose logging.                                                                    | No       | `true`              |

## 🛠️ Configuration 
Crawl4AI allows you to configure various parameters and settings in the `crawler/config.py` file. Here's an example of how you can adjust the parameters:

```python
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Default provider, ONLY used when the extraction strategy is LLMExtractionStrategy
DEFAULT_PROVIDER = "openai/gpt-4-turbo"

# Provider-model dictionary, ONLY used when the extraction strategy is LLMExtractionStrategy
PROVIDER_MODELS = {
    "ollama/llama3": "no-token-needed", # Any model from Ollama no need for API token
    "groq/llama3-70b-8192": os.getenv("GROQ_API_KEY"),
    "groq/llama3-8b-8192": os.getenv("GROQ_API_KEY"),
    "openai/gpt-3.5-turbo": os.getenv("OPENAI_API_KEY"),
    "openai/gpt-4-turbo": os.getenv("OPENAI_API_KEY"),
    "openai/gpt-4o": os.getenv("OPENAI_API_KEY"),
    "anthropic/claude-3-haiku-20240307": os.getenv("ANTHROPIC_API_KEY"),
    "anthropic/claude-3-opus-20240229": os.getenv("ANTHROPIC_API_KEY"),
    "anthropic/claude-3-sonnet-20240229": os.getenv("ANTHROPIC_API_KEY"),
}

# Chunk token threshold
CHUNK_TOKEN_THRESHOLD = 1000
# Threshold for the minimum number of words in an HTML tag to be considered 
MIN_WORD_THRESHOLD = 5
```

In the `crawler/config.py` file, you can:

REMEBER: You only need to set the API keys for the providers in case you choose LLMExtractStrategy as the extraction strategy. If you choose CosineStrategy, you don't need to set the API keys.

- Set the default provider using the `DEFAULT_PROVIDER` variable.
- Add or modify the provider-model dictionary (`PROVIDER_MODELS`) to include your desired providers and their corresponding API keys. Crawl4AI supports various providers such as Groq, OpenAI, Anthropic, and more. You can add any provider supported by LiteLLM, as well as Ollama.
- Adjust the `CHUNK_TOKEN_THRESHOLD` value to control the splitting of web content into chunks for parallel processing. A higher value means fewer chunks and faster processing, but it may cause issues with weaker LLMs during extraction.
- Modify the `MIN_WORD_THRESHOLD` value to set the minimum number of words an HTML tag must contain to be considered a meaningful block.

Make sure to set the appropriate API keys for each provider in the `PROVIDER_MODELS` dictionary. You can either directly provide the API key or use environment variables to store them securely.

Remember to update the `crawler/config.py` file based on your specific requirements and the providers you want to use with Crawl4AI.

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

Let's work together to make the web more accessible and useful for AI applications! 💪🌐🤖

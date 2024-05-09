# Crawl4AI 🕷️🤖

[![GitHub Stars](https://img.shields.io/github/stars/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/stargazers)
[![GitHub Forks](https://img.shields.io/github/forks/unclecode/crawl4ai?style=social)](https://github.com/unclecode/crawl4ai/network/members)
[![GitHub Issues](https://img.shields.io/github/issues/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/pulls)
[![License](https://img.shields.io/github/license/unclecode/crawl4ai)](https://github.com/unclecode/crawl4ai/blob/main/LICENSE)

Crawl4AI is a powerful, free web crawling service designed to extract useful information from web pages and make it accessible for large language models (LLMs) and AI applications. 🆓🌐

## Features ✨

- 🕷️ Efficient web crawling to extract valuable data from websites
- 🤖 LLM-friendly output formats (JSON, cleaned HTML, markdown)
- 🌍 Supports crawling multiple URLs simultaneously
- 🌃 Replace media tags with ALT.
- 🆓 Completely free to use and open-source

## Getting Started 🚀

To get started with Crawl4AI, simply visit our web application at [https://crawl4ai.your-domain.io](https://crawl4ai.uccode.io) and enter the URL(s) you want to crawl. The application will process the URLs and provide you with the extracted data in various formats.

## Installation 💻

There are two ways to use Crawl4AI: as a library in your Python projects or as a standalone local server.

### Using Crawl4AI as a Library 📚

To install Crawl4AI as a library, follow these steps:

1. Install the package from GitHub:
```
pip install git+https://github.com/unclecode/crawl4ai.git
```

2. Import the necessary modules in your Python script:
```python
from crawler.web_crawler import WebCrawler
from crawler.models import UrlModel
```

3. Use the Crawl4AI library in your project as needed. Refer to the [Usage with Python](#usage-with-python-) section for more details.

### Running Crawl4AI as a Local Server 🚀

To run Crawl4AI as a standalone local server, follow these steps:

1. Clone the repository:
```
git clone https://github.com/unclecode/crawl4ai.git
```

2. Navigate to the project directory:
```
cd crawl4ai
```

3. Create a `.env` file in the root folder and set your Groq API token:
```
GROQ_API_TOKEN=your_groq_api_token
```

4. Build the Docker image:
```
docker build -t crawl4ai .
```
   For Mac users, use the following command instead:
```
docker build --platform linux/amd64 -t crawl4ai .
```

5. Run the Docker container:
```
docker run -p 8000:80 crawl4ai
```

6. Access the application at `http://localhost:8000`.

For more detailed instructions and advanced configuration options, please refer to the [installation guide](https://github.com/unclecode/crawl4ai/blob/main/INSTALL.md).

Choose the approach that best suits your needs. If you want to integrate Crawl4AI into your existing Python projects, installing it as a library is the way to go. If you prefer to run Crawl4AI as a standalone service and interact with it via API endpoints, running it as a local server using Docker is the recommended approach.

## Usage with Python 🐍

Here's an example of how to use Crawl4AI with Python to crawl a webpage and retrieve the extracted data:

1. Make sure you have the `requests` library installed. You can install it using pip:
```
pip install requests
```

2. Use the following Python code to send a request to the Crawl4AI server and retrieve the crawled data:
```python
import requests
import os

url = "http://localhost:8000/crawl"  # Replace with the appropriate server URL
data = {
  "urls": [
    "https://example.com"
  ],
  "provider_model": "groq/llama3-70b-8192",
  "api_token": "your_api_token",
  "include_raw_html": true,
  "forced": false,
  "extract_blocks": true,
  "word_count_threshold": 5
}

response = requests.post(url, json=data)

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

This code sends a POST request to the Crawl4AI server running on localhost, specifying the target URL (`https://example.com`) and the desired options (`grq_api_token`, `include_raw_html`, and `forced`). The server processes the request and returns the crawled data in JSON format.

The response from the server includes the parsed JSON, cleaned HTML, and markdown representations of the crawled webpage. You can access and use this data in your Python application as needed.

Make sure to replace `"http://localhost:8000/crawl"` with the appropriate server URL if your Crawl4AI server is running on a different host or port.

## Using Crawl4AI as a Python Library 📚

You can also use Crawl4AI as a Python library in your own projects. Here's an example of how to use the Crawl4AI library:

1. Install the required dependencies:
```
pip install -r requirements.txt
```

2. Import the necessary modules and initialize the `WebCrawler`:
```python
from crawler.web_crawler import WebCrawler
from crawler.models import UrlModel
import os

crawler = WebCrawler(db_path='crawler_data.db')
```

3. Fetch a single page:
```python
single_url = UrlModel(url='https://kidocode.com', forced=True)
result = crawler.fetch_page(
    single_url, 
    provider= "openai/gpt-3.5-turbo", 
    api_token = os.getenv('OPENAI_API_KEY'), 
    extract_blocks_flag=True,
    word_count_threshold=5 # Minimum word count for a HTML tag to be considered as a worthy block
)
print(result.model_dump())
```

4. Fetch multiple pages:
```python
urls = [
    UrlModel(url='http://example.com', forced=False),
    UrlModel(url='http://example.org', forced=False)
]
results = crawler.fetch_pages(
    urls, 
    provider= "openai/gpt-3.5-turbo", 
    api_token = os.getenv('OPENAI_API_KEY'), 
    extract_blocks_flag=True, 
    word_count_threshold=5
)

for res in results:
    print(res.json())
```

This code demonstrates how to use the Crawl4AI library to fetch a single page or multiple pages. The `WebCrawler` is initialized with the path to the database, and the `fetch_page` and `fetch_pages` methods are used to crawl the specified URLs.

Make sure to set the `GROQ_API_TOKEN` environment variable with your Groq API token when using the library.

That's it! You can now integrate Crawl4AI into your Python projects and leverage its web crawling capabilities. 🎉

## 📖 Parameters

| Parameter            | Description                                                                                     | Required | Default Value |
|----------------------|-------------------------------------------------------------------------------------------------|----------|---------------|
| `urls`               | A list of URLs to crawl and extract data from.                                                  | Yes      | -             |
| `provider_model`     | The provider and model to use for extracting relevant information (e.g., "groq/llama3-70b-8192"). | Yes      | -             |
| `api_token`          | Your API token for the specified provider.                                                        | Yes      | -             |
| `include_raw_html`   | Whether to include the raw HTML content in the response.                                        | No       | `false`       |
| `forced`             | Whether to force a fresh crawl even if the URL has been previously crawled.                     | No       | `false`       |
| `extract_blocks`     | Whether to extract meaningful blocks of text from the HTML.                                     | No       | `false`       |
| `word_count_threshold` | The minimum number of words a block must contain to be considered meaningful (minimum value is 5). | No       | `5`           |


## Contributing 🤝

We welcome contributions from the open-source community to help improve Crawl4AI and make it even more valuable for AI enthusiasts and developers. To contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them with descriptive messages.
4. Push your changes to your forked repository.
5. Submit a pull request to the main repository.

For more information on contributing, please see our [contribution guidelines](https://github.com/unclecode/crawl4ai/blob/main/CONTRIBUTING.md).

## License 📄

Crawl4AI is released under the [MIT License](https://github.com/unclecode/crawl4ai/blob/main/LICENSE).

## Contact 📧

If you have any questions, suggestions, or feedback, please feel free to reach out to us:

- GitHub: [unclecode](https://github.com/unclecode)
- Twitter: [@unclecode](https://twitter.com/unclecode)
- Discord: [your-invite-link](https://discord.gg/your-invite-link)

Let's work together to make the web more accessible and useful for AI applications! 💪🌐🤖
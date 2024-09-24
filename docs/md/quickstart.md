# Quick Start Guide 🚀

Welcome to the Crawl4AI Quickstart Guide! In this tutorial, we'll walk you through the basic usage of Crawl4AI with a friendly and humorous tone. We'll cover everything from basic usage to advanced features like chunking and extraction strategies, all with the power of asynchronous programming. Let's dive in! 🌟

## Getting Started 🛠️

First, let's import the necessary modules and create an instance of `AsyncWebCrawler`. We'll use an async context manager, which handles the setup and teardown of the crawler for us.

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        # We'll add our crawling code here
        pass

if __name__ == "__main__":
    asyncio.run(main())
```

### Basic Usage

Simply provide a URL and let Crawl4AI do the magic!

```python
async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://www.nbcnews.com/business")
        print(f"Basic crawl result: {result.markdown[:500]}")  # Print first 500 characters

asyncio.run(main())
```

### Taking Screenshots 📸

Let's take a screenshot of the page!

```python
import base64

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url="https://www.nbcnews.com/business", screenshot=True)
        with open("screenshot.png", "wb") as f:
            f.write(base64.b64decode(result.screenshot))
        print("Screenshot saved to 'screenshot.png'!")

asyncio.run(main())
```

### Understanding Parameters 🧠

By default, Crawl4AI caches the results of your crawls. This means that subsequent crawls of the same URL will be much faster! Let's see this in action.

```python
async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        # First crawl (caches the result)
        result1 = await crawler.arun(url="https://www.nbcnews.com/business")
        print(f"First crawl result: {result1.markdown[:100]}...")

        # Force to crawl again
        result2 = await crawler.arun(url="https://www.nbcnews.com/business", bypass_cache=True)
        print(f"Second crawl result: {result2.markdown[:100]}...")

asyncio.run(main())
```

### Adding a Chunking Strategy 🧩

Let's add a chunking strategy: `RegexChunking`! This strategy splits the text based on a given regex pattern.

```python
from crawl4ai.chunking_strategy import RegexChunking

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            chunking_strategy=RegexChunking(patterns=["\n\n"])
        )
        print(f"RegexChunking result: {result.extracted_content[:200]}...")

asyncio.run(main())
```

### Adding an Extraction Strategy 🧠

Let's get smarter with an extraction strategy: `JsonCssExtractionStrategy`! This strategy extracts structured data from HTML using CSS selectors.

```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
import json

async def main():
    schema = {
        "name": "News Articles",
        "baseSelector": "article.tease-card",
        "fields": [
            {
                "name": "title",
                "selector": "h2",
                "type": "text",
            },
            {
                "name": "summary",
                "selector": "div.tease-card__info",
                "type": "text",
            }
        ],
    }

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            extraction_strategy=JsonCssExtractionStrategy(schema, verbose=True)
        )
        extracted_data = json.loads(result.extracted_content)
        print(f"Extracted {len(extracted_data)} articles")
        print(json.dumps(extracted_data[0], indent=2))

asyncio.run(main())
```

### Using LLMExtractionStrategy 🤖

Time to bring in the big guns: `LLMExtractionStrategy`! This strategy uses a large language model to extract relevant information from the web page.

```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy
import os
from pydantic import BaseModel, Field

class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(..., description="Fee for output token for the OpenAI model.")

async def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("OpenAI API key not found. Skipping this example.")
        return

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://openai.com/api/pricing/",
            word_count_threshold=1,
            extraction_strategy=LLMExtractionStrategy(
                provider="openai/gpt-4o",
                api_token=os.getenv("OPENAI_API_KEY"),
                schema=OpenAIModelFee.schema(),
                extraction_type="schema",
                instruction="""From the crawled content, extract all mentioned model names along with their fees for input and output tokens. 
                Do not miss any models in the entire content. One extracted model JSON format should look like this: 
                {"model_name": "GPT-4", "input_fee": "US$10.00 / 1M tokens", "output_fee": "US$30.00 / 1M tokens"}.""",
            ),
            bypass_cache=True,
        )
        print(result.extracted_content)

asyncio.run(main())
```

### Interactive Extraction 🖱️

Let's use JavaScript to interact with the page before extraction!

```python
async def main():
    js_code = """
    const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More'));
    loadMoreButton && loadMoreButton.click();
    """

    wait_for = """() => {
        return Array.from(document.querySelectorAll('article.tease-card')).length > 10;
    }"""

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            js_code=js_code,
            wait_for=wait_for,
            css_selector="article.tease-card",
            bypass_cache=True,
        )
        print(f"JavaScript interaction result: {result.extracted_content[:500]}")

asyncio.run(main())
```

### Advanced Session-Based Crawling with Dynamic Content 🔄

In modern web applications, content is often loaded dynamically without changing the URL. This is common in single-page applications (SPAs) or websites using infinite scrolling. Traditional crawling methods that rely on URL changes won't work here. That's where Crawl4AI's advanced session-based crawling comes in handy!

Here's what makes this approach powerful:

1. **Session Preservation**: By using a `session_id`, we can maintain the state of our crawling session across multiple interactions with the page. This is crucial for navigating through dynamically loaded content.

2. **Asynchronous JavaScript Execution**: We can execute custom JavaScript to trigger content loading or navigation. In this example, we'll click a "Load More" button to fetch the next page of commits.

3. **Dynamic Content Waiting**: The `wait_for` parameter allows us to specify a condition that must be met before considering the page load complete. This ensures we don't extract data before the new content is fully loaded.

Let's see how this works with a real-world example: crawling multiple pages of commits on a GitHub repository. The URL doesn't change as we load more commits, so we'll use these advanced techniques to navigate and extract data.

```python
import json
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://github.com/microsoft/TypeScript/commits/main"
        session_id = "typescript_commits_session"
        all_commits = []

        js_next_page = """
        const button = document.querySelector('a[data-testid="pagination-next-button"]');
        if (button) button.click();
        """

        wait_for = """() => {
            const commits = document.querySelectorAll('li.Box-sc-g0xbh4-0 h4');
            if (commits.length === 0) return false;
            const firstCommit = commits[0].textContent.trim();
            return firstCommit !== window.lastCommit;
        }"""

        schema = {
            "name": "Commit Extractor",
            "baseSelector": "li.Box-sc-g0xbh4-0",
            "fields": [
                {
                    "name": "title",
                    "selector": "h4.markdown-title",
                    "type": "text",
                    "transform": "strip",
                },
            ],
        }
        extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

        for page in range(3):  # Crawl 3 pages
            result = await crawler.arun(
                url=url,
                session_id=session_id,
                css_selector="li.Box-sc-g0xbh4-0",
                extraction_strategy=extraction_strategy,
                js_code=js_next_page if page > 0 else None,
                wait_for=wait_for if page > 0 else None,
                js_only=page > 0,
                bypass_cache=True,
                headless=False,
            )

            assert result.success, f"Failed to crawl page {page + 1}"

            commits = json.loads(result.extracted_content)
            all_commits.extend(commits)

            print(f"Page {page + 1}: Found {len(commits)} commits")

        await crawler.crawler_strategy.kill_session(session_id)
        print(f"Successfully crawled {len(all_commits)} commits across 3 pages")

asyncio.run(main())
```

In this example, we're crawling multiple pages of commits from a GitHub repository. The URL doesn't change as we load more commits, so we use JavaScript to click the "Load More" button and a `wait_for` condition to ensure the new content is loaded before extraction. This powerful combination allows us to navigate and extract data from complex, dynamically-loaded web applications with ease!

## Congratulations! 🎉

You've made it through the Crawl4AI Quickstart Guide! Now go forth and crawl the web asynchronously like a pro! 🕸️

Remember, these are just a few examples of what Crawl4AI can do. For more advanced usage, check out our other documentation pages:

- [LLM Extraction](examples/llm_extraction.md)
- [JS Execution & CSS Filtering](examples/js_execution_css_filtering.md)
- [Hooks & Auth](examples/hooks_auth.md)
- [Summarization](examples/summarization.md)
- [Research Assistant](examples/research_assistant.md)

Happy crawling! 🚀
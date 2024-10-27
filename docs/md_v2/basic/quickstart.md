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

Capture screenshots of web pages easily:

```python
async def capture_and_save_screenshot(url: str, output_path: str):
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=url,
            screenshot=True,
            bypass_cache=True
        )
        
        if result.success and result.screenshot:
            import base64
            screenshot_data = base64.b64decode(result.screenshot)
            with open(output_path, 'wb') as f:
                f.write(screenshot_data)
            print(f"Screenshot saved successfully to {output_path}")
        else:
            print("Failed to capture screenshot")
```

### Browser Selection 🌐

Crawl4AI supports multiple browser engines. Here's how to use different browsers:

```python
# Use Firefox
async with AsyncWebCrawler(browser_type="firefox", verbose=True, headless=True) as crawler:
    result = await crawler.arun(url="https://www.example.com", bypass_cache=True)

# Use WebKit
async with AsyncWebCrawler(browser_type="webkit", verbose=True, headless=True) as crawler:
    result = await crawler.arun(url="https://www.example.com", bypass_cache=True)

# Use Chromium (default)
async with AsyncWebCrawler(verbose=True, headless=True) as crawler:
    result = await crawler.arun(url="https://www.example.com", bypass_cache=True)
```

### User Simulation 🎭

Simulate real user behavior to avoid detection:

```python
async with AsyncWebCrawler(verbose=True, headless=True) as crawler:
    result = await crawler.arun(
        url="YOUR-URL-HERE",
        bypass_cache=True,
        simulate_user=True,  # Causes random mouse movements and clicks
        override_navigator=True  # Makes the browser appear more like a real user
    )
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

### Using LLMExtractionStrategy with Different Providers 🤖

Crawl4AI supports multiple LLM providers for extraction:

```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field

class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(..., description="Fee for output token for the OpenAI model.")

# OpenAI
await extract_structured_data_using_llm("openai/gpt-4o", os.getenv("OPENAI_API_KEY"))

# Hugging Face
await extract_structured_data_using_llm(
    "huggingface/meta-llama/Meta-Llama-3.1-8B-Instruct", 
    os.getenv("HUGGINGFACE_API_KEY")
)

# Ollama
await extract_structured_data_using_llm("ollama/llama3.2")

# With custom headers
custom_headers = {
    "Authorization": "Bearer your-custom-token",
    "X-Custom-Header": "Some-Value"
}
await extract_structured_data_using_llm(extra_headers=custom_headers)
```

### Knowledge Graph Generation 🕸️

Generate knowledge graphs from web content:

```python
from pydantic import BaseModel
from typing import List

class Entity(BaseModel):
    name: str
    description: str
    
class Relationship(BaseModel):
    entity1: Entity
    entity2: Entity
    description: str
    relation_type: str

class KnowledgeGraph(BaseModel):
    entities: List[Entity]
    relationships: List[Relationship]

extraction_strategy = LLMExtractionStrategy(
    provider='openai/gpt-4o-mini',
    api_token=os.getenv('OPENAI_API_KEY'),
    schema=KnowledgeGraph.model_json_schema(),
    extraction_type="schema",
    instruction="Extract entities and relationships from the given text."
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(
        url="https://paulgraham.com/love.html",
        bypass_cache=True,
        extraction_strategy=extraction_strategy
    )
```

### Advanced Session-Based Crawling with Dynamic Content 🔄

For modern web applications with dynamic content loading, here's how to handle pagination and content updates:

```python
async def crawl_dynamic_content():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://github.com/microsoft/TypeScript/commits/main"
        session_id = "typescript_commits_session"
        
        js_next_page = """
        const button = document.querySelector('a[data-testid="pagination-next-button"]');
        if (button) button.click();
        """

        wait_for = """() => {
            const commits = document.querySelectorAll('li.Box-sc-g0xbh4-0 h4');
            if (commits.length === 0) return false;
            const firstCommit = commits[0].textContent.trim();
            return firstCommit !== window.firstCommit;
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

        await crawler.crawler_strategy.kill_session(session_id)
```

### Handling Overlays and Fitting Content 📏

Remove overlay elements and fit content appropriately:

```python
async with AsyncWebCrawler(headless=False) as crawler:
    result = await crawler.arun(
        url="your-url-here",
        bypass_cache=True,
        word_count_threshold=10,
        remove_overlay_elements=True,
        screenshot=True
    )
```

## Performance Comparison 🏎️

Crawl4AI offers impressive performance compared to other solutions:

```python
# Firecrawl comparison
from firecrawl import FirecrawlApp
app = FirecrawlApp(api_key=os.environ['FIRECRAWL_API_KEY'])
start = time.time()
scrape_status = app.scrape_url(
    'https://www.nbcnews.com/business',
    params={'formats': ['markdown', 'html']}
)
end = time.time()

# Crawl4AI comparison
async with AsyncWebCrawler() as crawler:
    start = time.time()
    result = await crawler.arun(
        url="https://www.nbcnews.com/business",
        word_count_threshold=0,
        bypass_cache=True,
        verbose=False,
    )
    end = time.time()
```

Note: Performance comparisons should be conducted in environments with stable and fast internet connections for accurate results.

## Congratulations! 🎉

You've made it through the updated Crawl4AI Quickstart Guide! Now you're equipped with even more powerful features to crawl the web asynchronously like a pro! 🕸️

Happy crawling! 🚀
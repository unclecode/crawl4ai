# LLM Extraction with AsyncWebCrawler

Crawl4AI's AsyncWebCrawler allows you to use Language Models (LLMs) to extract structured data or relevant content from web pages asynchronously. Below are two examples demonstrating how to use `LLMExtractionStrategy` for different purposes with the AsyncWebCrawler.

## Example 1: Extract Structured Data

In this example, we use the `LLMExtractionStrategy` to extract structured data (model names and their fees) from the OpenAI pricing page.

```python
import os
import json
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from pydantic import BaseModel, Field

class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(..., description="Fee for output token for the OpenAI model.")

async def extract_openai_fees():
    url = 'https://openai.com/api/pricing/'

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=url,
            word_count_threshold=1,
            extraction_strategy=LLMExtractionStrategy(
                provider="openai/gpt-4o",
                api_token=os.getenv('OPENAI_API_KEY'),
                schema=OpenAIModelFee.model_json_schema(),
                extraction_type="schema",
                instruction="From the crawled content, extract all mentioned model names along with their "
                            "fees for input and output tokens. Make sure not to miss anything in the entire content. "
                            'One extracted model JSON format should look like this: '
                            '{ "model_name": "GPT-4", "input_fee": "US$10.00 / 1M tokens", "output_fee": "US$30.00 / 1M tokens" }'
            ),
            bypass_cache=True,
        )

    model_fees = json.loads(result.extracted_content)
    print(f"Number of models extracted: {len(model_fees)}")

    with open(".data/openai_fees.json", "w", encoding="utf-8") as f:
        json.dump(model_fees, f, indent=2)

asyncio.run(extract_openai_fees())
```

## Example 2: Extract Relevant Content

In this example, we instruct the LLM to extract only content related to technology from the NBC News business page.

```python
import os
import json
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

async def extract_tech_content():
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            extraction_strategy=LLMExtractionStrategy(
                provider="openai/gpt-4o",
                api_token=os.getenv('OPENAI_API_KEY'),
                instruction="Extract only content related to technology"
            ),
            bypass_cache=True,
        )

    tech_content = json.loads(result.extracted_content)
    print(f"Number of tech-related items extracted: {len(tech_content)}")

    with open(".data/tech_content.json", "w", encoding="utf-8") as f:
        json.dump(tech_content, f, indent=2)

asyncio.run(extract_tech_content())
```

## Advanced Usage: Combining JS Execution with LLM Extraction

This example demonstrates how to combine JavaScript execution with LLM extraction to handle dynamic content:

```python
async def extract_dynamic_content():
    js_code = """
    const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More'));
    if (loadMoreButton) {
        loadMoreButton.click();
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    """

    wait_for = """
    () => {
        const articles = document.querySelectorAll('article.tease-card');
        return articles.length > 10;
    }
    """

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            js_code=js_code,
            wait_for=wait_for,
            css_selector="article.tease-card",
            extraction_strategy=LLMExtractionStrategy(
                provider="openai/gpt-4o",
                api_token=os.getenv('OPENAI_API_KEY'),
                instruction="Summarize each article, focusing on technology-related content"
            ),
            bypass_cache=True,
        )

    summaries = json.loads(result.extracted_content)
    print(f"Number of summarized articles: {len(summaries)}")

    with open(".data/tech_summaries.json", "w", encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)

asyncio.run(extract_dynamic_content())
```

## Customizing LLM Provider

Crawl4AI uses the `litellm` library under the hood, which allows you to use any LLM provider you want. Just pass the correct model name and API token:

```python
extraction_strategy=LLMExtractionStrategy(
    provider="your_llm_provider/model_name",
    api_token="your_api_token",
    instruction="Your extraction instruction"
)
```

This flexibility allows you to integrate with various LLM providers and tailor the extraction process to your specific needs.

## Error Handling and Retries

When working with external LLM APIs, it's important to handle potential errors and implement retry logic. Here's an example of how you might do this:

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

class LLMExtractionError(Exception):
    pass

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def extract_with_retry(crawler, url, extraction_strategy):
    try:
        result = await crawler.arun(url=url, extraction_strategy=extraction_strategy, bypass_cache=True)
        return json.loads(result.extracted_content)
    except Exception as e:
        raise LLMExtractionError(f"Failed to extract content: {str(e)}")

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        try:
            content = await extract_with_retry(
                crawler,
                "https://www.example.com",
                LLMExtractionStrategy(
                    provider="openai/gpt-4o",
                    api_token=os.getenv('OPENAI_API_KEY'),
                    instruction="Extract and summarize main points"
                )
            )
            print("Extracted content:", content)
        except LLMExtractionError as e:
            print(f"Extraction failed after retries: {e}")

asyncio.run(main())
```

This example uses the `tenacity` library to implement a retry mechanism with exponential backoff, which can help handle temporary failures or rate limiting from the LLM API.
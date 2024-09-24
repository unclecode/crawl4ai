# LLM Extraction

Crawl4AI allows you to use Language Models (LLMs) to extract structured data or relevant content from web pages. Below are two examples demonstrating how to use LLMExtractionStrategy for different purposes.

## Example 1: Extract Structured Data

In this example, we use the `LLMExtractionStrategy` to extract structured data (model names and their fees) from the OpenAI pricing page.

```python
import os
import time
from crawl4ai.web_crawler import WebCrawler
from crawl4ai.chunking_strategy import *
from crawl4ai.extraction_strategy import *
from crawl4ai.crawler_strategy import *

url = r'https://openai.com/api/pricing/'

crawler = WebCrawler()
crawler.warmup()

from pydantic import BaseModel, Field

class OpenAIModelFee(BaseModel):
    model_name: str = Field(..., description="Name of the OpenAI model.")
    input_fee: str = Field(..., description="Fee for input token for the OpenAI model.")
    output_fee: str = Field(..., description="Fee for output token for the OpenAI model.")

result = crawler.run(
    url=url,
    word_count_threshold=1,
    extraction_strategy= LLMExtractionStrategy(
        provider= "openai/gpt-4o", api_token = os.getenv('OPENAI_API_KEY'), 
        schema=OpenAIModelFee.model_json_schema(),
        extraction_type="schema",
        instruction="From the crawled content, extract all mentioned model names along with their "\
            "fees for input and output tokens. Make sure not to miss anything in the entire content. "\
            'One extracted model JSON format should look like this: '\
            '{ "model_name": "GPT-4", "input_fee": "US$10.00 / 1M tokens", "output_fee": "US$30.00 / 1M tokens" }'
    ),
    bypass_cache=True,
)

model_fees = json.loads(result.extracted_content)

print(len(model_fees))

with open(".data/data.json", "w", encoding="utf-8") as f:
    f.write(result.extracted_content)
```

## Example 2: Extract Relevant Content

In this example, we instruct the LLM to extract only content related to technology from the NBC News business page.

```python
crawler = WebCrawler()
crawler.warmup()

result = crawler.run(
        url="https://www.nbcnews.com/business",
        extraction_strategy=LLMExtractionStrategy(
            provider="openai/gpt-4o",
            api_token=os.getenv('OPENAI_API_KEY'),
            instruction="Extract only content related to technology"
        ),
    bypass_cache=True,
    )

model_fees = json.loads(result.extracted_content)

print(len(model_fees))

with open(".data/data.json", "w", encoding="utf-8") as f:
    f.write(result.extracted_content)
```

## Customizing LLM Provider

Under the hood, Crawl4AI uses the `litellm` library, which allows you to use any LLM provider you want. Just pass the correct model name and API token.

```python
extraction_strategy=LLMExtractionStrategy(
    provider="your_llm_provider/model_name",
    api_token="your_api_token",
    instruction="Your extraction instruction"
)
```

This flexibility allows you to integrate with various LLM providers and tailor the extraction process to your specific needs.

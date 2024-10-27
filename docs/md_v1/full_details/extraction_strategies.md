## Extraction Strategies 🧠

Crawl4AI offers powerful extraction strategies to derive meaningful information from web content. Let's dive into three of the most important strategies: `CosineStrategy`, `LLMExtractionStrategy`, and the new `JsonCssExtractionStrategy`.

### LLMExtractionStrategy

`LLMExtractionStrategy` leverages a Language Model (LLM) to extract meaningful content from HTML. This strategy uses an external provider for LLM completions to perform extraction based on instructions.

#### When to Use
- Suitable for complex extraction tasks requiring nuanced understanding.
- Ideal for scenarios where detailed instructions can guide the extraction process.
- Perfect for extracting specific types of information or content with precise guidelines.

#### Parameters
- `provider` (str, optional): Provider for language model completions (e.g., openai/gpt-4). Default is `DEFAULT_PROVIDER`.
- `api_token` (str, optional): API token for the provider. If not provided, it will try to load from the environment variable `OPENAI_API_KEY`.
- `instruction` (str, optional): Instructions to guide the LLM on how to perform the extraction. Default is `None`.

#### Example Without Instructions
```python
import asyncio
import os
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Define extraction strategy without instructions
        strategy = LLMExtractionStrategy(
            provider='openai',
            api_token=os.getenv('OPENAI_API_KEY')
        )

        # Sample URL
        url = "https://www.nbcnews.com/business"

        # Run the crawler with the extraction strategy
        result = await crawler.arun(url=url, extraction_strategy=strategy)
        print(result.extracted_content)

asyncio.run(main())
```

#### Example With Instructions
```python
import asyncio
import os
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Define extraction strategy with instructions
        strategy = LLMExtractionStrategy(
            provider='openai',
            api_token=os.getenv('OPENAI_API_KEY'),
            instruction="Extract only financial news and summarize key points."
        )

        # Sample URL
        url = "https://www.nbcnews.com/business"

        # Run the crawler with the extraction strategy
        result = await crawler.arun(url=url, extraction_strategy=strategy)
        print(result.extracted_content)

asyncio.run(main())
```

### JsonCssExtractionStrategy

`JsonCssExtractionStrategy` is a powerful tool for extracting structured data from HTML using CSS selectors. It allows you to define a schema that maps CSS selectors to specific fields, enabling precise and efficient data extraction.

#### When to Use
- Ideal for extracting structured data from websites with consistent HTML structures.
- Perfect for scenarios where you need to extract specific elements or attributes from a webpage.
- Suitable for creating datasets from web pages with tabular or list-based information.

#### Parameters
- `schema` (Dict[str, Any]): A dictionary defining the extraction schema, including base selector and field definitions.

#### Example
```python
import asyncio
import json
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Define the extraction schema
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
                },
                {
                    "name": "link",
                    "selector": "a",
                    "type": "attribute",
                    "attribute": "href"
                }
            ],
        }

        # Create the extraction strategy
        strategy = JsonCssExtractionStrategy(schema, verbose=True)

        # Sample URL
        url = "https://www.nbcnews.com/business"

        # Run the crawler with the extraction strategy
        result = await crawler.arun(url=url, extraction_strategy=strategy)
        
        # Parse and print the extracted content
        extracted_data = json.loads(result.extracted_content)
        print(json.dumps(extracted_data, indent=2))

asyncio.run(main())
```

#### Use Cases for JsonCssExtractionStrategy
- Extracting product information from e-commerce websites.
- Gathering news articles and their metadata from news portals.
- Collecting user reviews and ratings from review websites.
- Extracting job listings from job boards.

By choosing the right extraction strategy, you can effectively extract the most relevant and useful information from web content. Whether you need fast, accurate semantic segmentation with `CosineStrategy`, nuanced, instruction-based extraction with `LLMExtractionStrategy`, or precise structured data extraction with `JsonCssExtractionStrategy`, Crawl4AI has you covered. Happy extracting! 🕵️‍♂️✨

For more details on schema definitions and advanced extraction strategies, check out the[Advanced JsonCssExtraction](../full_details/advanced_jsoncss_extraction.md).


### CosineStrategy

`CosineStrategy` uses hierarchical clustering based on cosine similarity to group text chunks into meaningful clusters. This method converts each chunk into its embedding and then clusters them to form semantical chunks.

#### When to Use
- Ideal for fast, accurate semantic segmentation of text.
- Perfect for scenarios where LLMs might be overkill or too slow.
- Suitable for narrowing down content based on specific queries or keywords.

#### Parameters
- `semantic_filter` (str, optional): Keywords for filtering relevant documents before clustering. Documents are filtered based on their cosine similarity to the keyword filter embedding. Default is `None`.
- `word_count_threshold` (int, optional): Minimum number of words per cluster. Default is `20`.
- `max_dist` (float, optional): Maximum cophenetic distance on the dendrogram to form clusters. Default is `0.2`.
- `linkage_method` (str, optional): Linkage method for hierarchical clustering. Default is `'ward'`.
- `top_k` (int, optional): Number of top categories to extract. Default is `3`.
- `model_name` (str, optional): Model name for embedding generation. Default is `'BAAI/bge-small-en-v1.5'`.

#### Example
```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import CosineStrategy

async def main():
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Define extraction strategy
        strategy = CosineStrategy(
            semantic_filter="finance economy stock market",
            word_count_threshold=10,
            max_dist=0.2,
            linkage_method='ward',
            top_k=3,
            model_name='BAAI/bge-small-en-v1.5'
        )

        # Sample URL
        url = "https://www.nbcnews.com/business"

        # Run the crawler with the extraction strategy
        result = await crawler.arun(url=url, extraction_strategy=strategy)
        print(result.extracted_content)

asyncio.run(main())
```

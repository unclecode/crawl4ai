# JSON CSS Extraction Strategy with AsyncWebCrawler

The `JsonCssExtractionStrategy` is a powerful feature of Crawl4AI that allows you to extract structured data from web pages using CSS selectors. This method is particularly useful when you need to extract specific data points from a consistent HTML structure, such as tables or repeated elements. Here's how to use it with the AsyncWebCrawler.

## Overview

The `JsonCssExtractionStrategy` works by defining a schema that specifies:
1. A base CSS selector for the repeating elements
2. Fields to extract from each element, each with its own CSS selector

This strategy is fast and efficient, as it doesn't rely on external services like LLMs for extraction.

## Example: Extracting Cryptocurrency Prices from Coinbase

Let's look at an example that extracts cryptocurrency prices from the Coinbase explore page.

```python
import json
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def extract_structured_data_using_css_extractor():
    print("\n--- Using JsonCssExtractionStrategy for Fast Structured Output ---")
    
    # Define the extraction schema
    schema = {
        "name": "Coinbase Crypto Prices",
        "baseSelector": ".cds-tableRow-t45thuk",
        "fields": [
            {
                "name": "crypto",
                "selector": "td:nth-child(1) h2",
                "type": "text",
            },
            {
                "name": "symbol",
                "selector": "td:nth-child(1) p",
                "type": "text",
            },
            {
                "name": "price",
                "selector": "td:nth-child(2)",
                "type": "text",
            }
        ],
    }

    # Create the extraction strategy
    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    # Use the AsyncWebCrawler with the extraction strategy
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://www.coinbase.com/explore",
            extraction_strategy=extraction_strategy,
            bypass_cache=True,
        )

        assert result.success, "Failed to crawl the page"

        # Parse the extracted content
        crypto_prices = json.loads(result.extracted_content)
        print(f"Successfully extracted {len(crypto_prices)} cryptocurrency prices")
        print(json.dumps(crypto_prices[0], indent=2))

    return crypto_prices

# Run the async function
asyncio.run(extract_structured_data_using_css_extractor())
```

## Explanation of the Schema

The schema defines how to extract the data:

- `name`: A descriptive name for the extraction task.
- `baseSelector`: The CSS selector for the repeating elements (in this case, table rows).
- `fields`: An array of fields to extract from each element:
  - `name`: The name to give the extracted data.
  - `selector`: The CSS selector to find the specific data within the base element.
  - `type`: The type of data to extract (usually "text" for textual content).

## Advantages of JsonCssExtractionStrategy

1. **Speed**: CSS selectors are fast to execute, making this method efficient for large datasets.
2. **Precision**: You can target exactly the elements you need.
3. **Structured Output**: The result is already structured as JSON, ready for further processing.
4. **No External Dependencies**: Unlike LLM-based strategies, this doesn't require any API calls to external services.

## Tips for Using JsonCssExtractionStrategy

1. **Inspect the Page**: Use browser developer tools to identify the correct CSS selectors.
2. **Test Selectors**: Verify your selectors in the browser console before using them in the script.
3. **Handle Dynamic Content**: If the page uses JavaScript to load content, you may need to combine this with JS execution (see the Advanced Usage section).
4. **Error Handling**: Always check the `result.success` flag and handle potential failures.

## Advanced Usage: Combining with JavaScript Execution

For pages that load data dynamically, you can combine the `JsonCssExtractionStrategy` with JavaScript execution:

```python
async def extract_dynamic_structured_data():
    schema = {
        "name": "Dynamic Crypto Prices",
        "baseSelector": ".crypto-row",
        "fields": [
            {"name": "name", "selector": ".crypto-name", "type": "text"},
            {"name": "price", "selector": ".crypto-price", "type": "text"},
        ]
    }

    js_code = """
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise(resolve => setTimeout(resolve, 2000));  // Wait for 2 seconds
    """

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url="https://example.com/crypto-prices",
            extraction_strategy=extraction_strategy,
            js_code=js_code,
            wait_for=".crypto-row:nth-child(20)",  # Wait for 20 rows to load
            bypass_cache=True,
        )

        crypto_data = json.loads(result.extracted_content)
        print(f"Extracted {len(crypto_data)} cryptocurrency entries")

asyncio.run(extract_dynamic_structured_data())
```

This advanced example demonstrates how to:
1. Execute JavaScript to trigger dynamic content loading.
2. Wait for a specific condition (20 rows loaded) before extraction.
3. Extract data from the dynamically loaded content.

By mastering the `JsonCssExtractionStrategy`, you can efficiently extract structured data from a wide variety of web pages, making it a valuable tool in your web scraping toolkit.

For more details on schema definitions and advanced extraction strategies, check out the[Advanced JsonCssExtraction](../full_details/advanced_jsoncss_extraction.md).
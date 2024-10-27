# Summarization Example with AsyncWebCrawler

This example demonstrates how to use Crawl4AI's `AsyncWebCrawler` to extract a summary from a web page asynchronously. The goal is to obtain the title, a detailed summary, a brief summary, and a list of keywords from the given page.

## Step-by-Step Guide

1. **Import Necessary Modules**

    First, import the necessary modules and classes:

    ```python
    import os
    import json
    import asyncio
    from crawl4ai import AsyncWebCrawler
    from crawl4ai.extraction_strategy import LLMExtractionStrategy
    from crawl4ai.chunking_strategy import RegexChunking
    from pydantic import BaseModel, Field
    ```

2. **Define the URL to be Crawled**

    Set the URL of the web page you want to summarize:

    ```python
    url = 'https://marketplace.visualstudio.com/items?itemName=Unclecode.groqopilot'
    ```

3. **Define the Data Model**

    Use Pydantic to define the structure of the extracted data:

    ```python
    class PageSummary(BaseModel):
        title: str = Field(..., description="Title of the page.")
        summary: str = Field(..., description="Summary of the page.")
        brief_summary: str = Field(..., description="Brief summary of the page.")
        keywords: list = Field(..., description="Keywords assigned to the page.")
    ```

4. **Create the Extraction Strategy**

    Set up the `LLMExtractionStrategy` with the necessary parameters:

    ```python
    extraction_strategy = LLMExtractionStrategy(
        provider="openai/gpt-4o", 
        api_token=os.getenv('OPENAI_API_KEY'), 
        schema=PageSummary.model_json_schema(),
        extraction_type="schema",
        apply_chunking=False,
        instruction=(
            "From the crawled content, extract the following details: "
            "1. Title of the page "
            "2. Summary of the page, which is a detailed summary "
            "3. Brief summary of the page, which is a paragraph text "
            "4. Keywords assigned to the page, which is a list of keywords. "
            'The extracted JSON format should look like this: '
            '{ "title": "Page Title", "summary": "Detailed summary of the page.", '
            '"brief_summary": "Brief summary in a paragraph.", "keywords": ["keyword1", "keyword2", "keyword3"] }'
        )
    )
    ```

5. **Define the Async Crawl Function**

    Create an asynchronous function to run the crawler:

    ```python
    async def crawl_and_summarize(url):
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url=url,
                word_count_threshold=1,
                extraction_strategy=extraction_strategy,
                chunking_strategy=RegexChunking(),
                bypass_cache=True,
            )
            return result
    ```

6. **Run the Crawler and Process Results**

    Use asyncio to run the crawler and process the results:

    ```python
    async def main():
        result = await crawl_and_summarize(url)
        
        if result.success:
            page_summary = json.loads(result.extracted_content)
            print("Extracted Page Summary:")
            print(json.dumps(page_summary, indent=2))
            
            # Save the extracted data
            with open(".data/page_summary.json", "w", encoding="utf-8") as f:
                json.dump(page_summary, f, indent=2)
            print("Page summary saved to .data/page_summary.json")
        else:
            print(f"Failed to crawl and summarize the page. Error: {result.error_message}")

    # Run the async main function
    asyncio.run(main())
    ```

## Explanation

- **Importing Modules**: We import the necessary modules, including `AsyncWebCrawler` and `LLMExtractionStrategy` from Crawl4AI.
- **URL Definition**: We set the URL of the web page to crawl and summarize.
- **Data Model Definition**: We define the structure of the data to extract using Pydantic's `BaseModel`.
- **Extraction Strategy Setup**: We create an instance of `LLMExtractionStrategy` with the schema and detailed instructions for the extraction process.
- **Async Crawl Function**: We define an asynchronous function `crawl_and_summarize` that uses `AsyncWebCrawler` to perform the crawling and extraction.
- **Main Execution**: In the `main` function, we run the crawler, process the results, and save the extracted data.

## Advanced Usage: Crawling Multiple URLs

To demonstrate the power of `AsyncWebCrawler`, here's how you can summarize multiple pages concurrently:

```python
async def crawl_multiple_urls(urls):
    async with AsyncWebCrawler(verbose=True) as crawler:
        tasks = [crawler.arun(
            url=url,
            word_count_threshold=1,
            extraction_strategy=extraction_strategy,
            chunking_strategy=RegexChunking(),
            bypass_cache=True
        ) for url in urls]
        results = await asyncio.gather(*tasks)
    return results

async def main():
    urls = [
        'https://marketplace.visualstudio.com/items?itemName=Unclecode.groqopilot',
        'https://marketplace.visualstudio.com/items?itemName=GitHub.copilot',
        'https://marketplace.visualstudio.com/items?itemName=ms-python.python'
    ]
    results = await crawl_multiple_urls(urls)
    
    for i, result in enumerate(results):
        if result.success:
            page_summary = json.loads(result.extracted_content)
            print(f"\nSummary for URL {i+1}:")
            print(json.dumps(page_summary, indent=2))
        else:
            print(f"\nFailed to summarize URL {i+1}. Error: {result.error_message}")

asyncio.run(main())
```

This advanced example shows how to use `AsyncWebCrawler` to efficiently summarize multiple web pages concurrently, significantly reducing the total processing time compared to sequential crawling.

By leveraging the asynchronous capabilities of Crawl4AI, you can perform advanced web crawling and data extraction tasks with improved efficiency and scalability.
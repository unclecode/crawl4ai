## Summarization Example

This example demonstrates how to use `Crawl4AI` to extract a summary from a web page. The goal is to obtain the title, a detailed summary, a brief summary, and a list of keywords from the given page.

### Step-by-Step Guide

1. **Import Necessary Modules**

    First, import the necessary modules and classes.

    ```python
    import os
    import time
    import json
    from crawl4ai.web_crawler import WebCrawler
    from crawl4ai.chunking_strategy import *
    from crawl4ai.extraction_strategy import *
    from crawl4ai.crawler_strategy import *
    from pydantic import BaseModel, Field
    ```

2. **Define the URL to be Crawled**

    Set the URL of the web page you want to summarize.

    ```python
    url = r'https://marketplace.visualstudio.com/items?itemName=Unclecode.groqopilot'
    ```

3. **Initialize the WebCrawler**

    Create an instance of the `WebCrawler` and call the `warmup` method.

    ```python
    crawler = WebCrawler()
    crawler.warmup()
    ```

4. **Define the Data Model**

    Use Pydantic to define the structure of the extracted data.

    ```python
    class PageSummary(BaseModel):
        title: str = Field(..., description="Title of the page.")
        summary: str = Field(..., description="Summary of the page.")
        brief_summary: str = Field(..., description="Brief summary of the page.")
        keywords: list = Field(..., description="Keywords assigned to the page.")
    ```

5. **Run the Crawler**

    Set up and run the crawler with the `LLMExtractionStrategy`. Provide the necessary parameters, including the schema for the extracted data and the instruction for the LLM.

    ```python
    result = crawler.run(
        url=url,
        word_count_threshold=1,
        extraction_strategy=LLMExtractionStrategy(
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
        ),
        bypass_cache=True,
    )
    ```

6. **Process the Extracted Data**

    Load the extracted content into a JSON object and print it.

    ```python
    page_summary = json.loads(result.extracted_content)
    print(page_summary)
    ```

7. **Save the Extracted Data**

    Save the extracted data to a file for further use.

    ```python
    with open(".data/page_summary.json", "w", encoding="utf-8") as f:
        f.write(result.extracted_content)
    ```

### Explanation

- **Importing Modules**: Import the necessary modules, including `WebCrawler` and `LLMExtractionStrategy` from `Crawl4AI`.
- **URL Definition**: Set the URL of the web page you want to crawl and summarize.
- **WebCrawler Initialization**: Create an instance of `WebCrawler` and call the `warmup` method to prepare the crawler.
- **Data Model Definition**: Define the structure of the data you want to extract using Pydantic's `BaseModel`.
- **Crawler Execution**: Run the crawler with the `LLMExtractionStrategy`, providing the schema and detailed instructions for the extraction process.
- **Data Processing**: Load the extracted content into a JSON object and print it to verify the results.
- **Data Saving**: Save the extracted data to a file for further use.

This example demonstrates how to harness the power of `Crawl4AI` to perform advanced web crawling and data extraction tasks with minimal code.

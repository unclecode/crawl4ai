# JS Execution & CSS Filtering with AsyncWebCrawler

In this example, we'll demonstrate how to use Crawl4AI's AsyncWebCrawler to execute JavaScript, filter data with CSS selectors, and use a cosine similarity strategy to extract relevant content. This approach is particularly useful when you need to interact with dynamic content on web pages, such as clicking "Load More" buttons.

## Example: Extracting Structured Data Asynchronously

```python
import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.chunking_strategy import RegexChunking
from crawl4ai.extraction_strategy import CosineStrategy
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

async def main():
    # Define the JavaScript code to click the "Load More" button
    js_code = """
    const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More'));
    if (loadMoreButton) {
        loadMoreButton.click();
        // Wait for new content to load
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    """

    # Define a wait_for function to ensure content is loaded
    wait_for = """
    () => {
        const articles = document.querySelectorAll('article.tease-card');
        return articles.length > 10;
    }
    """

    async with AsyncWebCrawler(verbose=True) as crawler:
        # Run the crawler with keyword filtering and CSS selector
        result = await crawler.arun(
            url="https://www.nbcnews.com/business",
            js_code=js_code,
            wait_for=wait_for,
            css_selector="article.tease-card",
            extraction_strategy=CosineStrategy(
                semantic_filter="technology",
            ),
            chunking_strategy=RegexChunking(),
        )

    # Display the extracted result
    print(result.extracted_content)

# Run the async function
asyncio.run(main())
```

### Explanation

1. **Asynchronous Execution**: We use `AsyncWebCrawler` with async/await syntax for non-blocking execution.

2. **JavaScript Execution**: The `js_code` variable contains JavaScript code that simulates clicking a "Load More" button and waits for new content to load.

3. **Wait Condition**: The `wait_for` function ensures that the page has loaded more than 10 articles before proceeding with the extraction.

4. **CSS Selector**: The `css_selector="article.tease-card"` parameter ensures that only article cards are extracted from the web page.

5. **Extraction Strategy**: The `CosineStrategy` is used with a semantic filter for "technology" to extract relevant content based on cosine similarity.

6. **Chunking Strategy**: We use `RegexChunking()` to split the content into manageable chunks for processing.

## Advanced Usage: Custom Session and Multiple Requests

For more complex scenarios where you need to maintain state across multiple requests or execute additional JavaScript after the initial page load, you can use a custom session:

```python
async def advanced_crawl():
    async with AsyncWebCrawler(verbose=True) as crawler:
        # Initial crawl with custom session
        result1 = await crawler.arun(
            url="https://www.nbcnews.com/business",
            js_code=js_code,
            wait_for=wait_for,
            css_selector="article.tease-card",
            session_id="business_session"
        )

        # Execute additional JavaScript in the same session
        result2 = await crawler.crawler_strategy.execute_js(
            session_id="business_session",
            js_code="window.scrollTo(0, document.body.scrollHeight);",
            wait_for_js="() => window.innerHeight + window.scrollY >= document.body.offsetHeight"
        )

        # Process results
        print("Initial crawl result:", result1.extracted_content)
        print("Additional JS execution result:", result2.html)

asyncio.run(advanced_crawl())
```

This advanced example demonstrates how to:
1. Use a custom session to maintain state across requests.
2. Execute additional JavaScript after the initial page load.
3. Wait for specific conditions using JavaScript functions.

## Try It Yourself

These examples demonstrate the power and flexibility of Crawl4AI's AsyncWebCrawler in handling complex web interactions and extracting meaningful data asynchronously. You can customize the JavaScript code, CSS selectors, extraction strategies, and waiting conditions to suit your specific requirements.
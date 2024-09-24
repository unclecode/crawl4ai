# JS Execution & CSS Filtering

In this example, we'll demonstrate how to use Crawl4AI to execute JavaScript, filter data with CSS selectors, and use a cosine similarity strategy to extract relevant content. This approach is particularly useful when you need to interact with dynamic content on web pages, such as clicking "Load More" buttons.

## Example: Extracting Structured Data

```python
# Import necessary modules
from crawl4ai import WebCrawler
from crawl4ai.chunking_strategy import *
from crawl4ai.extraction_strategy import *
from crawl4ai.crawler_strategy import *

# Define the JavaScript code to click the "Load More" button
js_code = ["""
const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More'));
loadMoreButton && loadMoreButton.click();
"""]

crawler = WebCrawler(verbose=True)
crawler.warmup()
# Run the crawler with keyword filtering and CSS selector
result = crawler.run(
    url="https://www.nbcnews.com/business",
    js=js_code,
    css_selector="p",
    extraction_strategy=CosineStrategy(
        semantic_filter="technology",
    ),
)

# Display the extracted result
print(result)
```

### Explanation

1. **JavaScript Execution**: The `js_code` variable contains JavaScript code that simulates clicking a "Load More" button. This is useful for loading additional content dynamically.
2. **CSS Selector**: The `css_selector="p"` parameter ensures that only paragraph (`<p>`) tags are extracted from the web page.
3. **Extraction Strategy**: The `CosineStrategy` is used with a semantic filter for "technology" to extract relevant content based on cosine similarity.

## Try It Yourself

This example demonstrates the power and flexibility of Crawl4AI in handling complex web interactions and extracting meaningful data. You can customize the JavaScript code, CSS selectors, and extraction strategies to suit your specific requirements.

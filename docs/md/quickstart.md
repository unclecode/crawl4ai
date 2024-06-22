# Quick Start Guide 🚀

Welcome to the Crawl4AI Quickstart Guide! In this tutorial, we'll walk you through the basic usage of Crawl4AI with a friendly and humorous tone. We'll cover everything from basic usage to advanced features like chunking and extraction strategies. Let's dive in! 🌟

## Getting Started 🛠️

First, let's create an instance of `WebCrawler` and call the `warmup()` function. This might take a few seconds the first time you run Crawl4AI, as it loads the required model files.

```python
from crawl4ai import WebCrawler

def create_crawler():
    crawler = WebCrawler(verbose=True)
    crawler.warmup()
    return crawler

crawler = create_crawler()
```

### Basic Usage

Simply provide a URL and let Crawl4AI do the magic!

```python
result = crawler.run(url="https://www.nbcnews.com/business")
print(f"Basic crawl result: {result}")
```

### Taking Screenshots 📸

Let's take a screenshot of the page!

```python
result = crawler.run(url="https://www.nbcnews.com/business", screenshot=True)
with open("screenshot.png", "wb") as f:
    f.write(base64.b64decode(result.screenshot))
print("Screenshot saved to 'screenshot.png'!")
```

### Understanding Parameters 🧠

By default, Crawl4AI caches the results of your crawls. This means that subsequent crawls of the same URL will be much faster! Let's see this in action.

First crawl (caches the result):
```python
result = crawler.run(url="https://www.nbcnews.com/business")
print(f"First crawl result: {result}")
```

Force to crawl again:
```python
result = crawler.run(url="https://www.nbcnews.com/business", bypass_cache=True)
print(f"Second crawl result: {result}")
```

### Adding a Chunking Strategy 🧩

Let's add a chunking strategy: `RegexChunking`! This strategy splits the text based on a given regex pattern.

```python
from crawl4ai.chunking_strategy import RegexChunking

result = crawler.run(
    url="https://www.nbcnews.com/business",
    chunking_strategy=RegexChunking(patterns=["\n\n"])
)
print(f"RegexChunking result: {result}")
```

You can also use `NlpSentenceChunking` which splits the text into sentences using NLP techniques.

```python
from crawl4ai.chunking_strategy import NlpSentenceChunking

result = crawler.run(
    url="https://www.nbcnews.com/business",
    chunking_strategy=NlpSentenceChunking()
)
print(f"NlpSentenceChunking result: {result}")
```

### Adding an Extraction Strategy 🧠

Let's get smarter with an extraction strategy: `CosineStrategy`! This strategy uses cosine similarity to extract semantically similar blocks of text.

```python
from crawl4ai.extraction_strategy import CosineStrategy

result = crawler.run(
    url="https://www.nbcnews.com/business",
    extraction_strategy=CosineStrategy(
        word_count_threshold=10, 
        max_dist=0.2, 
        linkage_method="ward", 
        top_k=3
    )
)
print(f"CosineStrategy result: {result}")
```

You can also pass other parameters like `semantic_filter` to extract specific content.

```python
result = crawler.run(
    url="https://www.nbcnews.com/business",
    extraction_strategy=CosineStrategy(
        semantic_filter="inflation rent prices"
    )
)
print(f"CosineStrategy result with semantic filter: {result}")
```

### Using LLMExtractionStrategy 🤖

Time to bring in the big guns: `LLMExtractionStrategy` without instructions! This strategy uses a large language model to extract relevant information from the web page.

```python
from crawl4ai.extraction_strategy import LLMExtractionStrategy
import os

result = crawler.run(
    url="https://www.nbcnews.com/business",
    extraction_strategy=LLMExtractionStrategy(
        provider="openai/gpt-4o", 
        api_token=os.getenv('OPENAI_API_KEY')
    )
)
print(f"LLMExtractionStrategy (no instructions) result: {result}")
```

You can also provide specific instructions to guide the extraction.

```python
result = crawler.run(
    url="https://www.nbcnews.com/business",
    extraction_strategy=LLMExtractionStrategy(
        provider="openai/gpt-4o",
        api_token=os.getenv('OPENAI_API_KEY'),
        instruction="I am interested in only financial news"
    )
)
print(f"LLMExtractionStrategy (with instructions) result: {result}")
```

### Targeted Extraction 🎯

Let's use a CSS selector to extract only H2 tags!

```python
result = crawler.run(
    url="https://www.nbcnews.com/business",
    css_selector="h2"
)
print(f"CSS Selector (H2 tags) result: {result}")
```

### Interactive Extraction 🖱️

Passing JavaScript code to click the 'Load More' button!

```python
js_code = """
const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More'));
loadMoreButton && loadMoreButton.click();
"""

result = crawler.run(
    url="https://www.nbcnews.com/business",
    js=js_code
)
print(f"JavaScript Code (Load More button) result: {result}")
```

### Using Crawler Hooks 🔗

Let's see how we can customize the crawler using hooks!

```python
def on_driver_created(driver):
    print("[HOOK] on_driver_created")
    driver.maximize_window()
    driver.get('https://example.com/login')
    driver.find_element(By.NAME, 'username').send_keys('testuser')
    driver.find_element(By.NAME, 'password').send_keys('password123')
    driver.find_element(By.NAME, 'login').click()
    driver.add_cookie({'name': 'test_cookie', 'value': 'cookie_value'})
    return driver        

def before_get_url(driver):
    print("[HOOK] before_get_url")
    driver.execute_cdp_cmd('Network.enable', {})
    driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {'X-Test-Header': 'test'}})
    return driver

def after_get_url(driver):
    print("[HOOK] after_get_url")
    print(driver.current_url)
    return driver

def before_return_html(driver, html):
    print("[HOOK] before_return_html")
    print(len(html))
    return driver

crawler.set_hook('on_driver_created', on_driver_created)
crawler.set_hook('before_get_url', before_get_url)
crawler.set_hook('after_get_url', after_get_url)
crawler.set_hook('before_return_html', before_return_html)

result = crawler.run(url="https://example.com")
print(f"Crawler Hooks result: {result}")
```

## Congratulations! 🎉

You've made it through the Crawl4AI Quickstart Guide! Now go forth and crawl the web like a pro! 🕸️

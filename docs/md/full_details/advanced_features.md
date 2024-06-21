# Advanced Features

Crawl4AI offers a range of advanced features that allow you to fine-tune your web crawling and data extraction process. This section will cover some of these advanced features, including taking screenshots, extracting media and links, customizing the user agent, using custom hooks, and leveraging CSS selectors.

## Taking Screenshots 📸

One of the cool features of Crawl4AI is the ability to take screenshots of the web pages you're crawling. This can be particularly useful for visual verification or for capturing the state of dynamic content.

Here's how you can take a screenshot:

```python
from crawl4ai import WebCrawler
import base64

# Create the WebCrawler instance
crawler = WebCrawler()
crawler.warmup()

# Run the crawler with the screenshot parameter
result = crawler.run(url="https://www.nbcnews.com/business", screenshot=True)

# Save the screenshot to a file
with open("screenshot.png", "wb") as f:
    f.write(base64.b64decode(result.screenshot))

print("Screenshot saved to 'screenshot.png'!")
```

In this example, we create a `WebCrawler` instance, warm it up, and then run it with the `screenshot` parameter set to `True`. The screenshot is saved as a base64 encoded string in the result, which we then decode and save as a PNG file.

## Extracting Media and Links 🎨🔗

Crawl4AI can extract all media tags (images, audio, and video) and links (both internal and external) from a web page. This feature is useful for collecting multimedia content or analyzing link structures.

Here's an example:

```python
from crawl4ai import WebCrawler

# Create the WebCrawler instance
crawler = WebCrawler()
crawler.warmup()

# Run the crawler
result = crawler.run(url="https://www.nbcnews.com/business")

print("Extracted media:", result.media)
print("Extracted links:", result.links)
```

In this example, the `result` object contains dictionaries for media and links, which you can access and use as needed.

## Customizing the User Agent 🕵️‍♂️

Crawl4AI allows you to set a custom user agent for your HTTP requests. This can help you avoid detection by web servers or simulate different browsing environments.

Here's how to set a custom user agent:

```python
from crawl4ai import WebCrawler

# Create the WebCrawler instance
crawler = WebCrawler()
crawler.warmup()

# Run the crawler with a custom user agent
result = crawler.run(url="https://www.nbcnews.com/business", user_agent="Mozilla/5.0 (compatible; MyCrawler/1.0)")

print("Crawl result:", result)
```

In this example, we specify a custom user agent string when running the crawler.

## Using Custom Hooks 🪝

Hooks are a powerful feature in Crawl4AI that allow you to customize the crawling process at various stages. You can define hooks for actions such as driver initialization, before and after URL fetching, and before returning the HTML.

Here's an example of using hooks:

```python
from crawl4ai import WebCrawler
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Define the hooks
def on_driver_created(driver):
    driver.maximize_window()
    driver.get('https://example.com/login')
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'username'))).send_keys('testuser')
    driver.find_element(By.NAME, 'password').send_keys('password123')
    driver.find_element(By.NAME, 'login').click()
    return driver

def before_get_url(driver):
    driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {'X-Test-Header': 'test'}})
    return driver

# Create the WebCrawler instance
crawler = WebCrawler()
crawler.warmup()

# Set the hooks
crawler.set_hook('on_driver_created', on_driver_created)
crawler.set_hook('before_get_url', before_get_url)

# Run the crawler
result = crawler.run(url="https://example.com")

print("Crawl result:", result)
```

In this example, we define hooks to handle driver initialization and custom headers before fetching the URL.

## Using CSS Selectors 🎯

CSS selectors allow you to target specific elements on a web page for extraction. This can be useful for scraping structured content, such as articles or product details.

Here's an example of using a CSS selector:

```python
from crawl4ai import WebCrawler

# Create the WebCrawler instance
crawler = WebCrawler()
crawler.warmup()

# Run the crawler with a CSS selector to extract only H2 tags
result = crawler.run(url="https://www.nbcnews.com/business", css_selector="h2")

print("Extracted H2 tags:", result.extracted_content)
```

In this example, we use the `css_selector` parameter to extract only the H2 tags from the web page.

---

With these advanced features, you can leverage Crawl4AI to perform sophisticated web crawling and data extraction tasks. Whether you need to take screenshots, extract specific elements, customize the crawling process, or set custom headers, Crawl4AI provides the flexibility and power to meet your needs. Happy crawling! 🕷️🚀

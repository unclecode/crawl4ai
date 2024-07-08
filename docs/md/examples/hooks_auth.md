# Hooks & Auth

Crawl4AI allows you to customize the behavior of the web crawler using hooks. Hooks are functions that are called at specific points in the crawling process, allowing you to modify the crawler's behavior or perform additional actions. This example demonstrates how to use various hooks to customize the crawling process.

## Example: Using Crawler Hooks

Let's see how we can customize the crawler using hooks! In this example, we'll:

1. Maximize the browser window and log in to a website when the driver is created.
2. Add a custom header before fetching the URL.
3. Log the current URL after fetching it.
4. Log the length of the HTML before returning it.

### Hook Definitions

```python
from crawl4ai.web_crawler import WebCrawler
from crawl4ai.crawler_strategy import *

def on_driver_created(driver):
    print("[HOOK] on_driver_created")
    # Example customization: maximize the window
    driver.maximize_window()
    
    # Example customization: logging in to a hypothetical website
    driver.get('https://example.com/login')
    
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, 'username'))
    )
    driver.find_element(By.NAME, 'username').send_keys('testuser')
    driver.find_element(By.NAME, 'password').send_keys('password123')
    driver.find_element(By.NAME, 'login').click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'welcome'))
    )
    # Add a custom cookie
    driver.add_cookie({'name': 'test_cookie', 'value': 'cookie_value'})
    return driver        
    

def before_get_url(driver):
    print("[HOOK] before_get_url")
    # Example customization: add a custom header
    # Enable Network domain for sending headers
    driver.execute_cdp_cmd('Network.enable', {})
    # Add a custom header
    driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {'headers': {'X-Test-Header': 'test'}})
    return driver

def after_get_url(driver):
    print("[HOOK] after_get_url")
    # Example customization: log the URL
    print(driver.current_url)
    return driver

def before_return_html(driver, html):
    print("[HOOK] before_return_html")
    # Example customization: log the HTML
    print(len(html))
    return driver
```

### Using the Hooks with the WebCrawler

```python
print("\n🔗 [bold cyan]Using Crawler Hooks: Let's see how we can customize the crawler using hooks![/bold cyan]", True)
crawler_strategy = LocalSeleniumCrawlerStrategy(verbose=True)
crawler_strategy.set_hook('on_driver_created', on_driver_created)
crawler_strategy.set_hook('before_get_url', before_get_url)
crawler_strategy.set_hook('after_get_url', after_get_url)
crawler_strategy.set_hook('before_return_html', before_return_html)
crawler = WebCrawler(verbose=True, crawler_strategy=crawler_strategy)
crawler.warmup()

result = crawler.run(url="https://example.com")

print("[LOG] 📦 [bold yellow]Crawler Hooks result:[/bold yellow]")
print(result)
```

### Explanation

- `on_driver_created`: This hook is called when the Selenium driver is created. In this example, it maximizes the window, logs in to a website, and adds a custom cookie.
- `before_get_url`: This hook is called right before Selenium fetches the URL. In this example, it adds a custom HTTP header.
- `after_get_url`: This hook is called after Selenium fetches the URL. In this example, it logs the current URL.
- `before_return_html`: This hook is called before returning the HTML content. In this example, it logs the length of the HTML content.

### Additional Ideas

- **Add custom headers to requests**: You can add custom headers to the requests using the `before_get_url` hook.
- **Perform safety checks**: Use the hooks to perform safety checks before the crawling process starts.
- **Modify the HTML content**: Use the `before_return_html` hook to modify the HTML content before it is returned.
- **Log additional information**: Use the hooks to log additional information for debugging or monitoring purposes.

By using these hooks, you can customize the behavior of the crawler to suit your specific needs.

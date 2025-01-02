# Parameter Reference Table

| File Name | Parameter Name | Code Usage | Strategy/Class | Description |
|-----------|---------------|------------|----------------|-------------|
| async_crawler_strategy.py | user_agent | `kwargs.get("user_agent")` | AsyncPlaywrightCrawlerStrategy | User agent string for browser identification |
| async_crawler_strategy.py | proxy | `kwargs.get("proxy")` | AsyncPlaywrightCrawlerStrategy | Proxy server configuration for network requests |
| async_crawler_strategy.py | proxy_config | `kwargs.get("proxy_config")` | AsyncPlaywrightCrawlerStrategy | Detailed proxy configuration including auth |
| async_crawler_strategy.py | headless | `kwargs.get("headless", True)` | AsyncPlaywrightCrawlerStrategy | Whether to run browser in headless mode |
| async_crawler_strategy.py | browser_type | `kwargs.get("browser_type", "chromium")` | AsyncPlaywrightCrawlerStrategy | Type of browser to use (chromium/firefox/webkit) |
| async_crawler_strategy.py | headers | `kwargs.get("headers", {})` | AsyncPlaywrightCrawlerStrategy | Custom HTTP headers for requests |
| async_crawler_strategy.py | verbose | `kwargs.get("verbose", False)` | AsyncPlaywrightCrawlerStrategy | Enable detailed logging output |
| async_crawler_strategy.py | sleep_on_close | `kwargs.get("sleep_on_close", False)` | AsyncPlaywrightCrawlerStrategy | Add delay before closing browser |
| async_crawler_strategy.py | use_remote_browser | `kwargs.get("use_remote_browser", False)` | AsyncPlaywrightCrawlerStrategy | Use managed browser instance |
| async_crawler_strategy.py | user_data_dir | `kwargs.get("user_data_dir", None)` | AsyncPlaywrightCrawlerStrategy | Custom directory for browser profile data |
| async_crawler_strategy.py | session_id | `kwargs.get("session_id")` | AsyncPlaywrightCrawlerStrategy | Unique identifier for browser session |
| async_crawler_strategy.py | override_navigator | `kwargs.get("override_navigator", False)` | AsyncPlaywrightCrawlerStrategy | Override browser navigator properties |
| async_crawler_strategy.py | simulate_user | `kwargs.get("simulate_user", False)` | AsyncPlaywrightCrawlerStrategy | Simulate human-like behavior |
| async_crawler_strategy.py | magic | `kwargs.get("magic", False)` | AsyncPlaywrightCrawlerStrategy | Enable advanced anti-detection features |
| async_crawler_strategy.py | log_console | `kwargs.get("log_console", False)` | AsyncPlaywrightCrawlerStrategy | Log browser console messages |
| async_crawler_strategy.py | js_only | `kwargs.get("js_only", False)` | AsyncPlaywrightCrawlerStrategy | Only execute JavaScript without page load |
| async_crawler_strategy.py | page_timeout | `kwargs.get("page_timeout", 60000)` | AsyncPlaywrightCrawlerStrategy | Timeout for page load in milliseconds |
| async_crawler_strategy.py | ignore_body_visibility | `kwargs.get("ignore_body_visibility", True)` | AsyncPlaywrightCrawlerStrategy | Process page even if body is hidden |
| async_crawler_strategy.py | js_code | `kwargs.get("js_code", kwargs.get("js", self.js_code))` | AsyncPlaywrightCrawlerStrategy | Custom JavaScript code to execute |
| async_crawler_strategy.py | wait_for | `kwargs.get("wait_for")` | AsyncPlaywrightCrawlerStrategy | Wait for specific element/condition |
| async_crawler_strategy.py | process_iframes | `kwargs.get("process_iframes", False)` | AsyncPlaywrightCrawlerStrategy | Extract content from iframes |
| async_crawler_strategy.py | delay_before_return_html | `kwargs.get("delay_before_return_html")` | AsyncPlaywrightCrawlerStrategy | Additional delay before returning HTML |
| async_crawler_strategy.py | remove_overlay_elements | `kwargs.get("remove_overlay_elements", False)` | AsyncPlaywrightCrawlerStrategy | Remove pop-ups and overlay elements |
| async_crawler_strategy.py | screenshot | `kwargs.get("screenshot")` | AsyncPlaywrightCrawlerStrategy | Take page screenshot |
| async_crawler_strategy.py | screenshot_wait_for | `kwargs.get("screenshot_wait_for")` | AsyncPlaywrightCrawlerStrategy | Wait before taking screenshot |
| async_crawler_strategy.py | semaphore_count | `kwargs.get("semaphore_count", 5)` | AsyncPlaywrightCrawlerStrategy | Concurrent request limit |
| async_webcrawler.py | verbose | `kwargs.get("verbose", False)` | AsyncWebCrawler | Enable detailed logging |
| async_webcrawler.py | warmup | `kwargs.get("warmup", True)` | AsyncWebCrawler | Initialize crawler with warmup request |
| async_webcrawler.py | session_id | `kwargs.get("session_id", None)` | AsyncWebCrawler | Session identifier for browser reuse |
| async_webcrawler.py | only_text | `kwargs.get("only_text", False)` | AsyncWebCrawler | Extract only text content |
| async_webcrawler.py | bypass_cache | `kwargs.get("bypass_cache", False)` | AsyncWebCrawler | Skip cache and force fresh crawl |
| async_webcrawler.py | cache_mode | `kwargs.get("cache_mode", CacheMode.ENABLE)` | AsyncWebCrawler | Cache handling mode for request |
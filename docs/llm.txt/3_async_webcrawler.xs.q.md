setup_usage: Initialize AsyncWebCrawler with BrowserConfig for basic web crawling | crawler setup, initialization, basic usage | AsyncWebCrawler(config=BrowserConfig(browser_type="chromium", headless=True))
browser_configuration: Configure browser settings including type, headless mode, viewport, and proxy | browser setup, browser settings, viewport config | BrowserConfig(browser_type="firefox", headless=False, viewport_width=1920)
docker_setup: Run crawler in Docker using python slim image with playwright installation | docker configuration, containerization | FROM python:3.10-slim; RUN pip install crawl4ai playwright
crawler_strategy: Use AsyncPlaywrightCrawlerStrategy as default crawler implementation | crawler implementation, strategy pattern | AsyncWebCrawler(crawler_strategy=AsyncPlaywrightCrawlerStrategy())
dynamic_content: Execute custom JavaScript code for dynamic content loading | javascript execution, dynamic loading, interaction | CrawlerRunConfig(js_code=["document.querySelector('.load-more').click()"])
extraction_strategies: Choose between JSON CSS, LLM, or No extraction strategies for content parsing | content extraction, parsing strategies | CrawlerRunConfig(extraction_strategy=JsonCssExtractionStrategy(selectors={"title": "h1"}))
cache_management: Control cache behavior with ENABLED, BYPASS, or DISABLED modes | caching, cache control, performance | await c.aclear_cache(), await c.aflush_cache()
parallel_crawling: Crawl multiple URLs concurrently with semaphore control | batch crawling, parallel execution | CrawlerRunConfig(semaphore_count=10)
media_capture: Capture screenshots and PDFs of crawled pages | screenshots, pdf generation, media export | CrawlerRunConfig(screenshot=True, pdf=True)
troubleshooting: Common issues include browser launch failures, timeouts, and stale cache | error handling, debugging, fixes | playwright install chromium
best_practices: Use modular crawl logic, proxies, and proper resource cleanup | optimization, maintenance, efficiency | async with AsyncWebCrawler() as c
custom_settings: Configure user agent and local file access options | customization, configuration options | user_agent="MyUserAgent", file:// prefix
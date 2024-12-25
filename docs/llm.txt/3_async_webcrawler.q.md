quick_start: Basic async crawl setup requires BrowserConfig and AsyncWebCrawler initialization | getting started, basic usage, initialization | asyncio.run(AsyncWebCrawler(browser_config=BrowserConfig(browser_type="chromium", headless=True)))
browser_types: AsyncWebCrawler supports multiple browser types including Chromium and Firefox | supported browsers, browser options | BrowserConfig(browser_type="chromium")
headless_mode: Browser can run in headless mode without UI for better performance | invisible browser, no GUI | BrowserConfig(headless=True)
viewport_settings: Configure browser viewport dimensions for proper page rendering | screen size, window size | BrowserConfig(viewport_width=1920, viewport_height=1080)
docker_deployment: AsyncWebCrawler can run in Docker containers for scalability | containerization, deployment | FROM python:3.10-slim; RUN pip install crawl4ai playwright
dynamic_content: Handle JavaScript-loaded content using custom JS injection | javascript handling, dynamic loading | CrawlerRunConfig(js_code=["document.querySelector('.load-more').click()"])
extraction_strategies: Multiple strategies available for content extraction including JsonCssExtractionStrategy and LLMExtractionStrategy | content extraction, data parsing | JsonCssExtractionStrategy(selectors={"title": "h1"})
caching_modes: Control cache behavior with different modes: ENABLED, BYPASS, DISABLED | cache control, caching options | CrawlerRunConfig(cache_mode=CacheMode.ENABLED)
batch_crawling: Process multiple URLs concurrently using arun_many method | parallel crawling, multiple urls | crawler.arun_many(urls, config=CrawlerRunConfig(semaphore_count=10))
rate_limiting: Control crawl rate using mean_delay and max_range parameters | throttling, delay control | CrawlerRunConfig(mean_delay=1.0, max_range=0.5)
visual_capture: Generate screenshots and PDFs of crawled pages | page capture, visual output | CrawlerRunConfig(screenshot=True, pdf=True)
error_handling: Common issues include browser launch failures, timeouts, and JS execution problems | troubleshooting, debugging | try/except blocks with crawler.logger
authentication: Handle login requirements through js_code or Playwright selectors | login handling, sessions | CrawlerRunConfig with login steps via js_code
proxy_configuration: Configure proxy settings to bypass IP restrictions | proxy setup, IP rotation | BrowserConfig(proxy="http://proxy-server:port")
chunking_strategies: Split content using regex or NLP-based chunking | content splitting, text processing | CrawlerRunConfig(chunking_strategy=RegexChunking())
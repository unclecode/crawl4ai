installation: Install Crawl4AI using pip and setup required dependencies | package installation, setup guide | pip install crawl4ai && crawl4ai-setup && playwright install chromium
basic_usage: Create AsyncWebCrawler instance to extract web content into markdown | quick start, basic crawling | async with AsyncWebCrawler(verbose=True) as crawler: result = await crawler.arun("https://example.com")
browser_configuration: Configure browser settings like headless mode, viewport, and JavaScript | browser setup, chrome options | BrowserConfig(headless=True, viewport_width=1920, viewport_height=1080)
crawler_config: Set crawling parameters including selectors, timeouts and content filters | crawl settings, extraction config | CrawlerRunConfig(css_selector="article.main", page_timeout=60000)
markdown_extraction: Get different markdown formats including raw, cited and filtered versions | content extraction, markdown output | result.markdown_v2.raw_markdown, result.markdown_v2.markdown_with_citations
structured_extraction: Extract structured data using CSS or XPath selectors into JSON | data extraction, scraping | JsonCssExtractionStrategy(schema), JsonXPathExtractionStrategy(xpath_schema)
llm_extraction: Use LLM models to extract structured data with custom schemas | AI extraction, model integration | LLMExtractionStrategy(provider="ollama/nemotron", schema=ModelSchema)
dynamic_content: Handle JavaScript-driven content using custom JS code and wait conditions | dynamic pages, JS execution | run_config.js_code="window.scrollTo(0, document.body.scrollHeight);"
media_handling: Access extracted images, videos and audio with relevance scores | media extraction, asset handling | result.media["images"], result.media["videos"]
link_extraction: Get categorized internal and external links with context | link scraping, URL extraction | result.links["internal"], result.links["external"]
authentication: Preserve login state using user data directory or storage state | login, session handling | BrowserConfig(user_data_dir="/path/to/profile")
proxy_setup: Configure proxy settings with authentication for crawling | proxy configuration, network setup | browser_config.proxy_config={"server": "http://proxy.example.com:8080"}
content_capture: Save screenshots and PDFs of crawled pages | page capture, downloads | run_config.screenshot=True, run_config.pdf=True
caching: Enable result caching to improve performance | performance optimization, caching | run_config.cache_mode = CacheMode.ENABLED
custom_hooks: Add custom logic at different stages of the crawling process | event hooks, customization | crawler.crawler_strategy.set_hook("on_page_context_created", hook_function)
containerization: Run Crawl4AI in Docker with different architectures and GPU support | docker, deployment | docker pull unclecode/crawl4ai:basic-amd64
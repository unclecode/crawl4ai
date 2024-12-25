installation: Install Crawl4AI using pip and run setup command | package installation, setup | pip install crawl4ai && crawl4ai-setup
playwright_setup: Install Chromium browser for Playwright if needed | browser installation, chromium setup | playwright install chromium
async_crawler: Create asynchronous web crawler instance with optional verbose logging | crawler initialization, async setup | AsyncWebCrawler(verbose=True)
basic_crawl: Perform basic asynchronous webpage crawl and get markdown output | single page crawl, basic usage | async with AsyncWebCrawler() as c: await c.arun(url="https://example.com")
concurrent_crawling: Crawl multiple URLs simultaneously using asyncio.gather | parallel crawling, multiple urls | asyncio.gather(*[c.arun(url=u) for u in urls])
cache_configuration: Enable or disable cache mode for crawling | caching, cache settings | cache_mode=CacheMode.ENABLED
proxy_setup: Configure proxy settings for web crawler | proxy configuration, http proxy | proxies={"http": "http://user:pass@proxy:port"}
browser_config: Set custom headers and viewport dimensions | user agent, viewport size | headers={"User-Agent": "MyUA"}, viewport={"width":1024,"height":768}
javascript_injection: Inject custom JavaScript code during crawling | js injection, custom scripts | js_code=["""(async () => {...})();"""]
json_extraction: Extract data using JSON CSS extraction strategy | css extraction, json schema | JsonCssExtractionStrategy(schema)
llm_extraction: Configure LLM-based extraction with OpenAI integration | language model extraction, AI extraction | LLMExtractionStrategy(provider="openai/gpt-4o", api_token="KEY")
troubleshooting: Common issues include Playwright errors, empty output, and SSL problems | error handling, debugging | playwright install chromium, verify_ssl=False
documentation_links: Access additional resources through GitHub repository and official documentation | resources, links | github.com/unclecode/crawl4ai, crawl4ai.com/mkdocs/
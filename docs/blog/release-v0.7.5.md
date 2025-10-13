# 🚀 Crawl4AI v0.7.5: The Docker Hooks & Security Update

*September 29, 2025 • 8 min read*

---

Today I'm releasing Crawl4AI v0.7.5—focused on extensibility and security. This update introduces the Docker Hooks System for pipeline customization, enhanced LLM integration, and important security improvements.

## 🎯 What's New at a Glance

- **Docker Hooks System**: Custom Python functions at key pipeline points with function-based API
- **Function-Based Hooks**: New `hooks_to_string()` utility with Docker client auto-conversion
- **Enhanced LLM Integration**: Custom providers with temperature control
- **HTTPS Preservation**: Secure internal link handling
- **Bug Fixes**: Resolved multiple community-reported issues
- **Improved Docker Error Handling**: Better debugging and reliability

## 🔧 Docker Hooks System: Pipeline Customization

Every scraping project needs custom logic—authentication, performance optimization, content processing. Traditional solutions require forking or complex workarounds. Docker Hooks let you inject custom Python functions at 8 key points in the crawling pipeline.

### Real Example: Authentication & Performance

```python
import requests

# Real working hooks for httpbin.org
hooks_config = {
    "on_page_context_created": """
async def hook(page, context, **kwargs):
    print("Hook: Setting up page context")
    # Block images to speed up crawling
    await context.route("**/*.{png,jpg,jpeg,gif,webp}", lambda route: route.abort())
    print("Hook: Images blocked")
    return page
""",

    "before_retrieve_html": """
async def hook(page, context, **kwargs):
    print("Hook: Before retrieving HTML")
    # Scroll to bottom to load lazy content
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(1000)
    print("Hook: Scrolled to bottom")
    return page
""",

    "before_goto": """
async def hook(page, context, url, **kwargs):
    print(f"Hook: About to navigate to {url}")
    # Add custom headers
    await page.set_extra_http_headers({
        'X-Test-Header': 'crawl4ai-hooks-test'
    })
    return page
"""
}

# Test with Docker API
payload = {
    "urls": ["https://httpbin.org/html"],
    "hooks": {
        "code": hooks_config,
        "timeout": 30
    }
}

response = requests.post("http://localhost:11235/crawl", json=payload)
result = response.json()

if result.get('success'):
    print("✅ Hooks executed successfully!")
    print(f"Content length: {len(result.get('markdown', ''))} characters")
```

**Available Hook Points:**
- `on_browser_created`: Browser setup
- `on_page_context_created`: Page context configuration
- `before_goto`: Pre-navigation setup
- `after_goto`: Post-navigation processing
- `on_user_agent_updated`: User agent changes
- `on_execution_started`: Crawl initialization
- `before_retrieve_html`: Pre-extraction processing
- `before_return_html`: Final HTML processing

### Function-Based Hooks API

Writing hooks as strings works, but lacks IDE support and type checking. v0.7.5 introduces a function-based approach with automatic conversion!

**Option 1: Using the `hooks_to_string()` Utility**

```python
from crawl4ai import hooks_to_string
import requests

# Define hooks as regular Python functions (with full IDE support!)
async def on_page_context_created(page, context, **kwargs):
    """Block images to speed up crawling"""
    await context.route("**/*.{png,jpg,jpeg,gif,webp}", lambda route: route.abort())
    await page.set_viewport_size({"width": 1920, "height": 1080})
    return page

async def before_goto(page, context, url, **kwargs):
    """Add custom headers"""
    await page.set_extra_http_headers({
        'X-Crawl4AI': 'v0.7.5',
        'X-Custom-Header': 'my-value'
    })
    return page

# Convert functions to strings
hooks_code = hooks_to_string({
    "on_page_context_created": on_page_context_created,
    "before_goto": before_goto
})

# Use with REST API
payload = {
    "urls": ["https://httpbin.org/html"],
    "hooks": {"code": hooks_code, "timeout": 30}
}
response = requests.post("http://localhost:11235/crawl", json=payload)
```

**Option 2: Docker Client with Automatic Conversion (Recommended!)**

```python
from crawl4ai.docker_client import Crawl4aiDockerClient

# Define hooks as functions (same as above)
async def on_page_context_created(page, context, **kwargs):
    await context.route("**/*.{png,jpg,jpeg,gif,webp}", lambda route: route.abort())
    return page

async def before_retrieve_html(page, context, **kwargs):
    # Scroll to load lazy content
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(1000)
    return page

# Use Docker client - conversion happens automatically!
client = Crawl4aiDockerClient(base_url="http://localhost:11235")

results = await client.crawl(
    urls=["https://httpbin.org/html"],
    hooks={
        "on_page_context_created": on_page_context_created,
        "before_retrieve_html": before_retrieve_html
    },
    hooks_timeout=30
)

if results and results.success:
    print(f"✅ Hooks executed! HTML length: {len(results.html)}")
```

**Benefits of Function-Based Hooks:**
- ✅ Full IDE support (autocomplete, syntax highlighting)
- ✅ Type checking and linting
- ✅ Easier to test and debug
- ✅ Reusable across projects
- ✅ Automatic conversion in Docker client
- ✅ No breaking changes - string hooks still work!

## 🤖 Enhanced LLM Integration

Enhanced LLM integration with custom providers, temperature control, and base URL configuration.

### Multi-Provider Support

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

# Test with different providers
async def test_llm_providers():
    # OpenAI with custom temperature
    openai_strategy = LLMExtractionStrategy(
        provider="gemini/gemini-2.5-flash-lite",
        api_token="your-api-token",
        temperature=0.7,  # New in v0.7.5
        instruction="Summarize this page in one sentence"
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            "https://example.com",
            config=CrawlerRunConfig(extraction_strategy=openai_strategy)
        )

        if result.success:
            print("✅ LLM extraction completed")
            print(result.extracted_content)

# Docker API with enhanced LLM config
llm_payload = {
    "url": "https://example.com",
    "f": "llm",
    "q": "Summarize this page in one sentence.",
    "provider": "gemini/gemini-2.5-flash-lite",
    "temperature": 0.7
}

response = requests.post("http://localhost:11235/md", json=llm_payload)
```

**New Features:**
- Custom `temperature` parameter for creativity control
- `base_url` for custom API endpoints
- Multi-provider environment variable support
- Docker API integration

## 🔒 HTTPS Preservation

**The Problem:** Modern web apps require HTTPS everywhere. When crawlers downgrade internal links from HTTPS to HTTP, authentication breaks and security warnings appear.

**Solution:** HTTPS preservation maintains secure protocols throughout crawling.

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, FilterChain, URLPatternFilter, BFSDeepCrawlStrategy

async def test_https_preservation():
    # Enable HTTPS preservation
    url_filter = URLPatternFilter(
        patterns=["^(https:\/\/)?quotes\.toscrape\.com(\/.*)?$"]
    )

    config = CrawlerRunConfig(
        exclude_external_links=True,
        preserve_https_for_internal_links=True,  # New in v0.7.5
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=2,
            max_pages=5,
            filter_chain=FilterChain([url_filter])
        )
    )

    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun(
            url="https://quotes.toscrape.com",
            config=config
        ):
            # All internal links maintain HTTPS
            internal_links = [link['href'] for link in result.links['internal']]
            https_links = [link for link in internal_links if link.startswith('https://')]

            print(f"HTTPS links preserved: {len(https_links)}/{len(internal_links)}")
            for link in https_links[:3]:
                print(f"  → {link}")
```

## 🛠️ Bug Fixes and Improvements

### Major Fixes
- **URL Processing**: Fixed '+' sign preservation in query parameters (#1332)
- **Proxy Configuration**: Enhanced proxy string parsing (old `proxy` parameter deprecated)
- **Docker Error Handling**: Comprehensive error messages with status codes
- **Memory Management**: Fixed leaks in long-running sessions
- **JWT Authentication**: Fixed Docker JWT validation issues (#1442)
- **Playwright Stealth**: Fixed stealth features for Playwright integration (#1481)
- **API Configuration**: Fixed config handling to prevent overriding user-provided settings (#1505)
- **Docker Filter Serialization**: Resolved JSON encoding errors in deep crawl strategy (#1419)
- **LLM Provider Support**: Fixed custom LLM provider integration for adaptive crawler (#1291)
- **Performance Issues**: Resolved backoff strategy failures and timeout handling (#989)

### Community-Reported Issues Fixed
This release addresses multiple issues reported by the community through GitHub issues and Discord discussions:
- Fixed browser configuration reference errors
- Resolved dependency conflicts with cssselect
- Improved error messaging for failed authentications
- Enhanced compatibility with various proxy configurations
- Fixed edge cases in URL normalization

### Configuration Updates
```python
# Old proxy config (deprecated)
# browser_config = BrowserConfig(proxy="http://proxy:8080")

# New enhanced proxy config
browser_config = BrowserConfig(
    proxy_config={
        "server": "http://proxy:8080",
        "username": "optional-user",
        "password": "optional-pass"
    }
)
```

## 🔄 Breaking Changes

1. **Python 3.10+ Required**: Upgrade from Python 3.9
2. **Proxy Parameter Deprecated**: Use new `proxy_config` structure
3. **New Dependency**: Added `cssselect` for better CSS handling

## 🚀 Get Started

```bash
# Install latest version
pip install crawl4ai==0.7.5

# Docker deployment
docker pull unclecode/crawl4ai:latest
docker run -p 11235:11235 unclecode/crawl4ai:latest
```

**Try the Demo:**
```bash
# Run working examples
python docs/releases_review/demo_v0.7.5.py
```

**Resources:**
- 📖 Documentation: [docs.crawl4ai.com](https://docs.crawl4ai.com)
- 🐙 GitHub: [github.com/unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)
- 💬 Discord: [discord.gg/crawl4ai](https://discord.gg/jP8KfhDhyN)
- 🐦 Twitter: [@unclecode](https://x.com/unclecode)

Happy crawling! 🕷️

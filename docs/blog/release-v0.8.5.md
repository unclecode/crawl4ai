# Crawl4AI v0.8.5: Anti-Bot, Shadow DOM & 60+ Bug Fixes

*March 2026 • 10 min read*

---

I'm releasing Crawl4AI v0.8.5—our biggest release since v0.8.0. This update brings automatic anti-bot detection with proxy escalation, Shadow DOM flattening, deep crawl cancellation, and over 60 bug fixes from both our team and the community. If you're running crawls at scale or dealing with protected sites, this one's for you.

## What's New at a Glance

- **Anti-Bot Detection & Proxy Escalation**: 3-tier detection with automatic retry, proxy chain, and fallback
- **Shadow DOM Flattening**: Extract content hidden inside shadow DOM components
- **Deep Crawl Cancellation**: Stop long crawls gracefully with `cancel()` or `should_cancel` callback
- **Config Defaults API**: Set once, apply everywhere with `set_defaults()` / `get_defaults()` / `reset_defaults()`
- **Source/Sibling Selector**: Extract data spanning sibling elements in JSON extraction schemas
- **Consent Popup Removal**: Auto-dismiss cookie banners from 40+ CMP platforms
- **Resource Filtering**: Block ads and CSS at the network level with `avoid_ads` / `avoid_css`
- **Browser Recycling**: Memory-saving mode and automatic browser restart for long sessions
- **GFM Table Compliance**: Proper `| col1 | col2 |` pipe delimiters in markdown output
- **60+ Bug Fixes**: Security patches, browser stability, extraction accuracy, and more

---

## New Features

### 1. Anti-Bot Detection, Retry & Fallback

This is the headline feature. Crawl4AI now automatically detects when a page is blocked by anti-bot protection and takes action—retrying with different proxies or falling back to an alternative fetch method.

The detection uses three tiers:
- **Tier 1**: Known vendor patterns (Cloudflare, Akamai, DataDome, PerimeterX, etc.)
- **Tier 2**: Generic block indicators on small pages
- **Tier 3**: Structural integrity checks (empty shells, script-heavy pages with no content)

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.async_configs import ProxyConfig

config = CrawlerRunConfig(
    # Try direct first, then proxy on bot detection
    proxy_config=[
        ProxyConfig.DIRECT,
        ProxyConfig(server="http://my-proxy:8080"),
    ],
    max_retries=2,
    # Optional: fallback when all proxies fail
    fallback_fetch_function=my_web_unlocker_function,
)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://protected-site.com", config=config)

    # Check what happened
    stats = result.crawl_stats
    print(f"Resolved by: {stats['resolved_by']}")  # "direct", "proxy", or "fallback_fetch"
    print(f"Proxies tried: {len(stats['proxies_used'])}")
```

The system errs on the side of caution—false positives are cheap (the fallback rescues them), but false negatives mean garbage results. After 5 iterations of real-world testing, it handles everything from Cloudflare challenges to Reddit's 180KB SPA block pages.

### 2. Shadow DOM Flattening

Web components with shadow DOM hide their content from regular DOM traversal. The new `flatten_shadow_dom` option serializes shadow DOM content into the light DOM before extraction.

```python
config = CrawlerRunConfig(flatten_shadow_dom=True)

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://some-web-component-site.com", config=config)
    # Shadow DOM content is now visible in result.html, cleaned_html, and markdown
```

The implementation patches `attachShadow` to force-open closed shadow roots, recursively resolves `<slot>` projections, and strips only shadow-scoped `<style>` tags. It also reorders the JS execution pipeline—`js_code` now runs after `wait_for` + `delay_before_return_html` so your scripts operate on the fully-hydrated page. If you need JS to run before waiting, use the new `js_code_before_wait` parameter.

### 3. Deep Crawl Cancellation

All deep crawl strategies (BFS, DFS, BestFirst) now support graceful cancellation:

```python
from crawl4ai.deep_crawling import DFSDeepCrawlStrategy

pages_found = 0

def should_stop():
    return pages_found >= 50  # Stop after finding enough pages

async def on_state(state):
    nonlocal pages_found
    pages_found = state["pages_crawled"]

strategy = DFSDeepCrawlStrategy(
    max_depth=3,
    max_pages=1000,
    should_cancel=should_stop,      # Sync or async callback
    on_state_change=on_state,
)

config = CrawlerRunConfig(deep_crawl_strategy=strategy)

async with AsyncWebCrawler() as crawler:
    results = await crawler.arun("https://example.com", config=config)
    print(f"Cancelled: {strategy.cancelled}")
```

You can also call `strategy.cancel()` directly from another thread or coroutine.

### 4. Config Defaults API

Tired of repeating the same parameters? Set defaults once and they apply to every new instance:

```python
from crawl4ai import BrowserConfig, CrawlerRunConfig

# Set organization-wide defaults
BrowserConfig.set_defaults(headless=True, text_mode=True)
CrawlerRunConfig.set_defaults(verbose=False, remove_consent_popups=True)

# All new instances inherit defaults
bc = BrowserConfig()                   # headless=True, text_mode=True
rc = CrawlerRunConfig()                # verbose=False, remove_consent_popups=True

# Explicit params always override
bc2 = BrowserConfig(text_mode=False)   # text_mode=False, headless still True

# Inspect and reset
print(BrowserConfig.get_defaults())    # {"headless": True, "text_mode": True}
BrowserConfig.reset_defaults()         # Back to normal
```

### 5. Source/Sibling Selector in JSON Extraction

Many sites split a single item's data across sibling elements (think Hacker News, where title and score are in separate `<tr>` rows). The new `"source"` field navigates to a sibling before extracting:

```python
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

schema = {
    "name": "HackerNewsItems",
    "baseSelector": "tr.athing",
    "fields": [
        {"name": "title", "selector": ".titleline > a", "type": "text"},
        {"name": "link", "selector": ".titleline > a", "type": "attribute", "attribute": "href"},
        # Navigate to the NEXT sibling <tr> to get the score
        {"name": "score", "selector": ".score", "type": "text", "source": "+ tr"},
        {"name": "author", "selector": ".hnuser", "type": "text", "source": "+ tr"},
    ]
}

strategy = JsonCssExtractionStrategy(schema=schema)
```

Works in both `JsonCssExtractionStrategy` and `JsonXPathExtractionStrategy`. Falls back gracefully when siblings don't exist.

### 6. Consent Popup Removal

A single flag auto-dismisses cookie consent banners from 40+ CMP platforms:

```python
config = CrawlerRunConfig(remove_consent_popups=True)
```

Covers OneTrust, Cookiebot, Didomi, Quantcast, Sourcepoint, Google FundingChoices, TrustArc, ConsentManager, Osano, Iubenda, Complianz, LiveRamp, CookieYes, Klaro, Termly, and many more.

### 7. Resource Filtering: avoid_ads / avoid_css

Block ad trackers and CSS resources at the network level for faster, leaner crawls:

```python
config = BrowserConfig(
    avoid_ads=True,   # Blocks doubleclick, google-analytics, etc.
    avoid_css=True,   # Blocks .css, .less, .scss resources
)
```

### 8. Browser Recycling & Memory-Saving Mode

For long-running crawl sessions:

```python
config = BrowserConfig(
    memory_saving_mode=True,          # Aggressive cache/V8 heap flags
    max_pages_before_recycle=100,     # Auto-restart browser after N pages
)
```

This prevents memory leaks during sustained crawling. The recycling uses a version-based approach that's safe under concurrent load—we fixed three separate deadlock bugs to get this right.

### 9. GFM Table Compliance

Tables in markdown output now have proper GitHub-Flavored Markdown pipe delimiters:

**Before (v0.8.0)**:
```
Name | Age | City
---|---|---
Alice | 30 | NYC
```

**After (v0.8.5)**:
```
| Name | Age | City |
| --- | --- | --- |
| Alice | 30 | NYC |
```

---

## Minor Features

- **`query_llm_config`**: Separate LLM config for adaptive crawler query expansion (#1682)
- **`force_viewport_screenshot`**: Screenshot only the viewport, not the full page
- **`device_scale_factor`**: Configurable screenshot DPI via BrowserConfig (#1463)
- **`redirected_status_code`**: Now available on CrawlResult (#1435)
- **`wait_for_images`**: Wait for images to load before taking screenshots (#1792)
- **`score_threshold`**: Filter low-quality URLs in BestFirstCrawlingStrategy (#1804)
- **`link_preview_timeout`**: Configurable timeout in AdaptiveConfig (#1793)
- **`--json-ensure-ascii`**: CLI flag for Unicode preservation in JSON output (#1668)
- **`type-list` pipeline**: Chained extraction like `["attribute", "regex"]` in JsonCssExtractionStrategy (#1290)

---

## Security Fixes

### Critical: RCE via Deserialization in Docker /crawl Endpoint

**Severity**: CRITICAL
**Affected**: Docker API deployment (v0.8.0 and earlier)

The `/crawl` endpoint's deserialization logic used `eval()` for certain object types. I removed this entirely and added an allowlist (`ALLOWED_DESERIALIZE_TYPES`) so only known config classes can be instantiated.

### Critical: Redis CVE-2025-49844 (CVSS 10.0)

**Affected**: Docker deployments using Redis

Upgraded Redis to 7.2.7 which patches the Lua use-after-free vulnerability.

### Additional Security

- **XSS prevention**: Use DOMParser instead of innerHTML in iframe processing (#1796)
- **API token enforcement**: `/token` endpoint now requires `api_token` when configured (#1795)
- **Stealth improvements**: `sec-ch-ua` synced with User-Agent, WebGL kept alive in stealth mode

---

## Bug Fixes

### Browser & Page Management

- Fix page reuse race condition when `create_isolated_context=False`
- Fix browser context memory leak — signature shrink + LRU eviction (#943)
- Fix cascading context crash from duplicate `add_init_script` (#1768)
- Fix `simulate_user` destroying page content via ArrowDown keypress
- Fix browser recycling deadlock under sustained concurrent load (#1640)
- Fix Docker monitor LOCK contention causing pod deadlock (#1754)

### Proxy & Network

- Fix proxy auth `ERR_INVALID_AUTH_CREDENTIALS` (#1281)
- Fix proxy auth for persistent browser contexts
- Fix proxy escalation not re-raising on first exception when chain has alternatives
- Fix fallback fetch: run when all proxies crash, skip re-check, never return None

### Deep Crawling

- Fix `can_process_url()` to receive normalized URL
- Fix `total_score` not calculated for links that fail head extraction
- Fix `FilterChain.add_filter` AttributeError on tuple immutability
- Fix URL Seeder forcing Common Crawl index for sitemaps (#1746)
- Fix `is_external_url` port comparison (#1783)
- Prevent AdaptiveCrawler from crawling external domains (#1805)

### Extraction & Content

- Fix `<base>` tag ignored in html2text relative link resolution (#1721)
- Fix script tag removal losing adjacent text in `cleaned_html` (#1364)
- Preserve `class` and `id` attributes in `cleaned_html` (#1782)
- Fix nested brackets/parentheses in LINK_PATTERN regex (#1790)
- Strip markdown fences in `force_json_response` path for LLM extraction
- Guard against None LLM content, propagate `finish_reason` (#1788)
- Fix `agenerate_schema()` JSON parsing for Anthropic models
- Fix `from_serializable_dict` ignoring plain data dicts with "type" key
- Fix MediaItem crash on non-numeric width values like "100%" (#1635)
- Fix BM25ContentFilter returning duplicate chunks (#1213)
- Fix `css_selector` ignored in LXML scraping for `raw://` URLs (#1484)

### CLI & Docker

- Fix deep-crawl CLI outputting only the first page (#1667)
- Fix VersionManager ignoring `CRAWL4_AI_BASE_DIRECTORY` env var (#1296)
- Fix Docker health endpoint to use dynamic version (#1686)
- Add explicit UTF-8 encoding to CLI file output (#1789)
- Handle `UnicodeEncodeError` in URL seeder, strip zero-width chars (#1784)
- Add TTL expiry for Redis task data to prevent memory growth (#1730)
- Add Windows support for crawler monitor keyboard input (#1794)
- Fix `scroll_delay` ignored in full-page screenshot scroller
- Fix MCP SSE endpoint crash — mount via raw ASGI Route (#1594)
- Fix `/llm` per-request provider override, Redis config from host/port/password (#1611, #1817)
- Fix screenshot respects `scan_full_page=False` (#1750)
- Fix screenshot distortion on Elementor sites (#1370)
- Fix deep crawl timeout and `arun_many` dispatcher bypass (#1818, #1509)

### Other

- Replace `tf-playwright-stealth` with `playwright-stealth` (#1553)
- Allow local embeddings by removing OpenAI fallback (#1658)
- Include GoogleSearchCrawler `script.js` in package distribution (#1711)
- Fix bs4 deprecation warning (`text` → `string`) (#1077)
- Run blocking `chardet.detect` in thread executor (#1751)
- Wire `mean_delay`/`max_range` from CrawlerRunConfig into dispatcher rate limiter (#1786)

---

## Tests

Added a comprehensive **291-test regression suite** covering all major subsystems: core crawl, content processing, extraction strategies, deep crawling, browser management, config serialization, utilities, and edge cases.

---

## Breaking Changes

### `cleaned_html` Now Preserves `class` and `id` Attributes

If you have downstream code that parses `cleaned_html` and assumes no class/id attributes are present, this may need updating. This change enables users to do CSS-based analysis on cleaned HTML.

### Docker: Redis Upgraded to 7.2.7

If you pin Redis versions in your deployment, update to 7.2.7 or later.

---

## Upgrade Instructions

### Python Package

```bash
pip install --upgrade crawl4ai
# or
pip install crawl4ai==0.8.5
```

### Docker

```bash
docker pull unclecode/crawl4ai:0.8.5

docker run -d -p 11235:11235 --shm-size=1g unclecode/crawl4ai:0.8.5
```

---

## Verification

Run the verification tests to confirm all features are working:

```bash
python docs/releases_review/demo_v0.8.5.py
```

This runs 13 actual tests that crawl real URLs and verify each feature end-to-end.

---

## Acknowledgments

This release includes contributions from a large number of community members. Thank you to everyone who submitted PRs, reported issues, and provided reproduction steps. Special thanks to all contributors listed in [CONTRIBUTORS.md](../CONTRIBUTORS.md).

Issues fixed: #462, #880, #943, #1031, #1077, #1183, #1213, #1251, #1281, #1290, #1296, #1308, #1354, #1364, #1370, #1374, #1424, #1435, #1463, #1484, #1487, #1489, #1494, #1503, #1509, #1512, #1520, #1553, #1594, #1601, #1606, #1611, #1622, #1635, #1640, #1658, #1666, #1667, #1668, #1671, #1682, #1686, #1711, #1715, #1716, #1721, #1730, #1731, #1746, #1750, #1751, #1754, #1758, #1762, #1768, #1770, #1776, #1782, #1783, #1784, #1786, #1788, #1789, #1790, #1792, #1793, #1794, #1795, #1796, #1797, #1801, #1803, #1804, #1805, #1815, #1817, #1818, #1824

---

## Support & Resources

- **Documentation**: [docs.crawl4ai.com](https://docs.crawl4ai.com)
- **GitHub**: [github.com/unclecode/crawl4ai](https://github.com/unclecode/crawl4ai)
- **Discord**: [discord.gg/crawl4ai](https://discord.gg/jP8KfhDhyN)
- **Twitter**: [@unclecode](https://x.com/unclecode)

---

**This is a massive release—10 new features, critical security patches, and 60+ bug fixes. Whether you're dealing with anti-bot protection, shadow DOM sites, or just want more reliable crawls at scale, v0.8.5 has you covered. Thank you for your continued support!**

**Happy crawling!**

*- unclecode*

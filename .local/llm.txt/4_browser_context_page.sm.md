# Creating Browser Instances, Contexts, and Pages (Condensed LLM Reference)

> Minimal code-focused reference retaining all outline sections.

## Introduction
- Manage browsers for crawling with identity preservation, sessions, scaling.
- Maintain cookies, local storage, human-like actions.

### Key Objectives
- **Identity Preservation**: Stealth plugins, human-like inputs.
- **Persistent Sessions**: Store cookies, continue tasks across runs.
- **Scalable Crawling**: Handle large volumes efficiently.

---

## Browser Creation Methods

### Standard Browser Creation
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig

cfg = BrowserConfig(browser_type="chromium", headless=True)
async with AsyncWebCrawler(config=cfg) as c:
    r = await c.arun("https://example.com")
```

### Persistent Contexts
```python
cfg = BrowserConfig(user_data_dir="/path/to/data")
async with AsyncWebCrawler(config=cfg) as c:
    r = await c.arun("https://example.com")
```

### Managed Browser
```python
cfg = BrowserConfig(headless=False, debug_port=9222, use_managed_browser=True)
async with AsyncWebCrawler(config=cfg) as c:
    r = await c.arun("https://example.com")
```

---

## Context and Page Management

### Creating and Configuring Browser Contexts
```python
from crawl4ai import CrawlerRunConfig
conf = CrawlerRunConfig(headers={"User-Agent": "C4AI"})
async with AsyncWebCrawler() as c:
    r = await c.arun("https://example.com", config=conf)
```

### Creating Pages
```python
conf = CrawlerRunConfig(viewport_width=1920, viewport_height=1080)
async with AsyncWebCrawler() as c:
    r = await c.arun("https://example.com", config=conf)
```

---

# Preserve Your Identity with Crawl4AI

Use Managed Browsers for authentic identity:

## Managed Browsers: Your Digital Identity Solution
- Store sessions, cookies, user profiles.
- Reuse CAPTCHAs, logins.

### Steps to Use Identity-Based Browsing
```bash
# Launch Chrome with user-data-dir
google-chrome --user-data-dir="/path/to/Profile"
# Then login manually, solve CAPTCHAs, etc.
```

```python
cfg = BrowserConfig(
    headless=True,
    use_managed_browser=True,
    user_data_dir="/path/to/Profile"
)
async with AsyncWebCrawler(config=cfg) as c:
    r = await c.arun("https://example.com")
```

### Example: Extracting Data Using Managed Browsers
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

schema = {...}
cfg = BrowserConfig(
    headless=True, use_managed_browser=True,
    user_data_dir="/path/to/data"
)
crawl_cfg = CrawlerRunConfig(extraction_strategy=JsonCssExtractionStrategy(schema))

async with AsyncWebCrawler(config=cfg) as c:
    r = await c.arun("https://example.com", config=crawl_cfg)
```

## Magic Mode: Simplified Automation
```python
async with AsyncWebCrawler() as c:
    r = await c.arun("https://example.com", magic=True)
```

---

# Session Management

Use `session_id` to maintain state across requests:

```python
from crawl4ai.async_configs import CrawlerRunConfig

async with AsyncWebCrawler() as c:
    sid = "my_session"
    conf1 = CrawlerRunConfig(url="https://example.com/page1", session_id=sid)
    conf2 = CrawlerRunConfig(url="https://example.com/page2", session_id=sid)
    r1 = await c.arun(config=conf1)
    r2 = await c.arun(config=conf2)
    await c.crawler_strategy.kill_session(sid)
```

---

# Session-Based Crawling for Dynamic Content

- Reuse the same session for multi-step actions, JS execution.
- Ideal for pagination, JS-driven content.

## Basic Concepts
- `session_id`: Keep the same ID for related crawls.
- `js_code`, `wait_for`: Run JS, wait for elements.

## Advanced Techniques
- Execute JS for dynamic content loading.
- Wait loops or hooks to handle new elements.

---

## Conclusion

- Combine managed browsers, sessions, and configs for scalable, identity-preserved crawling.
- Adjust headers, cookies, viewports.
- Magic mode for quick attempts; Managed Browsers for robust identity.
- Use sessions for multi-step, dynamic workflows.

## Optional
- [async_crawler_strategy.py](https://github.com/unclecode/crawl4ai/blob/main/crawl4ai/async_crawler_strategy.py)
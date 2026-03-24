# Anti-Bot Detection & Fallback

When crawling sites protected by anti-bot systems (Akamai, Cloudflare, PerimeterX, DataDome, Imperva, etc.), requests often get blocked with CAPTCHAs, 403 responses, or empty pages. Crawl4AI provides a layered retry and fallback system that automatically detects blocking and escalates through multiple strategies until content is retrieved.

## How Detection Works

After each crawl attempt, Crawl4AI inspects the HTTP status code and HTML content for known anti-bot signals:

- **HTTP 403/429** with short or empty response bodies
- **Challenge pages** — Cloudflare "Just a moment", Akamai "Access Denied", PerimeterX block pages
- **CAPTCHA injection** — reCAPTCHA, hCaptcha, or vendor-specific challenges on otherwise empty pages
- **Firewall blocks** — Imperva/Incapsula resource iframes, Sucuri firewall pages, Cloudflare error codes

Detection uses structural HTML markers (specific element IDs, script sources, form actions) rather than generic keywords to minimize false positives. A normal page that happens to mention "CAPTCHA" or "Cloudflare" in its content will not be flagged.

When all attempts fail and blocking is still detected, the result is returned with `success=False` and `error_message` describing the block reason.

## Configuration Options

All anti-bot retry options live on `CrawlerRunConfig`:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `proxy_config` | `ProxyConfig`, `list[ProxyConfig]`, or `None` | `None` | Single proxy or ordered list of proxies to try. Each retry round iterates through the full list. Use `"direct"` or `ProxyConfig.DIRECT` in a list to explicitly try without a proxy. |
| `max_retries` | `int` | `0` | Number of retry rounds when blocking is detected. `0` = no retries. |
| `fallback_fetch_function` | `async (str) -> str` | `None` | Async function called as last resort. Takes URL, returns raw HTML. |

## Escalation Chain

Each retry round tries every proxy in `proxy_config` in order. If all rounds are exhausted and the page is still blocked, the fallback fetch function is called as a last resort.

```
For each round (1 + max_retries rounds):
    1. Try proxy_config[0] (or direct if proxy_config is None)
    2. If blocked → try proxy_config[1]
    3. If blocked → try proxy_config[2]
    4. ... continue through all proxies
    5. If any attempt succeeds → done

If all rounds exhausted and still blocked:
    6. Call fallback_fetch_function(url) → process returned HTML
```

Worst-case attempts before the fetch function: `(1 + max_retries) x len(proxy_config)`

## Crawl Stats

Every crawl result includes a `crawl_stats` dict with detailed attempt tracking:

```python
result.crawl_stats = {
    "attempts": 3,                    # total browser attempts made
    "retries": 1,                     # retry rounds used (0 = succeeded first round)
    "proxies_used": [                 # ordered list of every attempt
        {"proxy": None,               "status_code": 403, "blocked": True,  "reason": "Akamai block (Reference #)"},
        {"proxy": "proxy.io:8080",    "status_code": 403, "blocked": True,  "reason": "Akamai block (Reference #)"},
        {"proxy": "premium.io:9090",  "status_code": 200, "blocked": False, "reason": ""},
    ],
    "fallback_fetch_used": False,     # whether fallback_fetch_function was called
    "resolved_by": "proxy",           # "direct" | "proxy" | "fallback_fetch" | null (all failed)
}
```

## Usage Examples

### Simple Retry (No Proxy)

Retry the crawl up to 3 times when blocking is detected. Useful when blocks are intermittent or IP-based.

```python
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

async with AsyncWebCrawler(config=BrowserConfig(headless=True)) as crawler:
    result = await crawler.arun(
        url="https://example.com",
        config=CrawlerRunConfig(max_retries=3),
    )
```

### Single Proxy

Pass a single `ProxyConfig` — it's used on every attempt. Same behavior as always.

```python
from crawl4ai.async_configs import ProxyConfig

config = CrawlerRunConfig(
    max_retries=2,
    proxy_config=ProxyConfig(
        server="http://proxy.example.com:8080",
        username="user",
        password="pass",
    ),
)
```

### Direct-First, Then Proxies

Try without a proxy first, then escalate to proxies if blocked. Use `ProxyConfig.DIRECT` (or the string `"direct"`) in the list to represent a no-proxy attempt.

```python
config = CrawlerRunConfig(
    max_retries=1,
    proxy_config=[
        ProxyConfig.DIRECT,  # Try without proxy first
        ProxyConfig(
            server="http://datacenter-proxy.example.com:8080",
            username="user",
            password="pass",
        ),
        ProxyConfig(
            server="http://residential-proxy.example.com:9090",
            username="user",
            password="pass",
        ),
    ],
)
```

With this setup, each round tries direct first, then datacenter, then residential. With `max_retries=1`, worst case is 2 rounds x 3 steps = 6 attempts.

### Proxy List (Escalation)

Pass a list of proxies. They're tried in order — first one that works wins. Within each retry round, the entire list is tried again.

```python
config = CrawlerRunConfig(
    max_retries=1,
    proxy_config=[
        ProxyConfig(
            server="http://datacenter-proxy.example.com:8080",
            username="user",
            password="pass",
        ),
        ProxyConfig(
            server="http://residential-proxy.example.com:9090",
            username="user",
            password="pass",
        ),
    ],
)
```

With this setup, each round tries the datacenter proxy first, then the residential proxy. With `max_retries=1`, worst case is 2 rounds x 2 proxies = 4 attempts.

### Fallback Fetch Function

When all browser-based attempts fail, call a custom async function as a last resort. This function receives the URL and must return raw HTML as a string. The returned HTML is processed through the normal pipeline (markdown generation, extraction, etc.).

This is useful when you have access to a scraping API, a pre-fetched cache, or any other source of HTML.

```python
import aiohttp

async def my_scraping_api(url: str) -> str:
    """Fetch HTML via an external scraping API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.my-scraping-service.com/fetch",
            params={"url": url, "format": "html"},
            headers={"Authorization": "Bearer MY_TOKEN"},
        ) as resp:
            if resp.status == 200:
                return await resp.text()
            raise RuntimeError(f"API error: {resp.status}")

config = CrawlerRunConfig(
    max_retries=1,
    fallback_fetch_function=my_scraping_api,
)
```

The function can do anything — call an API, read from a database, return cached HTML, or make a simple HTTP request with a different library. Crawl4AI does not care how the HTML is obtained.

### Full Escalation (All Features Combined)

This example combines every layer: stealth mode, a list of proxies tried in order, retries, and a final fetch function.

```python
import aiohttp
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, ProxyConfig

# Last-resort: fetch HTML via an external service
async def external_fetch(url: str) -> str:
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.my-service.com/scrape",
            json={"url": url, "render_js": True},
            headers={"Authorization": "Bearer MY_TOKEN"},
        ) as resp:
            return await resp.text()

browser_config = BrowserConfig(
    headless=True,
    enable_stealth=True,
)

crawl_config = CrawlerRunConfig(
    magic=True,
    wait_until="load",
    max_retries=2,

    # Proxies tried in order — cheapest first
    proxy_config=[
        ProxyConfig(
            server="http://datacenter-proxy.example.com:8080",
            username="user",
            password="pass",
        ),
        ProxyConfig(
            server="http://residential-proxy.example.com:9090",
            username="user",
            password="pass",
        ),
    ],

    # Last resort — called after all retries and proxies are exhausted
    fallback_fetch_function=external_fetch,
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(
        url="https://protected-site.com/products",
        config=crawl_config,
    )

    if result.success:
        print(f"Got {len(result.markdown.raw_markdown)} chars of markdown")
        print(f"Resolved by: {result.crawl_stats['resolved_by']}")
        print(f"Attempts: {result.crawl_stats['attempts']}")
    else:
        print(f"All attempts failed: {result.error_message}")
```

**What happens step by step:**

| Round | Attempt | What runs |
|---|---|---|
| 1 | 1 | Datacenter proxy — blocked |
| 1 | 2 | Residential proxy — blocked |
| 2 | 1 | Datacenter proxy — blocked |
| 2 | 2 | Residential proxy — blocked |
| 3 | 1 | Datacenter proxy — blocked |
| 3 | 2 | Residential proxy — blocked |
| - | - | `external_fetch(url)` called — returns HTML |

That's up to 6 browser attempts + 1 function call before giving up.

## Tips

- **Start with `max_retries=0`** and a `fallback_fetch_function` if you just want a safety net without burning time on retries.
- **Order proxies cheapest-first** — datacenter proxies before residential, residential before premium.
- **Combine with stealth mode** — `BrowserConfig(enable_stealth=True)` and `CrawlerRunConfig(magic=True)` reduce the chance of being blocked in the first place.
- **`wait_until="load"`** is important for anti-bot sites — the default `domcontentloaded` can return before the anti-bot sensor finishes.
- **Check `crawl_stats`** to understand what happened — how many attempts, which proxy worked, whether the fallback function was needed.

## See Also

- [Proxy & Security](proxy-security.md) — Proxy setup, authentication, and rotation
- [Undetected Browser](undetected-browser.md) — Stealth mode and browser fingerprint evasion
- [Session Management](session-management.md) — Maintaining sessions across requests

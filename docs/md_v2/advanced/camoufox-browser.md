# Camoufox Runtime

## Overview

Crawl4AI now supports Camoufox as a first-class browser runtime through `BrowserConfig(browser_runtime="camoufox")`.

This keeps the normal Crawl4AI surface intact:

- `AsyncWebCrawler`
- `CrawlerRunConfig`
- extraction and markdown generation
- screenshots and waiting primitives
- session reuse
- persistent browser profiles

Camoufox support is intentionally **local-first** in v1:

- supported: dedicated local launch
- supported: persistent local context
- not yet supported in Crawl4AI: CDP/custom browser mode
- not yet supported in Crawl4AI: Camoufox remote WebSocket mode

## Installation

Install the optional Crawl4AI extra or Camoufox directly:

```bash
pip install "crawl4ai[camoufox]"
```

Or:

```bash
pip install -U camoufox[geoip]
python -m camoufox fetch
```

## Linux / VPS Notes

For Linux and VPS deployments, prefer Camoufox's virtual display mode instead of plain headless mode. Camoufox's own docs recommend installing `xvfb` and using `headless="virtual"` when you want headless execution on Linux:

```bash
sudo apt-get install xvfb
```

Then use:

```python
camoufox_options = {
    "headless": "virtual",
    "geoip": True,
    "humanize": True,
}
```

## Basic Usage

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

browser_config = BrowserConfig(
    browser_runtime="camoufox",
    browser_type="firefox",
    headless=True,
    camoufox_options={
        "geoip": True,
        "humanize": True,
    },
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(
        "https://example.com",
        config=CrawlerRunConfig(wait_for="css:body"),
    )
    print(result.success)
    print(result.markdown[:500])
```

## Persistent Context Example

```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

browser_config = BrowserConfig(
    browser_runtime="camoufox",
    browser_type="firefox",
    use_persistent_context=True,
    user_data_dir="./camoufox-profile",
    camoufox_options={
        "geoip": True,
        "humanize": True,
    },
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(
        "https://example.com/account",
        config=CrawlerRunConfig(),
    )
    print(result.success)
```

## Identity Rules

Camoufox owns browser identity at the **browser session** level.

That means:

- use `camoufox_options` for browser fingerprint and geo settings
- use `BrowserConfig.proxy_config` for the browser proxy
- do not use per-run identity overrides with `CrawlerRunConfig`

These `CrawlerRunConfig` fields are rejected in Camoufox mode:

- `proxy_config`
- `user_agent`
- `user_agent_mode`
- `locale`
- `timezone_id`
- `geolocation`
- `override_navigator`
- `magic`

In `BrowserConfig.headers`, avoid identity-bearing headers such as:

- `User-Agent`
- `Accept-Language`
- `sec-ch-ua*`

## Residential Proxies

Camoufox works best when the proxy and browser identity are configured together at browser-launch time.

If your provider exports proxies in Webshare's `host:port:username:password` format, convert one line into `BrowserConfig.proxy_config` before you create the crawler:

```python
def parse_webshare_proxy(proxy_line: str) -> dict[str, str]:
    host, port, username, password = proxy_line.strip().split(":", 3)
    return {
        "server": f"http://{host}:{port}",
        "username": username,
        "password": password,
    }
```

Then use it like this:

```python
browser_config = BrowserConfig(
    browser_runtime="camoufox",
    browser_type="firefox",
    proxy_config=parse_webshare_proxy(proxy_line),
    camoufox_options={
        "headless": "virtual",
        "geoip": True,
        "humanize": True,
    },
)
```

Pick one residential proxy per browser session. Camoufox mode rejects per-run proxy overrides because the browser fingerprint, locale, timezone, and WebRTC state should all stay aligned with the chosen exit IP.

See `docs/examples/camoufox_proxy_example.py` for a complete environment-driven example that works on local machines and Linux hosts.

## Compatibility Notes

- `browser_type` must be `"firefox"` when `browser_runtime="camoufox"`.
- `browser_mode` must stay `"dedicated"`.
- `enable_stealth=True` is not allowed with Camoufox.
- `UndetectedAdapter` is not allowed with Camoufox.
- `storage_state` is not supported together with `use_persistent_context=True`; use `user_data_dir` to reuse session state instead.
- Camoufox persistent contexts are the recommended way to reuse sessions and browser state.

## Recommended Starting Point

Use this as the first production-style config:

```python
browser_config = BrowserConfig(
    browser_runtime="camoufox",
    browser_type="firefox",
    use_persistent_context=True,
    user_data_dir="./camoufox-profile",
    proxy_config={
        "server": "http://proxy.example.com:8080",
        "username": "user",
        "password": "pass",
    },
    camoufox_options={
        "geoip": True,
        "humanize": True,
    },
)
```

## Example Files

- `docs/examples/camoufox_example.py` demonstrates dedicated and persistent Camoufox sessions.
- `docs/examples/camoufox_proxy_example.py` shows how to pair Camoufox with a residential proxy using environment variables.

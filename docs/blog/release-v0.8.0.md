# Crawl4AI v0.8.0 Release Notes

**Release Date**: January 2026
**Previous Version**: v0.7.6
**Status**: Release Candidate

---

## Highlights

- **Critical Security Fixes** for Docker API deployment
- **11 New Features** including crash recovery, prefetch mode, and proxy improvements
- **Breaking Changes** - see migration guide below

---

## Breaking Changes

### 1. Docker API: Hooks Disabled by Default

**What changed**: Hooks are now disabled by default on the Docker API.

**Why**: Security fix for Remote Code Execution (RCE) vulnerability.

**Who is affected**: Users of the Docker API who use the `hooks` parameter in `/crawl` requests.

**Migration**:
```bash
# To re-enable hooks (only if you trust all API users):
export CRAWL4AI_HOOKS_ENABLED=true
```

### 2. Docker API: file:// URLs Blocked

**What changed**: The endpoints `/execute_js`, `/screenshot`, `/pdf`, and `/html` now reject `file://` URLs.

**Why**: Security fix for Local File Inclusion (LFI) vulnerability.

**Who is affected**: Users who were reading local files via the Docker API.

**Migration**: Use the Python library directly for local file processing:
```python
# Instead of API call with file:// URL, use library:
from crawl4ai import AsyncWebCrawler
async with AsyncWebCrawler() as crawler:
    result = await crawler.arun(url="file:///path/to/file.html")
```

---

## Security Fixes

### Critical: Remote Code Execution via Hooks (CVE Pending)

**Severity**: CRITICAL (CVSS 10.0)
**Affected**: Docker API deployment (all versions before v0.8.0)
**Vector**: `POST /crawl` with malicious `hooks` parameter

**Details**: The `__import__` builtin was available in hook code, allowing attackers to import `os`, `subprocess`, etc. and execute arbitrary commands.

**Fix**:
1. Removed `__import__` from allowed builtins
2. Hooks disabled by default (`CRAWL4AI_HOOKS_ENABLED=false`)

### High: Local File Inclusion via file:// URLs (CVE Pending)

**Severity**: HIGH (CVSS 8.6)
**Affected**: Docker API deployment (all versions before v0.8.0)
**Vector**: `POST /execute_js` (and other endpoints) with `file:///etc/passwd`

**Details**: API endpoints accepted `file://` URLs, allowing attackers to read arbitrary files from the server.

**Fix**: URL scheme validation now only allows `http://`, `https://`, and `raw:` URLs.

### Credits

Discovered by **Neo by ProjectDiscovery** ([projectdiscovery.io](https://projectdiscovery.io)) - December 2025

---

## New Features

### 1. init_scripts Support for BrowserConfig

Pre-page-load JavaScript injection for stealth evasions.

```python
config = BrowserConfig(
    init_scripts=[
        "Object.defineProperty(navigator, 'webdriver', {get: () => false})"
    ]
)
```

### 2. CDP Connection Improvements

- WebSocket URL support (`ws://`, `wss://`)
- Proper cleanup with `cdp_cleanup_on_close=True`
- Browser reuse across multiple connections

### 3. Crash Recovery for Deep Crawl Strategies

All deep crawl strategies (BFS, DFS, Best-First) now support crash recovery:

```python
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy

strategy = BFSDeepCrawlStrategy(
    max_depth=3,
    resume_state=saved_state,  # Resume from checkpoint
    on_state_change=save_callback  # Persist state in real-time
)
```

### 4. PDF and MHTML for raw:/file:// URLs

Generate PDFs and MHTML from cached HTML content.

### 5. Screenshots for raw:/file:// URLs

Render cached HTML and capture screenshots.

### 6. base_url Parameter for CrawlerRunConfig

Proper URL resolution for raw: HTML processing:

```python
config = CrawlerRunConfig(base_url='https://example.com')
result = await crawler.arun(url='raw:{html}', config=config)
```

### 7. Prefetch Mode for Two-Phase Deep Crawling

Fast link extraction without full page processing:

```python
config = CrawlerRunConfig(prefetch=True)
```

### 8. Proxy Rotation and Configuration

Enhanced proxy rotation with sticky sessions support.

### 9. Proxy Support for HTTP Strategy

Non-browser crawler now supports proxies.

### 10. Browser Pipeline for raw:/file:// URLs

New `process_in_browser` parameter for browser operations on local content:

```python
config = CrawlerRunConfig(
    process_in_browser=True,  # Force browser processing
    screenshot=True
)
result = await crawler.arun(url='raw:<html>...</html>', config=config)
```

### 11. Smart TTL Cache for Sitemap URL Seeder

Intelligent cache invalidation for sitemaps:

```python
config = SeedingConfig(
    cache_ttl_hours=24,
    validate_sitemap_lastmod=True
)
```

---

## Bug Fixes

### raw: URL Parsing Truncates at # Character

**Problem**: CSS color codes like `#eee` were being truncated.

**Before**: `raw:body{background:#eee}` → `body{background:`
**After**: `raw:body{background:#eee}` → `body{background:#eee}`

### Caching System Improvements

Various fixes to cache validation and persistence.

---

## Documentation Updates

- Multi-sample schema generation documentation
- URL seeder smart TTL cache parameters
- Security documentation (SECURITY.md)

---

## Upgrade Guide

### From v0.7.x to v0.8.0

1. **Update the package**:
   ```bash
   pip install --upgrade crawl4ai
   ```

2. **Docker API users**:
   - Hooks are now disabled by default
   - If you need hooks: `export CRAWL4AI_HOOKS_ENABLED=true`
   - `file://` URLs no longer work on API (use library directly)

3. **Review security settings**:
   ```yaml
   # config.yml - recommended for production
   security:
     enabled: true
     jwt_enabled: true
   ```

4. **Test your integration** before deploying to production

### Breaking Change Checklist

- [ ] Check if you use `hooks` parameter in API calls
- [ ] Check if you use `file://` URLs via the API
- [ ] Update environment variables if needed
- [ ] Review security configuration

---

## Full Changelog

See [CHANGELOG.md](../CHANGELOG.md) for complete version history.

---

## Contributors

Thanks to all contributors who made this release possible.

Special thanks to **Neo by ProjectDiscovery** for responsible security disclosure.

---

*For questions or issues, please open a [GitHub Issue](https://github.com/unclecode/crawl4ai/issues).*

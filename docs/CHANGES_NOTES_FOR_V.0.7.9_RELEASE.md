# Crawl4AI Release Notes v0.7.9

**Period**: December 13, 2025 - January 12, 2026
**Total Commits**: 18
**Status**: DRAFT - Pending review

---

## Breaking Changes ⚠️

### 1. Docker API Hooks Disabled by Default
- **Commit**: `f24396c` (Jan 12, 2026)
- **Reason**: Security fix for RCE vulnerability
- **Impact**: Hooks no longer work unless `CRAWL4AI_HOOKS_ENABLED=true` is set
- **Migration**: Set environment variable `CRAWL4AI_HOOKS_ENABLED=true` in Docker container

### 2. file:// URLs Blocked on Docker API
- **Commit**: `f24396c` (Jan 12, 2026)
- **Reason**: Security fix for LFI vulnerability
- **Impact**: Endpoints `/execute_js`, `/screenshot`, `/pdf`, `/html` reject `file://` URLs
- **Migration**: Use the library directly for local file processing

---

## Security Fixes 🔒

### Fix Critical RCE and LFI Vulnerabilities in Docker API
- **Commit**: `f24396c`
- **Date**: January 12, 2026
- **Severity**: CRITICAL
- **Files Changed**:
  - `deploy/docker/config.yml`
  - `deploy/docker/hook_manager.py`
  - `deploy/docker/server.py`
  - `deploy/docker/tests/run_security_tests.py`
  - `deploy/docker/tests/test_security_fixes.py`

**Details**:
1. **Remote Code Execution via Hooks (CVE pending)**
   - Removed `__import__` from allowed_builtins in hook_manager.py
   - Prevents arbitrary module imports (os, subprocess, etc.)
   - Hooks now disabled by default via `CRAWL4AI_HOOKS_ENABLED` env var

2. **Local File Inclusion via file:// URLs (CVE pending)**
   - Added URL scheme validation to `/execute_js`, `/screenshot`, `/pdf`, `/html`
   - Blocks `file://`, `javascript:`, `data:` and other dangerous schemes
   - Only allows `http://`, `https://`, and `raw:` (where appropriate)

3. **Security hardening**
   - Added `CRAWL4AI_HOOKS_ENABLED=false` as default (opt-in for hooks)
   - Added security warning comments in config.yml
   - Added `validate_url_scheme()` helper for consistent validation

---

## New Features ✨

### 1. init_scripts Support for BrowserConfig
- **Commit**: `d10ca38`
- **Date**: December 14, 2025
- **Files Changed**:
  - `crawl4ai/async_configs.py`
  - `crawl4ai/browser_manager.py`

**Description**: Pre-page-load JavaScript injection capability. Useful for stealth evasions (canvas/audio fingerprinting, userAgentData).

**Usage**:
```python
config = BrowserConfig(
    init_scripts=["Object.defineProperty(navigator, 'webdriver', {get: () => false})"]
)
```

---

### 2. CDP Connection Improvements
- **Commit**: `02acad1`
- **Date**: December 18, 2025
- **Files Changed**:
  - `crawl4ai/browser_manager.py`
  - `tests/browser/test_cdp_cleanup_reuse.py`

**Description**:
- Support WebSocket URLs (ws://, wss://) for CDP connections
- Proper cleanup when `cdp_cleanup_on_close=True`
- Enables reusing the same browser with multiple sequential connections

---

### 3. Crash Recovery for Deep Crawl Strategies
- **Commit**: `31ebf37`
- **Date**: December 22, 2025
- **Files Changed**:
  - `crawl4ai/deep_crawling/bff_strategy.py`
  - `crawl4ai/deep_crawling/bfs_strategy.py`
  - `crawl4ai/deep_crawling/dfs_strategy.py`
  - `tests/deep_crawling/test_deep_crawl_resume.py`
  - `tests/deep_crawling/test_deep_crawl_resume_integration.py`

**Description**: Optional `resume_state` and `on_state_change` parameters for all deep crawl strategies (BFS, DFS, Best-First) enabling cloud deployment crash recovery.

**Features**:
- `resume_state`: Pass saved state to resume from checkpoint
- `on_state_change`: Async callback fired after each URL for real-time state persistence
- `export_state()`: Get last captured state manually
- Zero overhead when features are disabled (None defaults)
- State is JSON-serializable

---

### 4. PDF and MHTML Support for raw:/file:// URLs
- **Commit**: `67e03d6`
- **Date**: December 22, 2025
- **Files Changed**:
  - `crawl4ai/async_crawler_strategy.py`

**Description**: Generate PDFs and MHTML from cached HTML content. Replaced `_generate_screenshot_from_html` with unified `_generate_media_from_html` method.

---

### 5. Screenshots for raw:/file:// URLs
- **Commit**: `444cb14`
- **Date**: December 22, 2025
- **Files Changed**:
  - `crawl4ai/async_crawler_strategy.py`

**Description**: Enables cached HTML to be rendered with screenshots. Loads HTML into browser via `page.set_content()` and takes screenshot.

---

### 6. base_url Parameter for CrawlerRunConfig
- **Commit**: `3937efc`
- **Date**: December 24, 2025
- **Files Changed**:
  - `crawl4ai/async_configs.py`
  - `crawl4ai/async_webcrawler.py`

**Description**: When processing raw: HTML (e.g., from cache), provides proper URL resolution context for markdown link generation.

**Usage**:
```python
config = CrawlerRunConfig(base_url='https://example.com')
result = await crawler.arun(url='raw:{html}', config=config)
```

---

### 7. Prefetch Mode for Two-Phase Deep Crawling
- **Commit**: `fde4e9f`
- **Date**: December 25, 2025
- **Files Changed**:
  - `crawl4ai/async_configs.py`
  - `crawl4ai/async_webcrawler.py`
  - `crawl4ai/utils.py`
  - `tests/test_prefetch_integration.py`
  - `tests/test_prefetch_mode.py`
  - `tests/test_prefetch_regression.py`

**Description**:
- Added `prefetch` parameter to CrawlerRunConfig
- Added `quick_extract_links()` function for fast link extraction
- Short-circuit in `aprocess_html()` for prefetch mode
- 42 tests added (unit, integration, regression)

---

### 8. Proxy Rotation and Configuration Updates
- **Commit**: `9e7f5aa`
- **Date**: December 26, 2025
- **Files Changed**:
  - `crawl4ai/async_configs.py`
  - `crawl4ai/async_webcrawler.py`
  - `crawl4ai/proxy_strategy.py`
  - `tests/proxy/test_sticky_sessions.py`

**Description**: Enhanced proxy rotation and proxy configuration options.

---

### 9. Proxy Support for HTTP Crawler Strategy
- **Commit**: `a43256b`
- **Date**: December 26, 2025
- **Files Changed**:
  - `crawl4ai/async_crawler_strategy.py`

**Description**: Added proxy support to the HTTP (non-browser) crawler strategy.

---

### 10. Browser Pipeline Support for raw:/file:// URLs
- **Commit**: `2550f3d`
- **Date**: December 27, 2025
- **Files Changed**:
  - `crawl4ai/async_configs.py`
  - `crawl4ai/async_crawler_strategy.py`
  - `crawl4ai/browser_manager.py`
  - `tests/test_raw_html_browser.py`
  - `tests/test_raw_html_edge_cases.py`

**Description**:
- Added `process_in_browser` parameter to CrawlerRunConfig
- Routes raw:/file:// URLs through browser when browser operations needed
- Uses `page.set_content()` instead of `goto()` for local content
- Auto-detects browser requirements: js_code, wait_for, screenshot, etc.
- Maintains fast path for raw:/file:// without browser params

**Fixes**: #310

---

### 11. Smart TTL Cache for Sitemap URL Seeder
- **Commit**: `3d78001`
- **Date**: December 30, 2025
- **Files Changed**:
  - `crawl4ai/async_configs.py`
  - `crawl4ai/async_url_seeder.py`

**Description**:
- Added `cache_ttl_hours` and `validate_sitemap_lastmod` params to SeedingConfig
- New JSON cache format with metadata (version, created_at, lastmod, url_count)
- Cache validation by TTL expiry and sitemap lastmod comparison
- Auto-migration from old .jsonl to new .json format
- Fixes bug where incomplete cache was used indefinitely

---

## Bug Fixes 🐛

### 1. HTTP Strategy raw: URL Parsing Truncates at # Character
- **Commit**: `624e341`
- **Date**: December 24, 2025
- **Files Changed**:
  - `crawl4ai/async_crawler_strategy.py`

**Problem**: `urlparse()` treated `#` as URL fragment delimiter, breaking CSS color codes like `#eee`.

**Before**: `raw:body{background:#eee}` → parsed to `body{background:`
**After**: `raw:body{background:#eee}` → parsed to `body{background:#eee}`

**Fix**: Strip `raw:` prefix directly instead of using urlparse.

---

### 2. Caching Debugging and Fixes
- **Commit**: `48426f7`
- **Date**: December 21, 2025
- **Files Changed**:
  - `crawl4ai/async_configs.py`
  - `crawl4ai/async_database.py`
  - `crawl4ai/async_webcrawler.py`
  - `crawl4ai/cache_validator.py`
  - `crawl4ai/models.py`
  - `crawl4ai/utils.py`
  - `tests/cache_validation/` (multiple test files)

**Description**: Various debugging and improvements to the caching system.

---

## Documentation Updates 📚

### 1. Multi-Sample Schema Generation Section
- **Commit**: `6b2dca7`
- **Date**: January 4, 2026
- **Files Changed**:
  - `docs/md_v2/extraction/no-llm-strategies.md`

**Description**: Added documentation explaining how to pass multiple HTML samples to `generate_schema()` for stable selectors that work across pages with varying DOM structures.

---

### 2. URL Seeder Docs - Smart TTL Cache Parameters
- **Commit**: `db61ab8`
- **Date**: December 30, 2025
- **Files Changed**:
  - `docs/md_v2/core/url-seeding.md`

**Description**:
- Added `cache_ttl_hours` and `validate_sitemap_lastmod` to parameter table
- Documented smart TTL cache validation with examples
- Added cache-related troubleshooting entries

---

## Other Changes 🔧

| Date | Commit | Description |
|------|--------|-------------|
| Dec 30, 2025 | `0d3f9e6` | Add MEMORY.md to gitignore |
| Dec 21, 2025 | `f6b29a8` | Update gitignore |

---

## Files Changed Summary

### Core Library
- `crawl4ai/async_configs.py` - Multiple changes (init_scripts, base_url, prefetch, proxy, process_in_browser, cache TTL)
- `crawl4ai/async_webcrawler.py` - Prefetch mode, base_url, proxy
- `crawl4ai/async_crawler_strategy.py` - Media generation, proxy, raw URL fixes
- `crawl4ai/browser_manager.py` - init_scripts, CDP cleanup, cookie handling
- `crawl4ai/async_url_seeder.py` - Smart TTL cache
- `crawl4ai/proxy_strategy.py` - Proxy rotation
- `crawl4ai/deep_crawling/*.py` - Crash recovery for all strategies
- `crawl4ai/utils.py` - quick_extract_links, cache fixes

### Docker Deployment
- `deploy/docker/server.py` - Security fixes
- `deploy/docker/hook_manager.py` - RCE fix
- `deploy/docker/config.yml` - Security warnings

### Documentation
- `docs/md_v2/extraction/no-llm-strategies.md` - Schema generation
- `docs/md_v2/core/url-seeding.md` - Cache parameters

### Tests Added
- `tests/test_prefetch_*.py` - 42 prefetch tests
- `tests/test_raw_html_*.py` - Raw HTML browser tests
- `tests/deep_crawling/test_deep_crawl_resume*.py` - Resume tests
- `tests/browser/test_cdp_cleanup_reuse.py` - CDP tests
- `tests/proxy/test_sticky_sessions.py` - Proxy tests
- `tests/cache_validation/*.py` - Cache tests
- `deploy/docker/tests/test_security_fixes.py` - Security tests
- `deploy/docker/tests/run_security_tests.py` - Security integration tests

---

## Questions for Main Developer

1. [ ] Are there any other breaking changes not captured here?
2. [ ] Should the security fixes get their own patch release?
3. [ ] Any features that need additional documentation?

---

*Generated: January 12, 2026*

# Crawl4AI v0.9.1: Bug Fixes & PruningContentFilter Whitelist

*July 2026 - 3 min read*

---

I'm releasing Crawl4AI v0.9.1, a patch release that ships 12 bug fixes across Docker, browser, core, and extraction, plus one new feature for `PruningContentFilter`.

No breaking changes. If you're on v0.9.0, upgrade freely.

## What's new at a glance

- **PruningContentFilter whitelist**: New `preserve_classes` / `preserve_tags` parameters to protect specific elements from density-based pruning
- **Windows browser fix**: Default `channel='chromium'` no longer crashes Playwright on Windows
- **Docker hardening**: 6 fixes for auth gate, supervisord, redis, tmpfs, and FastAPI compatibility
- **HTTP timeout fix**: `page_timeout` was passed in milliseconds to aiohttp (which expects seconds), effectively disabling timeouts in HTTP mode
- **Dependency**: lxml ceiling widened to allow 6.x

## PruningContentFilter whitelist

PruningContentFilter's density-based scoring is great at stripping boilerplate, but it sometimes takes short metadata elements — author names, timestamps, attribution lines — along with it. The new `preserve_classes` and `preserve_tags` parameters let you whitelist specific CSS classes or HTML tags that should never be pruned, regardless of their density score.

```python
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

filter = PruningContentFilter(
    threshold=0.48,
    preserve_classes=["author", "byline", "dateline"],
    preserve_tags=["time", "address"],
)
generator = DefaultMarkdownGenerator(content_filter=filter)

config = CrawlerRunConfig(markdown_generator=generator)
```

Whitelisted nodes skip scoring entirely. Default is empty sets — no behavior change for existing users. (#1900, thanks @hafezparast)

## Bug fixes

### Docker (6 fixes)

- **Auth gate UI**: Dashboard and playground now load when JWT auth is active. Token input bar added to both UIs; all fetch calls use `authFetch()` with Bearer token. API routes remain fail-closed. (#2037)
- **Supervisord/Redis dirs**: Pidfile and RDB snapshot dirs moved to writable paths for read-only rootfs deployments. (#2047, thanks @TobiasWallura-xitaso)
- **tmpfs writable**: Read-only tmpfs mounts made writable. (#2027, thanks @nightcityblade)
- **FastAPI cap**: Pinned FastAPI below 0.137 to avoid compatibility breakage. (#2025, thanks @nightcityblade)
- **Redis auth**: Rate-limit Redis storage now authenticates with the configured password. (#2040, thanks @harshmathurx)
- **Posture tests updated**: Dashboard/playground moved to public UI assertions to match auth gate fix.

### Browser (2 fixes)

- **Windows channel crash**: `channel='chromium'` (the default) caused Playwright to look for a system Chrome install instead of the bundled binary, crashing on Windows with `TargetClosedError`. The default channel is no longer passed to Playwright. (#2051, thanks @fstark96)
- **Context snapshot leak**: Browser contexts from snapshot are now properly closed. (#1999, thanks @nightcityblade)

### Core (2 fixes)

- **HTTP timeout**: `page_timeout` (60000ms) was passed directly to `aiohttp.ClientTimeout` which expects seconds, making the effective timeout 16.7 hours. Now correctly divided by 1000. (#1894, thanks @hafezparast)
- **Best-first ordering**: Batch ordering in `BestFirstCrawlingStrategy` stabilized for deterministic crawl order. (#1998, thanks @nightcityblade)

### Extraction (1 fix)

- **Table attributes**: `html2text` now preserves all attributes on table tags when `bypass_tables` is enabled. (#2007)

### Dependencies (1 fix)

- **lxml 6.x**: Widened lxml ceiling from `<6` to `<7` so crawl4ai can co-install with packages requiring lxml 6.x (e.g. scrapling). (#2019)

### Housekeeping

- Removed dead `normalize_url` duplicates and accidental `adaptive_crawler` copy. (thanks @RajanChavada)
- Sponsor logos hosted locally to fix broken GitHub rendering.

## Upgrade

```bash
pip install -U crawl4ai
crawl4ai-doctor  # verify installation
```

Docker users: pull the latest image once the Docker release workflow finishes.

## Acknowledgments

Thanks to the community contributors who made this release possible: @hafezparast (#1894, #1900), @nightcityblade (#1998, #1999, #2025, #2027), @fstark96 (#2051), @TobiasWallura-xitaso (#2047), @harshmathurx (#2040), @RajanChavada (#2042).

## Support & Resources

- [Documentation](https://docs.crawl4ai.com)
- [GitHub Issues](https://github.com/unclecode/crawl4ai/issues)
- [Discord Community](https://discord.gg/crawl4ai)

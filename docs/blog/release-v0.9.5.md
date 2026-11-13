# Crawl4AI v0.9.5: Security Release and Opt-in Deep Crawling on Docker

*October 2026 - 4 min read*

---

I'm releasing Crawl4AI v0.9.5. It closes six coordinated-disclosure advisories, adds opt-in deep crawling to the Docker server, and ships the bug fixes that landed on `develop` since 0.9.4.

All six advisories are in the same place: what the Docker server lets an untrusted request body do. Since 0.9.0 the server refuses `js_code`, refuses dangerous config types, and sends every fetch through one pinning egress proxy. This release closes the gaps where an allowed field still reached one of those sinks: one more HTTP client outside the proxy, two fields that reached page JavaScript, a model name, caller-supplied regexes, delay fields with no ceiling, and a Chromium flag that turned TLS verification off.

If you self-host the Docker server, upgrade.

## What's new at a glance

- **SSRF via the cache freshness check**: `check_cache_freshness` sent requests outside the egress proxy
- **Page JavaScript injection**: `css_selector` and `wait_for` could run script in the crawl page
- **Caller-chosen model**: `CosineStrategy.model_name` let a client pick the HuggingFace weights the server loads
- **ReDoS**: one bad regex could freeze the whole server
- **Unbounded delays**: one request could hold a browser page for as long as it liked
- **TLS off in Chromium**: `--ignore-certificate-errors` was in the default launch flags
- **Opt-in deep crawling on Docker**: `CRAWL4AI_ALLOW_DEEP_CRAWL=true`
- **Bug fixes**: deep crawl budgets, `<noscript>` pages, proxies with special characters, the CLI, and the Docker server

## Security fixes

### Blind SSRF via the cache freshness check

**GHSA-w4xc-px5p-c32w, CWE-918, medium.** Credit: [arpe1618](https://github.com/arpe1618).

`check_cache_freshness` is allowed in an untrusted body. `CacheValidator` built its own `httpx` client without the egress proxy, so a client could make the server send HEAD and GET requests to internal addresses, directly or through a redirect. This is the same root cause as the robots.txt and seeder fixes in 0.9.4: one more library HTTP client without `proxy=proxy_url()`. It now uses the proxy. A plain library caller sees no change.

### Page JavaScript injection via css_selector and wait_for

**GHSA-qj46-wp7m-rgj8, CWE-95, medium.** Credit: Zhixi "Jace" Sun ([manus-use](https://github.com/manus-use)).

Untrusted bodies may not send `js_code`. But two allowed fields reached the same `page.evaluate()` sink:

1. `_crawl_web` pasted each `css_selector` part into a JavaScript string. A `"` ended the string, and the rest ran as script.
2. `smart_wait` runs a `wait_for` as JavaScript when it starts with `js:`, looks like a function, or is not a valid selector.

`css_selector` is now passed to the page as an argument, which also makes selectors with quotes such as `p[title="x"]` work. For untrusted bodies, JavaScript `wait_for` values are refused, and a bare value is always treated as a CSS selector.

### Caller-chosen HuggingFace model in CosineStrategy

**GHSA-f856-7xp9-w3cc, CWE-502, high.** Credit: Zhixi "Jace" Sun ([manus-use](https://github.com/manus-use)).

`CosineStrategy` is allowed in an untrusted body, and its `model_name` was not filtered. The server passed it to `from_pretrained()`, so a client chose which repository the server downloaded and loaded. With PyTorch older than 2.6, a crafted pickle weight file runs code in the server process. With current PyTorch the code does not run, but the client still controls what the server downloads and keeps in memory.

`model_name` is now refused from untrusted bodies. The default image does not install PyTorch or transformers and is not affected.

### ReDoS via caller-supplied regexes

**GHSA-j843-8p47-rhxp, CWE-1333, medium.** Credit: Zhixi "Jace" Sun ([manus-use](https://github.com/manus-use)).

`RegexExtractionStrategy.custom`, `RegexChunking.patterns`, and `"type": "regex"` fields in extraction schemas took a pattern from the caller. Python's `re` holds the GIL while it matches, so one catastrophic-backtracking pattern froze the whole server, and the crawl deadline could not interrupt it. These fields are now refused from untrusted bodies. The built-in patterns stay available.

### Unbounded delay fields

**GHSA-rhjm-7hj7-75fx, CWE-770, medium.** Credit: Chunyi Liu ([liuchunyi-buaa](https://github.com/liuchunyi-buaa)).

`delay_before_return_html`, `mean_delay`, and `max_range` are allowed in untrusted bodies, but had no ceiling. One request could hold a browser page open, or stall the `arun_many` rate limiter, for as long as it liked. They are now capped at 60 seconds. Negative, NaN, and non-numeric values fall back to the field default.

### Chromium launched with certificate checks off

**GHSA-j2qh-f73r-mg3q, CWE-295, medium.** Credit: Julian Godfrey.

Both default Chromium launch flag lists carried `--ignore-certificate-errors`. That flag turns TLS verification off for the whole browser, so `ignore_https_errors=False`, and the Docker server's TLS-on default, had no effect.

The flag is gone. Insecure mode now comes only from `ignore_https_errors`. Only the CDP-managed browser, whose default context takes no such option, adds the flag, and only when `ignore_https_errors=True`.

Also in this fix: `CRAWL4AI_CHROMIUM_SANDBOX=true` now reaches every browser, including ones built from a request body.

### Hardening

These came with the reports above but did not need an advisory. Credit: Chunyi Liu ([liuchunyi-buaa](https://github.com/liuchunyi-buaa)).

- `DomainFilter` reads the real host, so `https://user@evil.com/`, `https://evil.com:443/`, and `https://evil.com./` no longer slip past `blocked_domains`.
- Webhook header names and artifact ids use `fullmatch`, so a trailing newline no longer passes.
- If the server cannot pin the browser to the egress proxy, it refuses the crawl instead of running unpinned.
- Two documentation examples are fixed: the marketplace backend uses bound SQL parameters, and the LinkedIn graph view escapes crawled data.

## Opt-in deep crawling on Docker

Since 0.9.0 the Docker server refused any request that set `deep_crawl_strategy`. Now an operator can turn it on:

```bash
docker run -e CRAWL4AI_ALLOW_DEEP_CRAWL=true -p 11235:11235 unclecode/crawl4ai:0.9.5
```

Requests may then run BFS, DFS, or BestFirst deep crawls with filters and scorers. The server keeps control: page and depth budgets come from `limits.max_pages` and `limits.max_depth` in `config.yml`, URL patterns are glob only, a strategy may hold at most 20 filters and scorers, and streamed deep crawls get a deadline. It is off by default. (#2340, issue #2308, thanks @SohamKukreti)

## Bug fixes

### Crawler and core

- **BFS overshoots `max_pages`**: BFS did not count URLs already queued for the next level, so `max_pages=50` could fetch 950 pages. (#2339, issue #2338, thanks @drakeo338)
- **Reused deep-crawl strategy**: a second run shared the first run's page budget. It now starts fresh. (#2317, issue #2309, thanks @Artechie0806)
- **Missing body on `<noscript>` pages**: content nested in an unclosed `<noscript>` was dropped from `cleaned_html` and `fit_html`. (#2284, thanks @tommypacker; #2360, #2363, issue #2293)
- **Words run together**: removing `<span> </span>` joined "Hi there" into "Hithere". A space is kept now. (#2329, issue #2328, thanks @drakeo338)
- **Failed results**: `CrawlResult.links` and `.media` have the normal shape even when the crawl failed. (#2289, issue #2286, thanks @talelboussetta)
- **PDF**: markdown is the same on every run with `batch_size > 1`. (#2320, issue #2319, thanks @Kylinny)
- **Proxy credentials**: passwords with `#`, `/`, `?`, or `%` work in the HTTP crawler, and credentials no longer appear in its error messages. (#2327, issue #2326, thanks @omarbounawarapy; #2361, thanks @alkaz-nodemaven)

### CLI

- **`-c cache_mode=...` ignored**: `crwl` always bypassed the cache. It now honors the setting. (#2366, issue #2365)
- **`-o json` crash**: without an extraction strategy, `crwl` now fails early with a clear message. (#2362, #2335, issue #2334, thanks @SohamKukreti and @ege-arhan)

### Docker server

- **`crawler_configs`**: now applies to single-URL and streaming requests too. (#2290, issue #2287, thanks @talelboussetta)
- **One bad seed**: a seed that fails the destination check is a failed result, not a 400 for the whole batch. (#2359, issue #2288)
- **Invalid `cache_mode`**: returns 400, not 500.
- **MCP over SSE**: `initialize` is processed before early tool calls, so fan-out clients no longer get -32602 on connect. (#2273, issue #2233, thanks @SohamKukreti)

## Breaking changes

None for library users.

On the Docker server, untrusted request bodies that set `CosineStrategy.model_name`, `RegexExtractionStrategy.custom`, `RegexChunking.patterns`, a `"type": "regex"` schema field, or a JavaScript `wait_for` are now refused with 400.

## Upgrade

```bash
pip install -U crawl4ai
crawl4ai-doctor  # verify installation
```

Docker users: pull the new image once the Docker release workflow finishes.

```bash
docker pull unclecode/crawl4ai:0.9.5
```

## Acknowledgments

Thank you to [arpe1618](https://github.com/arpe1618), Zhixi "Jace" Sun ([manus-use](https://github.com/manus-use)), Chunyi Liu ([liuchunyi-buaa](https://github.com/liuchunyi-buaa)), and Julian Godfrey for reporting these issues privately and giving us time to fix them before disclosure. All reporters are listed in [SECURITY-CREDITS.md](https://github.com/unclecode/crawl4ai/blob/main/SECURITY-CREDITS.md).

Thanks to the community contributors behind this release: @SohamKukreti (#2340, #2362, #2273), @drakeo338 (#2339, #2329), @talelboussetta (#2290, #2289), @tommypacker (#2284), @Kylinny (#2320), @Artechie0806 (#2317), @omarbounawarapy (#2327), @alkaz-nodemaven (#2361), and @ege-arhan (#2335).

If you find a security issue in Crawl4AI, please report it privately. See [SECURITY.md](https://github.com/unclecode/crawl4ai/blob/main/SECURITY.md).

## Support & Resources

- [Documentation](https://docs.crawl4ai.com)
- [GitHub Issues](https://github.com/unclecode/crawl4ai/issues)
- [Discord Community](https://discord.gg/crawl4ai)

# Crawl4AI v0.9.4: Security Release and 10x Faster Pruning

*September 2026 - 4 min read*

---

I'm releasing Crawl4AI v0.9.4. It closes three coordinated-disclosure advisories, makes content pruning about 10x faster, and ships the bug fixes that landed on `develop` since 0.9.3. No breaking changes.

Two of the three advisories share one root cause. The Docker server sends every attacker-influenced fetch through one egress rule: reject any destination that resolves to a non-global IP, re-check each redirect hop, and dial the pinned IP so DNS cannot rebind. The browser, the PDF downloader, and the job webhook all went through it. The robots.txt check and the URL seeder did not. They used their own HTTP clients. The third advisory is a trust-boundary bypass that let an ordinary API client read server environment variables.

If you self-host the Docker server, upgrade.

## What's new at a glance

- **SSRF via robots.txt**: `check_robots_txt` could make the server fetch internal addresses
- **SSRF via link preview**: the seeder fetched internal links and returned their `<head>` to the caller
- **Config gate bypass**: a dict wrapper let a forbidden `LLMConfig` through and leaked env vars
- **10x faster pruning**: new `PruningContentFilterLXML`, now the default
- **Bug fixes**: deep crawl, tables, robots.txt, timeouts, pooled browsers, and the Playground

## Security fixes

### Blind SSRF via the robots.txt fetch

**GHSA-f77g-77vp-r96v, CWE-918, medium.** Credit: [arpe1618](https://github.com/arpe1618).

`RobotsParser.can_fetch()` built `{scheme}://{host}/robots.txt` from the caller's URL and fetched it on a bare `aiohttp` session. No pinning, redirects followed by default, and TLS verification off. `check_robots_txt` is allowed in an untrusted request body, so any API client could choose the host. A public host whose robots.txt answers `302` to `169.254.169.254` was enough to reach cloud metadata.

The response body was not returned to the caller, so this was blind. It still gave internal request delivery, port discovery through timing, and a small boolean side channel through the robots decision.

### SSRF with response disclosure via link_preview_config

**GHSA-wh5w-hmj3-vgg7, CWE-918, high.** Credit: Ibrahim AlJaafreh ([LinkedIn](https://www.linkedin.com/in/ibrahim-aljaafreh-glitch/)), Cystack RedTeam ([cystack.ps](https://cystack.ps)).

`link_preview_config` is allowed in an untrusted body, and `LinkPreviewConfig` had no field allowlist. A client could set `include_external=True` and `include_patterns=["*"]`, point the crawl at a page it controls, and the server would fetch every link on it. That included internal and metadata addresses. The seeder then parsed each response's `<head>` and returned it in `result.links[*].head_data`. Unlike the robots issue, this one disclosed content.

### The fix for both SSRF issues

A new module, `crawl4ai/egress_policy.py`, holds one process-wide egress proxy URL for the library's own HTTP clients. The seeder and the robots.txt fetch now pass `proxy=proxy_url()`. The Docker server already runs a `PinningProxy` for Chromium, and it registers that proxy here at boot.

A proxy, not a validator hook, because a validator resolves the name, checks it, and throws the address away. The client then resolves again when it connects, and that gap is the DNS rebinding window. The proxy resolves, pins, and dials the same address, and it re-checks every redirect hop.

A plain library caller sets nothing. `proxy_url()` returns `None`, which is the default on both `httpx` and `aiohttp`, so nothing changes.

Also in this fix:

- The robots.txt fetch verifies TLS now.
- `LinkPreviewConfig` is capped for untrusted bodies: `max_links` 100, `concurrency` 10, `timeout` 10 seconds.

### Untrusted-config gate bypass via dict-wrapper laundering

**GHSA-5w5p-vcv6-mm3f, CWE-501, high.** Credit: Adam Jordan ([adamyordan](https://github.com/adamyordan)).

The Docker server limits which config types an untrusted body may build. `LLMConfig` is not on that list, because it resolves `api_token="env:NAME"` from the server environment. Two defects combined:

1. `from_serializable_dict()` unwrapped `{"type": "dict", "value": X}` by walking `X.items()`. It never checked `X` itself as a typed object, so a forbidden type inside `value` was never seen by the gate.
2. `CrawlerRunConfig.from_kwargs` and `BrowserConfig.from_kwargs` called `from_serializable_dict()` with no provenance, and the default was trusted. The laundered object was rebuilt as trusted.

The result: an ordinary, non-admin API client could read any server environment variable, including `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `SECRET_KEY`. With `SECRET_KEY` it could forge an admin JWT.

The unwrapped value is now re-checked under the untrusted gate, and `from_kwargs` carries the caller's provenance. If you run the Docker server with secrets in its environment, rotate `SECRET_KEY` and any LLM keys after you upgrade.

## Faster pruning: PruningContentFilterLXML

`PruningContentFilter` called `get_text()` and `encode_contents()` on every node while pruning. Each call walks the whole subtree, so the cost grew faster than the page. A page with 6000 cards spent about 2.2 seconds just pruning.

`PruningContentFilterLXML` computes every per-node metric (text length, inner-HTML length, link text, word count) once, in one bottom-up pass. Then it scores and prunes top-down. That is O(N).

The output is byte-identical to the old filter. The scoring, thresholds, tag weights, and bs4 quirks are reproduced 1:1, and it was checked node by node on real pages and adversarial shapes.

| Page | Before | After |
|---|---|---|
| medium | 134 ms | 13 ms |
| 200 cards | 67 ms | 7 ms |
| 6000 cards | 2200 ms | 260 ms |

It is now the default for the Docker server's fit filter and the CLI. To use it in your own code:

```python
from crawl4ai import PruningContentFilterLXML
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

md = DefaultMarkdownGenerator(content_filter=PruningContentFilterLXML(threshold=0.48))
```

`PruningContentFilter` still works, but now warns with a `DeprecationWarning`. It takes the same arguments, so the switch is a rename.

## Bug fixes

### Crawler and core

- **Deep crawl speed**: BFS re-scanned the whole level to find each result's parent, which was O(n^2) on wide pages. BestFirst enqueued the same URL twice. Both are fixed, and de-duplication keeps the shallowest depth, so no subtree is lost. (#2265, issue #2242)
- **Tables with spans**: `rowspan` and `colspan` are expanded into a real grid, and `<th>` row headers are kept instead of shifting every cell left. Spans are clamped, so one huge cell cannot hang the parse. (#2261, issue #2258)
- **robots.txt `Disallow: /*?`**: no longer blocks the whole site. (#2229, thanks @Nalhin)
- **robots.txt on Python 3.14**: the wildcard patch is skipped. 3.14 supports wildcards natively, and the patch broke `Allow:` precedence. (#2278)
- **Timeout ceiling**: `CRAWL4AI_MAX_TIMEOUT_MS` sets the ceiling for timeouts on untrusted configs. The default stays 60 seconds. A malformed or non-positive value falls back to the 60-second default, not to the ceiling. (#2212, thanks @damusix; #2266)
- **macOS arm64 crash**: Chrome for Testing no longer crashes under `--headless=new`. (#2241, issue #2239, thanks @Zsanz3)

### Docker server

- **Pooled browsers slow down**: a pooled browser context gets slower with use, and the idle janitor never fires on a busy server. `crawler.pool.max_pages_before_recycle` (default 200) now recycles a context after that many pages. (#2232, issue #2231)
- **Playground Advanced Config**: now a JSON params editor. The old Python editor sent a `code` field that the untrusted boundary rejects. (#2262, issue #2260)
- **Playground `md` and `llm` runs**: they no longer die on the `/config/dump` pre-flight. (#2224, issue #2222)
- **Permanent browser**: built with the egress-hardened default config, so its pool signature matches incoming requests. (#2237)

### Documentation and CI

- `SECURITY.md` lists 0.9.x as supported. (#2269, thanks @nightcityblade)
- The Discord stargazer notification no longer depends on a dead Google Apps Script step. (#2263, #2279)

## Breaking changes

None.

## Upgrade

```bash
pip install -U crawl4ai
crawl4ai-doctor  # verify installation
```

Docker users: pull the new image once the Docker release workflow finishes.

```bash
docker pull unclecode/crawl4ai:0.9.4
```

## Acknowledgments

Thank you to [arpe1618](https://github.com/arpe1618), Ibrahim AlJaafreh of Cystack RedTeam, and Adam Jordan ([adamyordan](https://github.com/adamyordan)) for reporting these issues privately and giving us time to fix them before disclosure. All reporters are listed in [SECURITY-CREDITS.md](https://github.com/unclecode/crawl4ai/blob/main/SECURITY-CREDITS.md).

Thanks to the community contributors behind the bug fixes in this release: @Nalhin (#2229), @damusix (#2212), @Zsanz3 (#2241), and @nightcityblade (#2269).

If you find a security issue in Crawl4AI, please report it privately. See [SECURITY.md](https://github.com/unclecode/crawl4ai/blob/main/SECURITY.md).

## Support & Resources

- [Documentation](https://docs.crawl4ai.com)
- [GitHub Issues](https://github.com/unclecode/crawl4ai/issues)
- [Discord Community](https://discord.gg/crawl4ai)

# Crawl4AI v0.9.6: Security Release

*November 2026 - 5 min read*

---

I'm releasing Crawl4AI v0.9.6. It closes eleven coordinated-disclosure advisories and ships the bug fixes that landed on `develop` since 0.9.5.

Nine advisories are in the Docker server. Two of them are about isolation: API callers shared one browser context, and declarative hooks stayed on the pooled crawler for the next caller. The rest close gaps in limits we already had: one more SSRF path, a list-form bypass of the 0.9.5 ReDoS fix, markdown options with no allowlist, a body limit that skipped chunked requests, a blocking TLS fetch, an uncapped screenshot wait, and a monitor leak.

Two reach the library too: the URL seeder followed sitemap indexes with no limits, and the dependency floors allowed a Brotli decoder with a known CVE.

If you self-host the Docker server, upgrade. If you use the library, upgrade too: the new dependency floors keep the vulnerable Brotli decoder out.

## What's new at a glance

- **Isolation on Docker**: each API caller gets its own browser context, and hooks are scoped to the request that sent them
- **SSRF via URL userinfo**: the TLS certificate fetch dialled a different host than the one checked
- **ReDoS bypass**: list-form schema `type` reached the regex step
- **Brotli CVE-2026-111497**: new floors for `brotli`, `playwright`, and `patchright`
- **Memory and DoS limits**: markdown options, chunked bodies, `screenshot_wait_for`, the TLS fetch, the monitor, and sitemap indexes
- **New default LLM**: `openai/gpt-6-luna`, before OpenAI shuts down `gpt-4o` on 14 Jan 2027
- **New options**: `dispatcher` and `batch_size` for deep crawls, `api_token` for the Docker client, `max_pdf_seconds` for PDFs
- **Bug fixes**: the Chromium channel, user agents, the cache, scraping, robots.txt, and the Docker client

## Security fixes

### Browser context shared between API callers

**GHSA-9xxj-3r64-qw54, CWE-488, medium.** Credit: [arpe1618](https://github.com/arpe1618).

The Docker pool keys browsers by browser config, and inside a browser it reused one context per run config. Neither key includes the caller. Two clients that sent the same config, including no config at all, ran in the same Chromium context, so cookies, localStorage, IndexedDB, service workers, and the HTTP cache from one crawl were present in the next. Each caller now gets its own context, and `browser_mode` is refused from untrusted bodies.

### Declarative hooks kept on the pooled crawler

**GHSA-x4gh-gvcx-p9gp, CWE-668, medium.** Credit: [TheCyberMessi](https://github.com/TheCyberMessi).

With `CRAWL4AI_HOOKS_ENABLED=true`, the hooks one client sent were set on the shared crawler and never removed. The next client on that crawler ran them too, so it could receive the `Authorization` header or session cookie an earlier client set. Hooks are now held per request.

### SSRF via URL userinfo in the TLS certificate fetch

**GHSA-qwxw-87g2-26vm, CWE-918, medium.** Credit: Zachariah Mithani ([zachariah-mithani](https://github.com/zachariah-mithani)).

The destination check reads `urlparse(url).hostname`, which drops the userinfo. The certificate fetch read the netloc and split it on the first `:`. So `https://127.0.0.1:443@public.example.com/` passed the check as `public.example.com` and the fetch connected to `127.0.0.1:443`. The fetch now dials the real host, through the egress proxy.

### ReDoS gate bypass via list-form schema type

**GHSA-8696-2734-9jqw, CWE-1333, medium.** Credit: Vijhn Austin ([VijhnAustin](https://github.com/VijhnAustin)).

The 0.9.5 fix for GHSA-j843-8p47-rhxp refused `"type": "regex"`. The schema strategies also accept a list of steps, such as `["text", "regex"]`, and run the `regex` step the same way. A list is never equal to `"regex"`, so it passed. List-form types with a `regex` step are now refused from untrusted bodies.

### Vulnerable Brotli decoder (CVE-2026-111497)

**GHSA-phmg-6873-j3gj, CWE-787, high.** Credit: Daniel Ruf ([weaverant](https://github.com/weaverant)).

CVE-2026-111497 is an out-of-bounds write in Google's Brotli decoder. Our floors allowed `brotli` 1.1.0 and 1.2.0, and Playwright and patchright drivers that bundle an affected Node.js. aiohttp decodes `br` responses with `brotli`, and the HTTP crawler asks for `br`, so the server being crawled could reach the decoder. The floors are now `brotli>=1.2.1`, `playwright>=1.64.1`, and `patchright>=1.64.2`.

### Memory exhaustion via DefaultMarkdownGenerator options

**GHSA-jfhw-vrxg-wpcw, CWE-915, medium.** Credit: Soham.

`DefaultMarkdownGenerator.options` reached `HTML2Text.update_params()`, which sets every key as an attribute, internal state included. `{"blockquote": 1000000000}` turned a tiny page into gigabytes of output. Untrusted bodies may now set only known boolean options and `body_width`, capped at 10,000.

### Unbounded sitemap index following

**GHSA-8x85-mx8f-wj4v, CWE-674, medium.** Credit: Ugur Celik ([ucsurf](https://github.com/ucsurf)).

`AsyncUrlSeeder` and `DomainMapper` followed every `<sitemap><loc>` in an index with no visited set, no depth limit, and no size limit. An index that lists itself never ended, and a small gzip file could inflate to hundreds of megabytes. Each sitemap is now fetched once, nesting stops at 5 levels, a run fetches at most 10,000 sitemaps, and each sitemap is capped at 50 MB raw and inflated. The Docker server does not expose the seeder.

### Request-size limit skipped chunked bodies

**GHSA-3q59-v69g-m9vc, CWE-770, medium.** Credit: [TheCyberMessi](https://github.com/TheCyberMessi).

The body limit read only `Content-Length`. A chunked request has no such header, so the whole body reached the endpoint. The server now counts the bytes it receives and returns 413 past `limits.max_body_bytes`.

### TLS certificate fetch blocked the event loop

**GHSA-363x-fqh9-cvp2, CWE-400, medium.** Credit: [TheCyberMessi](https://github.com/TheCyberMessi).

With `fetch_ssl_certificate`, the crawler ran a blocking connect and TLS handshake on the event loop. The Docker server runs one worker, so a host that never answers froze every request and health check for about 10 seconds. The fetch now runs in a thread.

### Uncapped screenshot_wait_for

**GHSA-7628-8pmq-4xhq, CWE-770, medium.** Credit: [TheCyberMessi](https://github.com/TheCyberMessi).

The 0.9.5 delay caps did not cover `screenshot_wait_for`, and `POST /screenshot` built its config without the untrusted clamps. Forty requests, the default number of page permits, could hold every browser page. It is now capped at 60 seconds, and `/screenshot` uses the untrusted loader.

### Rejected requests stayed in the monitor

**GHSA-2prc-jrcf-ccrm, CWE-401, low.** Credit: [TheCyberMessi](https://github.com/TheCyberMessi).

A `/crawl` request that ended with an HTTP error or a timeout was never removed from the active-request monitor, so its memory and `/monitor/requests` grew without limit. Records now end on every exit, and monitor reads need an admin token.

### Hardening

Credit: Siyang Wu ([LeoWSY-hashblue](https://github.com/LeoWSY-hashblue)).

- PDF `batch_size` and `max_redirects` in untrusted bodies are clamped to their class defaults, 4 and 5.

## New default LLM provider

OpenAI shuts down `gpt-4o` and `gpt-4o-mini` on 14 Jan 2027. After that, LLM extraction with the defaults would fail. The default provider is now `openai/gpt-6-luna`, and the CLI, `LLMTableExtraction`, the adaptive crawler, and the Docker config use it too. The shut-down `o1` and `o3-mini` entries are removed.

`gpt-6-luna` accepts only the default temperature, so LLM calls no longer send `temperature=0.01`. If you use another model and want the old, steadier output, pass `extra_args={"temperature": 0.01}`. (#2585, issue #2584)

## New options

- **Deep crawl dispatcher**: `BFSDeepCrawlStrategy` and `BestFirstCrawlingStrategy` take a `dispatcher`, and `BestFirstCrawlingStrategy` takes a `batch_size` (default 10). (#2246, thanks @yashikam19)
- **Docker client token**: `Crawl4aiDockerClient(api_token="...")` sends the bearer token on every request. (#2475, issue #2474, thanks @SohamKukreti)
- **PDF time budget**: `max_pdf_seconds` (default 300) stops a slow download or parse. (#2461, issue #2460, thanks @prassu017)

## Bug fixes

### Crawler and core

- **HTTPS-only sites failed headless**: since 0.9.1 the default `chromium` channel was dropped, so Playwright started chrome-headless-shell. It is passed again, with one retry without it if it cannot launch. (#2448, issue #2382)
- **User agents**: the default is a current Chrome string, an empty `sec-ch-ua` is never sent, and `generate(browser_type=...)` honors the type. (#2558, issue #2493; #2576, issue #2566; #2473, thanks @SohamKukreti)
- **Cache**: failed crawls and results with a markdown or LLM error are not cached, so a good copy is kept and the next run retries. (#2519, issue #2490; #2523, thanks @GoldArowana; #2559, issue #2520)
- **Missing text**: text after a removed element is kept, and `PruningContentFilter` keeps inline tags inside a kept sentence. (#2532, issue #2416; #2489, issue #2417)
- **`clone()`**: `CrawlerRunConfig.clone()` keeps `fallback_fetch_function`, `base_url`, and `force_viewport_screenshot`. (#2385, thanks @Parsiffall1; #2447, issue #2379)
- **Deep crawl**: breaking out of a streamed deep crawl early no longer breaks the next one. (#2386, issue #2380, thanks @PiUnknown)
- **URLs**: a relative `<base href>` is resolved against the page URL, `ContentTypeFilter` ignores query strings, and `normalize_url` keeps the userinfo case. (#2552, #2555, #2553, thanks @HhH666-ux; #2575; #2530, thanks @Steve-20-ai)
- **robots.txt**: `$` end anchors work below Python 3.14, and `%24` and `%2A` stay literal. (#2545, #2578, thanks @adityajai119)
- **Sitemaps**: gzipped sitemaps are detected by content, not by URL. (#2542, thanks @adityajai119)
- **PDF**: URI links and saved image paths are kept. (#2375, thanks @Hugo-DDT; #2470, thanks @michaelkillgta)

### Docker client and server

- **Docker client**: sends 0.9 declarative hooks, returns real PDF bytes, keeps a `base_url` subpath, and keeps its own timeout. (#2485, thanks @SohamKukreti; #2580, thanks @adityajai119)
- **Dead pooled browsers**: a browser whose process died is replaced instead of handed out again. (#2429, issue #842, thanks @eastwood-c and @greerso)

### Setup

- `crawl4ai-setup` and `crawl4ai-doctor` exit with code 1 on failure and give the exact fix command, instead of printing "completed".

## Breaking changes

**Library:** the minimum versions are now `playwright>=1.64.1`, `patchright>=1.64.2`, and `brotli>=1.2.1`. Run `crawl4ai-setup` after you upgrade. LLM calls no longer send `temperature=0.01` by default; `extra_args={"temperature": 0.01}` restores it.

**Docker server, untrusted request bodies:** list-form schema `type` values with a `regex` step, `browser_mode`, and unknown `DefaultMarkdownGenerator` options are refused with 400. `screenshot_wait_for` is capped at 60 seconds. Chunked bodies over `limits.max_body_bytes` get 413. Monitor reads need an admin token. API callers no longer share browser cookies or storage.

## Upgrade

```bash
pip install -U crawl4ai
crawl4ai-setup   # installs the matching browser
crawl4ai-doctor  # verify installation
```

Docker users: pull the new image once the Docker release workflow finishes.

```bash
docker pull unclecode/crawl4ai:0.9.6
```

## Acknowledgments

Thank you to Zachariah Mithani ([zachariah-mithani](https://github.com/zachariah-mithani)), [arpe1618](https://github.com/arpe1618), Vijhn Austin ([VijhnAustin](https://github.com/VijhnAustin)), Daniel Ruf ([weaverant](https://github.com/weaverant)), Soham, Ugur Celik ([ucsurf](https://github.com/ucsurf)), [TheCyberMessi](https://github.com/TheCyberMessi), and Siyang Wu ([LeoWSY-hashblue](https://github.com/LeoWSY-hashblue)) for reporting these issues privately and giving us time to fix them before disclosure. All reporters are listed in [SECURITY-CREDITS.md](https://github.com/unclecode/crawl4ai/blob/main/SECURITY-CREDITS.md).

Thanks to the community contributors behind this release: @SohamKukreti (#2475, #2485, #2473, #2487, #2434, #2457), @adityajai119 (#2545, #2578, #2542, #2580), @HhH666-ux (#2552, #2553, #2555), @yashikam19 (#2246), @prassu017 (#2461), @GoldArowana (#2523), @PiUnknown (#2386), @Parsiffall1 (#2385), @Steve-20-ai (#2530), @Hugo-DDT (#2375), @michaelkillgta (#2470), and @eastwood-c and @greerso (#2429).

If you find a security issue in Crawl4AI, please report it privately. See [SECURITY.md](https://github.com/unclecode/crawl4ai/blob/main/SECURITY.md).

## Support & Resources

- [Documentation](https://docs.crawl4ai.com)
- [GitHub Issues](https://github.com/unclecode/crawl4ai/issues)
- [Discord Community](https://discord.gg/jP8KfhDhyN)

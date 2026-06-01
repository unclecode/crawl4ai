# Crawl4AI v0.8.7: Security Hardening, DomainMapper & Community Fixes

*June 2026 - 7 min read*

---

I'm releasing Crawl4AI v0.8.7, a security-hardening release. It bundles every responsibly-disclosed vulnerability we patched since v0.8.6, adds the new DomainMapper feature, and ships a batch of scraping, deep-crawl, and LLM fixes from our team and the community.

If you self-host the Docker API server, please upgrade right away. This release closes several critical issues, and two GitHub Security Advisories accompany it.

## What's New at a Glance

- **Security hardening**: critical RCE, SSRF, auth-bypass, file-write, XSS, and hardcoded-secret fixes across the Docker API
- **DomainMapper**: comprehensive domain URL discovery with subdomain and per-source timeout controls
- **arun_many config-list in the Docker API**: send per-URL configs in one request
- **Markdown fidelity fixes**: mermaid SVG text, table rowspan/colspan, trailing text, sentence order
- **Deep crawl and dispatcher fixes**: streaming ContextVar bug, semaphore wiring
- **LLM and provider fixes**: Bedrock auth, schema-first extraction, table-extraction allowlist
- **Logging and MCP fixes**: stderr by default, non-TTY width, CJK preservation

---

## Security

v0.8.7 is, first and foremost, a security release. Every issue below was reported responsibly by the community, and every reporter is credited in `SECURITY-CREDITS.md` and the published advisories.

### Remote Code Execution

- **AST sandbox escape (CVSS 9.8)**: a `gi_frame.f_back` frame-chain walk escaped the computed-field expression sandbox to reach the real `__import__`. We removed `eval()` from computed fields entirely. SDK users can still pass Python callables via the `function` key.
- **Hook sandbox escape (CVSS 9.8)**: injected module objects (`asyncio`, `json`, `re`) carried a full `__builtins__`, providing an alternate path to `__import__`. We stripped those builtins and tightened the allowlist.

### Authentication and Secrets

- **Hardcoded JWT secret (CVSS 9.8)**: the signing key defaulted to `"mysecret"`. We removed the default, reject weak or short secrets at startup, and auto-generate an ephemeral key when JWT is enabled with no key set.
- **Monitor endpoint auth bypass (CVSS 6.5)**: the `/monitor/*` routes, including destructive actions, ran without auth. They now require a token, and the WebSocket endpoint checks the token explicitly.

### SSRF

- **Webhook SSRF (CVSS 8.6)**: webhook URLs on `/crawl/job` and `/llm/job` could hit internal and cloud-metadata addresses. We added a blocklist and disabled redirect following.
- **Direct crawl-endpoint SSRF (CVSS 8.6)**: `/crawl`, `/md`, and `/llm` fetched arbitrary URLs, and IPv6-mapped IPv4 addresses such as `[::ffff:169.254.169.254]` slipped past naive checks. We added destination validation on all entry points and normalize IPv6-mapped IPv4 before the blocklist check.

### File Write, XSS, and JS Execution

- **Arbitrary file write (CVSS 9.1)**: `/screenshot` and `/pdf` honored any `output_path`. Writes are now restricted to `CRAWL4AI_OUTPUT_DIR`, and `..` traversal is rejected.
- **Stored XSS in the monitor dashboard (CVSS 6.1)**: crawled URLs were rendered via `innerHTML` without escaping. We escape on both the server and the client now.
- **Arbitrary JS execution via `/execute_js` (CVSS 8.1)**: the endpoint is disabled by default behind `CRAWL4AI_EXECUTE_JS_ENABLED`, we removed `--disable-web-security` from default browser args, and added an SSRF blocklist on the destination.

We also replaced the `eval()` in `/config/dump` with Pydantic-validated JSON input, and added type validation for `markdown_generator` in `CrawlerRunConfig`.

---

## New Features

### DomainMapper

DomainMapper discovers URLs across an entire domain in one pass, combining multiple discovery sources. It supports an `include_subdomains` flag to widen or narrow the crawl boundary, and a per-source timeout so a single slow source cannot stall the whole map. See the [Domain Mapping guide](../core/domain-mapping.md).

### arun_many config-list in the Docker API

The Docker API now accepts a list of configs aligned with the list of URLs, so you can apply a different `CrawlerRunConfig` to each URL in a single `arun_many` request (#1837).

---

## Fixes

**Markdown and scraping**

- Preserve mermaid diagram text rendered as SVG, and prevent nested code fences (#1043)
- Preserve table `rowspan` and `colspan` in cleaned HTML (#1920)
- Preserve `.tail` text when removing empty elements (#1938)
- Keep sentence order in `NlpSentenceChunking` (#1909)

**Deep crawl and dispatcher**

- Fix the deep-crawl streaming ContextVar bug by using `set(False)` instead of `reset(token)` (#1917)
- Wire `semaphore_count` into the auto-created `MemoryAdaptiveDispatcher` and default it to 10 (#1927)

**LLM and providers**

- Add Bedrock to the provider prefixes so AWS credential auth works
- Default `LLMExtractionStrategy.extraction_type` to schema
- Add `LLMTableExtraction` to the Docker deserialization allowlist

**Crawler and downloads**

- Return `success=True` for binary downloads, and skip the block check when `downloaded_files` is set
- Honor `<base href>` in prefetch `quick_extract_links` (#752)

**Logging and MCP**

- Route `AsyncLogger` output to stderr by default (#1968) and use `Console(width=200)` for non-TTY contexts
- Use `ensure_ascii=False` in the MCP bridge to preserve CJK characters (#1967)

**Browser and misc**

- `browser_adapter` now uses the `Stealth` import, fixing a stealth import mismatch (#1960)
- Correct the `arun()` return type to `CrawlResultContainer` (#1898)
- Log the real failure reason before COMPLETE, fixing a misleading success line (#1949)
- Assistant toolbar scroll fix and issue-1973 fix

---

## Upgrade

```bash
pip install -U crawl4ai
```

Docker users should pull the latest image once the Docker release workflow finishes.

## Security Credits

Thank you to the researchers who disclosed these issues responsibly: Song Binglin (q1uf3ng), by111 (August829), Jeongbean Jeon, wulonchia, secsys_codex, Velayutham Selvaraj, and IcySun. Full details are in `SECURITY-CREDITS.md`.

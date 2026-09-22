# Crawl4AI v0.9.3: Security Release

*August 2026 - 4 min read*

---

I'm releasing Crawl4AI v0.9.3, a security release that closes five coordinated-disclosure advisories. It also carries the 33 bug fixes that piled up on `develop` since 0.9.2, most of them in the Docker server. No new features, no breaking changes.

Four of the five are in the PDF path, and they share one root cause. `PDFContentScrapingStrategy` can be selected from an untrusted Docker API request body, and it downloads with `requests` rather than through the browser. Every control the server applies on the Chromium side (destination pinning, resource caps) simply did not reach it. The fifth is a DOM-based XSS in the Playground UI that could hand an operator's API token to an attacker.

If you self-host the Docker server and accept crawl requests from clients you do not fully trust, upgrade. If you use the pip library and open PDFs from sources you do not control, upgrade.

## What's fixed at a glance

- **Arbitrary file write**: an untrusted request body could choose where extracted PDF images were written
- **SSRF**: the PDF download followed redirects into internal addresses
- **Denial of service**: remote PDFs were downloaded and parsed with no size or page cap
- **XSS**: PDF text was written into `cleaned_html` without escaping
- **DOM XSS**: the Playground result viewer re-parsed crawled content as live HTML
- **33 other bug fixes**: Docker server, crawler, and PDF handling, listed further down

## Security fixes

### Arbitrary file write via PDF image-write fields

**GHSA-xpp7-j28w-2gvx, CWE-22, high.** Credit: Zhixi "Jace" Sun ([manus-use](https://github.com/manus-use)).

`PDFContentScrapingStrategy` was in the untrusted-allowed type list but had no field allowlist of its own. A request body could therefore set `save_images_locally: true` and `image_save_dir` to any path, and the server would write extracted PDF images there.

Both fields are now filtered out of untrusted bodies at the trust boundary, and `extract_images` is forced off for them. Rasterizing every page of a caller-supplied PDF is the most expensive thing this strategy can do, and nothing about untrusted crawling needs it.

### SSRF via PDF download redirects

**GHSA-q5rj-45vw-vp2g, CWE-918, high.** Credit: Nguyen Tran Thanh Lam ([c240030](https://github.com/c240030)).

The PDF download let `requests` follow redirects on its own. A public, allowed URL that returned a 302 to `169.254.169.254` or any other internal address was fetched without the destination ever being checked.

Redirects are now resolved by hand, one hop at a time, with the destination policy consulted before each hop is fetched and a cap of five hops. The peer IP of the response whose body is actually read back is validated too, which closes DNS rebinding: passing the URL check only proves the *name* resolved somewhere allowed, and `requests` resolves it again when it dials.

The library ships with no egress policy of its own, because a plain library caller already chose the URL. The Docker server installs its existing `egress_broker` policy into the PDF path at boot, so that path now gets the same non-global-IP rule the browser path already had.

### Denial of service via unbounded PDF size and page count

**GHSA-v2rm-hvrj-2x9q, CWE-400, medium.** Credit: Nguyen Tran Thanh Lam ([c240030](https://github.com/c240030)).

A remote PDF was streamed to a temp file with no cap and then parsed with no page limit. One request pointing at a large or many-page PDF could exhaust disk, CPU, and bandwidth on a shared worker.

Downloads now stop at `max_pdf_bytes`, 100 MiB by default. The cap is enforced on the running byte total, not on the `content-length` header, because that header is attacker-controlled and may be absent or understated. Parsing stops at `max_pdf_pages`, 2000 by default, in both the single and batch paths. Untrusted request bodies have both caps clamped, so a client cannot raise its own limits back to unbounded.

The Docker config also ships a non-zero `limits.wall_clock_s` of 300 seconds. It was `0`, meaning no per-crawl deadline at all.

### XSS via unescaped PDF text in cleaned_html

**GHSA-7g3g-vhm6-79f3, CWE-79, medium.** Credit: Nguyen Tran Thanh Lam ([c240030](https://github.com/c240030)).

`clean_pdf_text_to_html()` escapes every sink it writes to except one: paragraph text. The `html.escape()` call on that path had been commented out. Markup embedded in a PDF therefore survived verbatim into `cleaned_html` and executed wherever the result was rendered.

The escape is restored.

### DOM-based XSS in the Playground leading to API token theft

**GHSA-m446-hp3q-qfxp, CWE-79, high.** Credit: [e1codes](https://github.com/e1codes).

The Playground result viewer reset syntax highlighting with:

```js
const text = element.textContent;
element.innerHTML = text;
```

That round trip re-parses the text as live HTML. The text is crawl output, so it is whatever the crawled page contained. Script in a crawled page could therefore run in the operator's Playground session and read the API token held there.

The round trip is removed. highlight.js renders from `textContent` and emits escaped markup on its own, so it was never needed.

## Bug fixes

Everything below landed on `develop` between 0.9.2 and this release. None of it is security related.

### Docker server

- **PDF works out of the box**: PDF scraping is supported by default, and a request that selects `PDFContentScrapingStrategy` is now routed to `PDFCrawlerStrategy` automatically. Before this you had to pair them by hand or get a placeholder back. (#2094, #2150)
- **Upstream proxy chaining**: the egress proxy now chains through `HTTP_PROXY` / `HTTPS_PROXY` instead of ignoring them, so the server works behind a corporate proxy. (#2142)
- **Proxy env handling**: junk values in the proxy environment fall through to the next candidate rather than failing the crawl, and non-http proxy schemes are refused up front. (#2094)
- **Compose v5**: compatibility fixes, clearer warnings when a legacy field is used, and better error handling in the playground. (#2094)
- **Token and LLM env**: `CRAWL4AI_API_TOKEN` is forwarded through compose, and `.llm.env` is optional instead of required. (#2094)
- **Clearer 403 on hooks**: the disabled-hooks response now says when the request used the removed `hooks.code` field, rather than giving one generic refusal. (#2094)
- **`output_path`**: declared a deprecated no-op instead of being silently ignored. (#2094)
- **`GET /monitor`**: redirects to the dashboard UI instead of returning nothing useful. (#2157, issue #2091)
- **Failed crawls are reported**: failure details are preserved for both batch and single-URL requests instead of being dropped. (#2094, #2134, issue #2133)
- **IPv6 loopback**: an unavailable IPv6 loopback no longer breaks startup. (#2081, issue #2078)
- **MCP pinning**: `mcp` is capped below 2, keeping the v1 low-level API that `mcp_bridge` depends on. (#2148, thanks @weike-zhang)
- **Compose formatting**: commented environment variable lines are aligned with the environment list. (#2156)

### Crawler and core

- **Playwright driver leak**: when a browser failed to launch inside `__aenter__`, the Playwright driver subprocess was left running. Repeated failed launches leaked one process each time. It is now cleaned up. (#2160)
- **PDF crawls wrongly flagged as blocked**: `PDFCrawlerStrategy` returns a deliberately near-empty placeholder response, and the anti-bot check read that as a block. Every PDF crawl failed, burned the whole retry budget, and then called the fallback fetch. The placeholder is now recognised. (#2138, issue #2135)
- **Cookies across PDF redirects**: redirects are followed by hand, which meant each hop started with an empty cookie jar. A host that set a cookie and then redirected never got it back, so gated and CDN-signed PDFs failed. One session now covers the whole chain. (#2159)
- **Overlay removal hang**: the overlay and consent removal scripts waited on unconditional `setTimeout` calls, which could hang a crawl under a restrictive CSP. The waits are gone. (#2139)
- **`remove_overlay_elements` deleting the page**: a page whose `<body>` carried a global popup class had its entire body removed, leaving an empty result. (#2163, thanks @Nalhin)
- **Body-visibility timeout**: now configurable and validated, and the timeout warning is emitted even when `verbose=False`. (#2117, #2131, #2145, issues #2116, #2129, #2144)

### Documentation

- Self-hosting and migration guides updated for 0.9.x. (#2093)
- The `PDFCrawlerStrategy` plus `PDFContentScrapingStrategy` pairing requirement is now documented.

## Tests

- `tests/unit/test_pdf_download_limits.py`, 22 tests: per-hop destination validation, DNS rebinding, redirect bounds, byte and page caps, untrusted-body clamping, and temp-file cleanup on abort.
- `tests/unit/test_pdf_html_escaping.py`, 7 tests: escaping of PDF paragraph text in `cleaned_html`.
- `deploy/docker/tests/test_security_pdf_image_write.py`, 6 tests: rejection of image-write fields from untrusted bodies.
- Docker endpoint coverage for crawl failures and for the per-URL `crawler_configs` PDF guard.

## Breaking changes

None.

Two defaults changed, which is worth knowing if you process large PDFs in a self-hosted deployment:

- `PDFContentScrapingStrategy` now caps downloads at 100 MiB and parsing at 2000 pages. Raise them with `max_pdf_bytes` and `max_pdf_pages` when you call it from the SDK. Requests arriving over the Docker API cannot raise them past those caps.
- `limits.wall_clock_s` in `deploy/docker/config.yml` is now `300` instead of `0`. Set it back to `0` if you deliberately want no per-crawl deadline.

## Upgrade

```bash
pip install -U crawl4ai
crawl4ai-doctor  # verify installation
```

Docker users: pull the latest image once the Docker release workflow finishes.

```bash
docker pull unclecode/crawl4ai:0.9.3
```

## Acknowledgments

Thank you to Zhixi "Jace" Sun ([manus-use](https://github.com/manus-use)), Nguyen Tran Thanh Lam ([c240030](https://github.com/c240030)), and [e1codes](https://github.com/e1codes) for reporting these issues privately and giving us time to fix them before disclosure. All reporters are listed in [SECURITY-CREDITS.md](https://github.com/unclecode/crawl4ai/blob/main/SECURITY-CREDITS.md).

Thanks to the community contributors behind the bug fixes in this release: @nightcityblade (#2130, #2131, #2117, #2134, #2081), @weike-zhang (#2148), and @Nalhin (#2163).

If you find a security issue in Crawl4AI, please report it privately. See [SECURITY.md](https://github.com/unclecode/crawl4ai/blob/main/SECURITY.md).

## Support & Resources

- [Documentation](https://docs.crawl4ai.com)
- [GitHub Issues](https://github.com/unclecode/crawl4ai/issues)
- [Discord Community](https://discord.gg/crawl4ai)

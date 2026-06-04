# Crawl4AI v0.8.9: Proxy SSRF Patch

*June 2026 - 2 min read*

---

I'm releasing Crawl4AI v0.8.9, a follow-up security patch for the self-hosted Docker API server. It closes a server-side request forgery path that v0.8.8 did not cover. It is backward compatible: upgrade in place, no configuration changes required.

If you run the Docker server, please upgrade. If it is exposed to a network, also set `CRAWL4AI_API_TOKEN`. A security advisory accompanies this release.

## What it fixes

The SSRF destination check validated the crawl target URL, but not the proxy address. An unauthenticated `/crawl`, `/crawl/stream`, or `/crawl/job` request could point a proxy at an internal IP and route the browser through it, reaching internal services and cloud-metadata endpoints, even with a perfectly valid crawl URL.

v0.8.9 validates every proxy destination with the same global-routability check before the browser is built:

- `browser_config.proxy_config.server`
- `browser_config.proxy` (deprecated field)
- `crawler_config.proxy_config.server`
- proxy / DNS-redirecting flags in `extra_args` (`--proxy-server`, `--host-resolver-rules`, `--proxy-bypass-list`, `--proxy-pac-url`) are stripped

A legitimate public proxy still works. The only behavior change: set proxies through `proxy_config` (which is validated) rather than raw `extra_args` flags.

## Upgrade

```bash
pip install -U crawl4ai
docker pull unclecode/crawl4ai:0.8.9
```

## Still coming: a secure-by-default Docker server (~1-2 weeks)

The next release remains a larger, secure-by-default update for the Docker API server, with intentional breaking changes (authentication on by default, stricter request validation, safer deployment defaults). A full migration guide will accompany the pre-announcement on Discord and X. This proxy fix is already part of that release; 0.8.9 simply brings it forward because it is an unauthenticated SSRF.

Thanks to Geo for the responsible disclosure.

Live long and import crawl4ai

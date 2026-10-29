# Crawl4AI v0.8.8: Docker Server Security Patch

*June 2026 - 3 min read*

---

I'm releasing Crawl4AI v0.8.8, a focused security patch for the self-hosted Docker API server. It is backward compatible: upgrade in place, no configuration changes required.

If you run the Docker server, please upgrade. If it is exposed to a network, also set `CRAWL4AI_API_TOKEN`. Security advisories accompany this release.

## What it fixes

- **SSRF filter gaps**: the SSRF protection now rejects any resolved address that is not globally routable, and it covers IPv6 transition forms that previously slipped past the blocklist (NAT64, 6to4, IPv4-mapped, and the unspecified `::`). These could otherwise reach internal services and cloud-metadata endpoints. Error messages no longer echo the resolved address.
- **Arbitrary file write via `output_path`**: `/screenshot` and `/pdf` now resolve symlinks and re-check containment before writing, and write with `O_NOFOLLOW`, closing a symlink/TOCTOU bypass of the output-directory restriction. Normal use is unchanged.
- **LLM credential exfiltration**: the LLM endpoints no longer honor a request-supplied `base_url`, so the configured provider key cannot be redirected to an attacker endpoint, and `LLMConfig` will not resolve protected environment variables via `env:`.
- **Hardening**: CRLF-safe logging and webhook request-header validation.

All changes are backward compatible. Details and credits are in the security advisories.

## Coming next: a secure-by-default Docker server (~1-2 weeks)

The next release is a larger, secure-by-default update for the Docker API server, and it has intentional breaking changes. I want to give everyone time to prepare, so here is the heads-up.

If you run the Docker server, plan for these and test in staging before upgrading:

- **Authentication on by default.** The server binds loopback unless you configure a credential (`CRAWL4AI_API_TOKEN`). Put a TLS-terminating reverse proxy in front to expose it.
- **Stricter request validation and safer defaults.** TLS verification on, tighter outbound egress controls, and declarative hook actions instead of inline code.
- **A few request options move server-side.** `/screenshot` and `/pdf` return an artifact id instead of a file path, and the LLM endpoint is selected by provider name.
- **Hardened container defaults.** Least-privilege compose, Redis authentication, loopback bind.

A full migration guide will go out with the pre-announcement on Discord and X. Watch those channels.

## Upgrade

```bash
pip install -U crawl4ai
# Docker
docker pull unclecode/crawl4ai:0.8.8
```

Thanks to everyone who reports issues responsibly. Star and use Crawl4AI: https://github.com/unclecode/crawl4ai

Live long and import crawl4ai

# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.9.x   | :white_check_mark: |
| 0.8.x   | :x: (upgrade recommended) |
| 0.7.x   | :x: (upgrade recommended) |
| < 0.7   | :x:                |

Fixes are not backported to earlier lines. The 0.9.3 advisories listed below are not patched in any 0.8.x release; if you run 0.8.x, upgrade.

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report via one of these methods:

1. **GitHub Security Advisories (Preferred)**
   - Go to [Security Advisories](https://github.com/unclecode/crawl4ai/security/advisories)
   - Click "New draft security advisory"
   - Fill in the details

2. **Email**
   - Send details to: unclecode@crawl4ai.com (CC: nasrin@crawl4ai.com and aravind@crawl4ai.com)
   - Use subject: `[SECURITY] Brief description`
   - Include:
     - Description of the vulnerability
     - Steps to reproduce
     - Potential impact
     - Any suggested fixes

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Resolution Timeline**: Depends on severity
  - Critical: 24-72 hours
  - High: 7 days
  - Medium: 30 days
  - Low: 90 days

### Disclosure Policy

- We follow responsible disclosure practices
- We will coordinate with you on disclosure timing
- Credit will be given to reporters (unless anonymity is requested)
- We may request CVE assignment for significant vulnerabilities

## Security Best Practices for Users

### Docker API Deployment

If you're running the Crawl4AI Docker API in production:

1. **Enable Authentication**
   ```yaml
   # config.yml
   security:
     enabled: true
     jwt_enabled: true
   ```
   ```bash
   # Set a strong secret key
   export SECRET_KEY="your-secure-random-key-here"
   ```

2. **Hooks are Declarative** (v0.9.0+)
   - Request-supplied hook code is no longer accepted; only the fixed action set in `GET /hooks/info`
   - On 0.8.x, hooks are disabled by default; set `CRAWL4AI_HOOKS_ENABLED=true` only if you trust all API users

3. **Network Security**
   - Run behind a reverse proxy (nginx, traefik)
   - Use HTTPS in production
   - Restrict access to trusted IPs if possible

4. **Container Security**
   - Run as non-root user (default in our container)
   - Use read-only filesystem where possible
   - Limit container resources

### Library Usage

When using Crawl4AI as a Python library:

1. **Validate URLs** before crawling untrusted input
2. **Sanitize extracted content** before using in other systems
3. **Be cautious with hooks** - they execute arbitrary code

## Known Security Issues

All issues below are fixed in the version named. Advisories with a GHSA id are published under [Security Advisories](https://github.com/unclecode/crawl4ai/security/advisories). Full detail for every release is in [CHANGELOG.md](CHANGELOG.md); reporter credits are in [SECURITY-CREDITS.md](SECURITY-CREDITS.md).

### Fixed in v0.9.3 (2026-08-31)

| ID | Severity | Component | Description | Fix |
|----|----------|-----------|-------------|-----|
| GHSA-xpp7-j28w-2gvx | HIGH | Library + Docker API | Arbitrary file write via `PDFContentScrapingStrategy` image-write fields in untrusted config bodies (CWE-22) | `save_images_locally` / `image_save_dir` filtered at the trust boundary; `extract_images` forced off for untrusted bodies |
| GHSA-q5rj-45vw-vp2g | HIGH | Library | SSRF via PDF download redirects; DNS rebinding (CWE-918) | Redirects resolved manually with a per-hop destination check (max 5 hops); peer IP of the read response validated |
| GHSA-v2rm-hvrj-2x9q | MEDIUM | Library | Denial of service via unbounded PDF size and page count (CWE-400) | `max_pdf_bytes` (100 MiB) and `max_pdf_pages` (2000) caps; untrusted bodies cannot raise them |
| GHSA-7g3g-vhm6-79f3 | MEDIUM | Library | XSS via unescaped PDF paragraph text in `cleaned_html` (CWE-79) | Paragraph text escaped like every other sink |
| GHSA-m446-hp3q-qfxp | HIGH | Docker Playground | DOM-based XSS via `innerHTML` round-trip in the result viewer, leading to API token theft (CWE-79) | Round-trip removed; highlight.js renders from `textContent` |

### Fixed in v0.9.2 (2026-07-15)

| ID | Severity | Component | Description | Fix |
|----|----------|-----------|-------------|-----|
| - | LOW | Docker API | `/monitor/ws` WebSocket returned 500 under JWT auth because the router-level token dependency cannot run on WebSocket scopes | Auth enforced by `AuthGateMiddleware`; admin routes keep `require_admin` |

### Fixed in v0.9.1 (2026-07-08)

| ID | Severity | Component | Description | Fix |
|----|----------|-----------|-------------|-----|
| - | MEDIUM | Docker API | Rate-limit Redis storage connected without the configured password | Rate limiter authenticates to Redis |

### Fixed in v0.9.0 (2026-06-18)

Secure-by-default rework of the Docker API server. The pip library is unchanged. See `deploy/docker/MIGRATION.md`.

| ID | Severity | Component | Description | Fix |
|----|----------|-----------|-------------|-----|
| - | CRITICAL | Docker API | Unauthenticated API served on `0.0.0.0` by default (CWE-306) | Auth on by default; loopback bind unless `CRAWL4AI_API_TOKEN` is set |
| - | CRITICAL | Docker API | Request-supplied hook code executed on the server (CWE-94) | `hooks.code` removed; fixed set of declarative hook actions |
| - | HIGH | Docker API | Chromium launch-arg injection via request-supplied `browser_config.extra_args` (CWE-94) | `extra_args` rejected at the network boundary |
| - | HIGH | Docker API | Path traversal to file write via download sinks (CWE-22) | basename + realpath + `O_NOFOLLOW` confinement |
| - | HIGH | Docker API | SSRF on `/crawl/stream` and `/crawl` with `stream=true` (CWE-918) | Destination validation added; HTTP 400 on disallowed targets |
| - | HIGH | Docker API | Request body could drive browser internals (`js_code`, `proxy_config`, `cdp_url`, `user_data_dir`, `cookies`, `headers`, `init_scripts`, `base_url`, ...) | Request trust boundary: scalar declarative options only, HTTP 400 otherwise |
| - | MEDIUM | Docker API | Weak JWT, unscoped monitor actions, permissive CORS, TLS verification off, unauthenticated Redis, unbounded job queue, verbose 5xx, unvalidated webhook headers | Hardened defaults for each; see CHANGELOG 0.9.0 |

### Fixed in v0.8.9 (2026-06-04)

| ID | Severity | Component | Description | Fix |
|----|----------|-----------|-------------|-----|
| - | HIGH | Docker API | SSRF via `proxy_config.server`, deprecated `proxy`, or `--proxy-server` / `--host-resolver-rules` in `extra_args` (CWE-918) | All proxy destinations validated with the global-routability check; proxy/DNS flags stripped from `extra_args` |

### Fixed in v0.8.8 (2026-06-04)

| ID | Severity | Component | Description | Fix |
|----|----------|-----------|-------------|-----|
| - | HIGH | Docker API | SSRF filter bypass via IPv6 transition forms (NAT64, 6to4, IPv4-mapped, `::`) (CWE-918) | Reject any resolved address that is not globally routable; errors no longer echo the address |
| - | HIGH | Docker API | Symlink / TOCTOU bypass of the `output_path` directory restriction on `/screenshot` and `/pdf` (CWE-59/22) | Resolve symlinks, re-check containment, write with `O_NOFOLLOW` |
| - | HIGH | Docker API | LLM credential exfiltration via request-supplied `base_url` on `/md`, `/llm`, `/llm/job`; `env:` token resolved protected variables (CWE-522/200) | `base_url` ignored; `LLMConfig` refuses protected env vars |
| - | LOW | Docker API | CRLF log injection (CWE-117); unvalidated webhook request headers (CWE-93) | Control characters stripped from log records; webhook header name/value validation |

### Fixed in v0.8.7 (2026-06-01)

| ID | Severity | Component | Description | Fix |
|----|----------|-----------|-------------|-----|
| - | CRITICAL (9.8) | Docker API | AST sandbox escape via `gi_frame.f_back` in computed-field `eval()` leading to pre-auth RCE (CWE-94/913) | `eval()` removed from computed fields; `_safe_eval_expression` deleted |
| - | CRITICAL (9.8) | Docker API | Hook sandbox escape: injected modules carried full `__builtins__` (CWE-94) | Injected builtins stripped; dangerous allowlist entries removed |
| - | CRITICAL (9.8) | Docker API | Hardcoded default JWT secret `"mysecret"` allowed token forgery (CWE-798) | Default removed; weak secrets rejected; ephemeral key generated if none set |
| - | HIGH (9.1) | Docker API | Arbitrary file write via `output_path` on `/screenshot` and `/pdf` (CWE-22) | Writes restricted to `CRAWL4AI_OUTPUT_DIR`; `..` rejected |
| - | HIGH (8.6) | Docker API | SSRF via webhook URL on `/crawl/job` and `/llm/job` (CWE-918) | Blocklist; `follow_redirects=False` |
| - | HIGH (8.6) | Docker API | SSRF via `/crawl`, `/md`, `/llm`; IPv6-mapped IPv4 bypass (CWE-918) | Destination validation on all entry points; IPv6-mapped IPv4 normalized |
| - | HIGH (8.1) | Docker API | Arbitrary JavaScript execution via `/execute_js` (CWE-94) | Disabled by default (`CRAWL4AI_EXECUTE_JS_ENABLED`); `--disable-web-security` removed from default args |
| - | MEDIUM (6.5) | Docker API | `/monitor/*` routes, including destructive actions, unauthenticated (CWE-306) | `token_dep` on the router; explicit check on the WebSocket |
| - | MEDIUM (6.1) | Docker API | Stored XSS in the monitor dashboard via `innerHTML` (CWE-79) | Server-side `html.escape()`; client-side `escapeHtml()` |
| - | MEDIUM | Docker API | `eval()` in `/config/dump` | Replaced by Pydantic-validated JSON |

### Fixed in v0.8.6 (2026-03-24)

| ID | Severity | Component | Description | Fix |
|----|----------|-----------|-------------|-----|
| - | CRITICAL | Library + Docker | PyPI supply-chain compromise of the `litellm` dependency | Dependency replaced with `unclecode-litellm` |

### Fixed in v0.8.5 (2026-03-18)

| ID | Severity | Component | Description | Fix |
|----|----------|-----------|-------------|-----|
| CVE-2025-49844 | CRITICAL (10.0) | Docker (Redis) | Lua use-after-free in bundled Redis | Redis upgraded to 7.2.7 |
| - | MEDIUM | Library | XSS via `innerHTML` in iframe processing | `DOMParser` used instead (#1796) |
| - | MEDIUM | Docker API | `/token` endpoint issued tokens without checking `api_token` | `api_token` required when configured (#1795) |

### Fixed in v0.8.1 (2026-01-30)

| ID | Severity | Component | Description | Fix |
|----|----------|-----------|-------------|-----|
| CVE-pending-3 | CRITICAL | Docker API | RCE via deserialization + `eval()` in `/crawl` endpoint | Allowlisted deserializable types; AST-validated computed field expressions (later removed entirely in 0.8.7) |

### Fixed in v0.8.0 (2026-01-16)

| ID | Severity | Component | Description | Fix |
|----|----------|-----------|-------------|-----|
| CVE-pending-1 | CRITICAL | Docker API | RCE via hooks `__import__` | Removed from allowed builtins; hooks disabled by default |
| CVE-pending-2 | HIGH | Docker API | LFI via `file://` URLs | URL scheme validation added |

## Security Features

### v0.9.3+

- **PDF egress policy**: PDF downloads validate every redirect hop and the peer IP actually read, so the Docker SSRF policy also covers the out-of-browser `requests` path
- **PDF resource caps**: `max_pdf_bytes` (100 MiB) and `max_pdf_pages` (2000), not raisable from an untrusted request body
- **PDF image-write fields filtered** from untrusted bodies; `extract_images` forced off
- **Egress proxy upstream chaining**: the pinning egress proxy honours `HTTP_PROXY` / `HTTPS_PROXY` and refuses non-http proxy schemes
- **Per-crawl wall clock**: Docker config ships `limits.wall_clock_s` of 300 seconds

### v0.9.0+ (Docker API server, secure by default)

- **Authentication on by default**: loopback bind unless `CRAWL4AI_API_TOKEN` is set; `Authorization: Bearer <token>` required on every request except `GET /health`
- **Request trust boundary**: crawl request bodies carry scalar, declarative options only; browser internals and code fields are rejected with HTTP 400; unknown fields dropped; timeouts, viewport and scroll counts clamped
- **Declarative hooks**: `hooks.code` removed; fixed action set (`block_resources`, `add_cookies`, `set_headers`, `scroll_to_bottom`, `wait_for_timeout`)
- **`extra_args` rejected** over the network, closing the Chromium launch-arg injection class
- **Artifact ids instead of `output_path`**: `/screenshot` and `/pdf` return an `artifact_id`; fetch via authenticated `GET /artifacts/{id}` with TTL and quota
- **Download path confinement**: basename + realpath + `O_NOFOLLOW`
- **SSRF validation on every crawl path**, including `/crawl/stream`; internal targets need `CRAWL4AI_ALLOW_INTERNAL_URLS=true`
- **Hardened JWT** (tokens from older versions are invalid; re-mint via `POST /token`); **admin scope** for `/monitor/actions/*` and `/monitor/stats/reset`
- **CORS deny by default** (`security.cors_allow_origins`); **strict security headers**
- **TLS verification on**; escape hatch `CRAWL4AI_ALLOW_INSECURE_TLS=true`
- **Redis password-protected and loopback-only**; port no longer published
- **Bounded job queue**: body size, per-crawl wall clock, queue size and per-principal concurrency capped
- **Generic 5xx responses** with a correlation id; **webhook headers validated** (HTTP 422 on malformed or hop-by-hop headers)
- **LLM provider by name only**: `base_url` removed; providers constrained by `config.llm.allowed_providers`

### v0.8.7+ to v0.8.9+ (Docker API server)

- **Global-routability SSRF check** on crawl targets, webhook URLs and proxy destinations, evaluated on IPv6 transition forms
- **`/execute_js` disabled by default** (`CRAWL4AI_EXECUTE_JS_ENABLED`)
- **No default JWT secret**; weak secrets rejected
- **Monitor routes authenticated**; monitor dashboard output escaped
- **`eval()` removed** from computed fields and `/config/dump`
- **Protected env vars** cannot be resolved through the `LLMConfig` `env:` token form
- **CRLF-safe logging**

### v0.8.1+

- **Deserialization Allowlist**: Only known-safe types can be instantiated via API config

### v0.8.0+

- **URL Scheme Validation**: Blocks `file://`, `javascript:`, `data:` URLs on API
- **Hooks Disabled by Default**: Opt-in via `CRAWL4AI_HOOKS_ENABLED=true` (replaced by declarative hooks in 0.9.0)
- **Restricted Hook Builtins**: No `__import__`, `eval`, `exec`, `open`
- **JWT Authentication**: Optional (on by default since 0.9.0)
- **Rate Limiting**: Configurable request limits
- **Security Headers**: X-Frame-Options, CSP, HSTS when enabled

## Acknowledgments

We thank the security researchers who responsibly disclosed the issues above. The full list, with the vulnerability each person reported and the release that fixed it, is maintained in [SECURITY-CREDITS.md](SECURITY-CREDITS.md).

---

*Last updated: September 2026*

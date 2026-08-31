# Crawl4AI v0.9.0: Secure-by-Default Docker Server

*June 2026 - 6 min read*

---

I'm releasing Crawl4AI v0.9.0, a major, secure-by-default release of the Crawl4AI Docker API server. This is the biggest change to the self-hosted HTTP server since we shipped it. It moves the out-of-the-box deployment from an open, trust-the-caller posture to a closed, hardened one with defense in depth.

This is a breaking release for the Docker server only. The core pip library (the SDK and in-process use) is unchanged. If you only `pip install crawl4ai` and drive it from Python, nothing here affects you and you can upgrade freely.

If you self-host the Docker API server, please read the [migration guide](https://github.com/unclecode/crawl4ai/blob/main/deploy/docker/MIGRATION.md) before you upgrade, and roll out behind a staging environment first.

## Why this release

Over the last few releases we patched a series of issues in the Docker server one at a time. 0.9.0 finishes the job by changing the architecture instead of patching behavior. The principle is simple: the server should be safe the moment you start it, and the network request body should be treated as untrusted input rather than a trusted control channel.

That means the permissive defaults are gone. Authentication is on by default. The server binds loopback unless you give it a token. The request body carries declarative options only. Everything that used to let a caller reach into browser internals or supply code now lives server-side, where the operator controls it.

## What changed at a glance

- **Auth on by default, loopback bind**: no unauthenticated API on `0.0.0.0`.
- **Request trust boundary**: crawl request bodies are declarative and scalar; power fields are rejected at the network edge.
- **Declarative hooks**: a fixed action set replaces request-supplied hook code.
- **Artifact store**: `output_path` is gone; screenshots and PDFs return an artifact id you fetch with auth.
- **Provider by name**: LLM endpoints select a provider by name, configured server-side.
- **Hardened transport and infra**: TLS verification on, deny-by-default CORS, strict security headers, password-protected loopback-only Redis, a bounded job queue, and generic error responses with correlation ids.

## Hardening details

### Authentication and binding

The server no longer serves an unauthenticated API on `0.0.0.0`. With no token configured it binds `127.0.0.1` only and prints a one-off token at startup for local use. To expose it, set a token and put a TLS-terminating reverse proxy in front:

```bash
export CRAWL4AI_API_TOKEN="$(openssl rand -hex 32)"
```

Every request except `GET /health` then needs `Authorization: Bearer <token>`. WebSocket clients that cannot set headers may pass `?token=...`. The JWT implementation changed, so tokens from older versions are no longer valid; re-mint via `POST /token`.

### The request trust boundary

A crawl request body now carries declarative, scalar options only. Fields that previously let a caller drive browser internals or arbitrary code are rejected with HTTP 400 at the network boundary, including `js_code`, `c4a_script`, `proxy_config`, `extra_args`, `user_data_dir`, `cdp_url`, `cookies`, `headers`, `init_scripts`, `base_url`, `deep_crawl_strategy`, `simulate_user`, `magic`, and `process_in_browser`. Configure these server-side, or use the in-process SDK where you keep full control. Unknown fields are dropped, and timeouts, viewport, and scroll counts are clamped to safe maximums.

Request-supplied browser launch arguments (`browser_config.extra_args`) are part of this boundary and are now rejected, closing a Chromium launch-argument injection class.

### Declarative hooks

`hooks.code` (Python strings) is replaced by a fixed set of declarative actions: `block_resources`, `add_cookies`, `set_headers`, `scroll_to_bottom`, and `wait_for_timeout`. Call `GET /hooks/info` for the parameter schemas. Arbitrary hook code remains available in a self-hosted in-process build.

### Downloads, screenshots, and PDFs

Download sinks now confine writes with basename plus realpath plus `O_NOFOLLOW`, removing a path-traversal-to-file-write class. `output_path` is removed from `/screenshot` and `/pdf`; the server stores the result and returns an `artifact_id` plus a URL, which you fetch with authenticated `GET /artifacts/{artifact_id}` (artifacts have a TTL and a storage quota).

### SSRF on the streaming path

Destination validation now covers the streaming crawl handler. `/crawl/stream` and `/crawl` with `stream=true` validate the target and return HTTP 400 for disallowed destinations, matching the non-streaming handlers.

### Transport and infrastructure

TLS verification is on; self-signed or internal targets fail by default, with explicit escape hatches (`CRAWL4AI_ALLOW_INSECURE_TLS`, `CRAWL4AI_ALLOW_INTERNAL_URLS`) for trusted internal testing. CORS is deny-by-default; allowlist your frontend origin under `security.cors_allow_origins`. Redis runs in-container, loopback-only, password-protected, with its port no longer published. Background jobs run on a bounded queue, and request size, wall-clock, and per-principal concurrency are capped (all configurable, `0` = unbounded). 5xx responses return a generic body with a correlation id you can match in the logs.

## Migrating

How much you have to do scales with how much you drove through the API. A plain "crawl these URLs with a normal config" user only needs to set a token and re-issue tokens. Everything else applies only if you used that specific feature.

Read the [migration guide](https://github.com/unclecode/crawl4ai/blob/main/deploy/docker/MIGRATION.md) first, then follow `deploy/docker/SECURITY-VERIFY.md` for the deployment checklist.

## Upgrade

```bash
pip install -U crawl4ai
```

Docker users should pull the latest image once the Docker release workflow finishes.

## Security Credits

Thank you to the researchers who disclosed these issues responsibly: Y4tacker, KOH Jun Sheng, and UDU_RisePho ([hoanggxyuuki](https://github.com/hoanggxyuuki)). Full details are in `SECURITY-CREDITS.md`.

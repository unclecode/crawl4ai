# Migration Guide — Docker Server Hardening Release

This is a major, **secure-by-default** release of the Crawl4AI **Docker API
server** (`deploy/docker/`). Several defaults changed in breaking ways so the
out-of-the-box deployment is safe. The core pip library (SDK / in-process use)
is **unchanged** — these notes apply only to the self-hosted HTTP server.

How much you have to do scales with how much you drove through the API. A plain
"crawl these URLs with a normal config" user only does the two steps in
**Everyone**. The rest applies only if you used that specific feature.

> Upgrading from a self-hosted server? Read this first, then roll out behind a
> staging environment. See `SECURITY-VERIFY.md` for the deployment checklist.

---

## Everyone (2 steps)

### 1. Set an API token

The server no longer serves an unauthenticated API on `0.0.0.0`. It binds
loopback by default and will not expose itself without a credential.

```bash
export CRAWL4AI_API_TOKEN="$(openssl rand -hex 32)"
```

- With a token set, you may expose the server (put a TLS-terminating reverse
  proxy in front) and must send `Authorization: Bearer <token>` on every
  request except `GET /health`.
- With **no** token set, the server binds `127.0.0.1` only and prints a one-off
  token at startup for local use.

WebSocket clients (MCP, monitor) that can't set headers may pass `?token=...`.

### 2. Re-issue any tokens

The JWT implementation changed; tokens issued by older versions are no longer
valid. Re-mint via `POST /token` (which now requires the server to have an
`api_token` configured).

---

## Only if you used that feature

### Request bodies accept declarative options only

A crawl request body now carries scalar, declarative options only. The
following are **rejected with HTTP 400** when sent over the network; configure
them server-side or run a self-hosted in-process build (the SDK keeps full
control):

`js_code`, `js_code_before_wait`, `c4a_script`, `proxy` / `proxy_config`,
`extra_args`, `user_data_dir`, `cdp_url`, `cookies`, `headers`, `init_scripts`,
`base_url`, `deep_crawl_strategy`, `simulate_user`, `magic`,
`process_in_browser`, and nested LLM config objects.

Unknown fields are dropped; timeouts, viewport and scroll counts are clamped to
safe maximums.

### Hooks: declarative actions instead of code

`hooks.code` (Python strings) is replaced by a fixed set of declarative actions:

```jsonc
{
  "hooks": {
    "hooks": [
      {"action": "block_resources", "params": {"resource_types": ["image", "font"]}},
      {"action": "scroll_to_bottom",  "params": {"max_steps": 10, "delay_ms": 500}}
    ]
  }
}
```

Available actions: `block_resources`, `add_cookies`, `set_headers`,
`scroll_to_bottom`, `wait_for_timeout`. Call `GET /hooks/info` for the parameter
schemas. Arbitrary hook code is available in a self-hosted in-process build.

### Screenshot / PDF: artifact id instead of `output_path`

`output_path` is removed. The server stores the result and returns an id + URL:

```jsonc
{"success": true, "screenshot": "<base64>",
 "artifact_id": "….", "url": "/artifacts/….", "mime": "image/png", "size": 12345}
```

Fetch the file with `GET /artifacts/{artifact_id}` (authenticated). Artifacts
have a TTL and a storage quota.

### LLM endpoints: provider by name

`base_url` is removed from `/md`, `/llm`, and `/llm/job`. Select a provider by
**name** only; the endpoint and key are configured server-side via env
(`OPENAI_BASE_URL` / `LLM_BASE_URL`) and `config.llm.allowed_providers`. A
provider outside the allowed family returns 400.

### Monitor actions need an admin token

`POST /monitor/actions/cleanup|kill_browser|restart_browser` and
`/monitor/stats/reset` require an **admin-scope** principal (the static
`CRAWL4AI_API_TOKEN` is admin; `/token`-issued JWTs are `data` scope).

### Browser / JS clients: allowlist your origin (CORS)

Cross-origin browser requests are denied unless allowlisted:

```yaml
security:
  cors_allow_origins: ["https://your-frontend.example"]
```

### TLS verification is on

Self-signed / internal TLS crawl targets now fail by default. For trusted
internal testing only: `CRAWL4AI_ALLOW_INSECURE_TLS=true`. Internal-network
crawling escape hatch: `CRAWL4AI_ALLOW_INTERNAL_URLS=true`.

### Webhook headers are validated

Custom webhook headers must be well-formed names with no control characters and
may not set hop-by-hop / sensitive headers (`Host`, `Content-Length`,
`Transfer-Encoding`, `Authorization`, `Cookie`, …). Invalid headers → 422.

### Redis requires a password

Redis runs in-container, loopback-only, password-protected, and its port is no
longer published. For an **external** redis, set `REDIS_PASSWORD`.

### Resource limits (all configurable; `0` = unbounded)

```yaml
limits:
  max_body_bytes: 10485760   # request body cap (413); 0 = unbounded
  wall_clock_s: 0            # per-crawl deadline (504); 0 = none
  queue:
    maxsize: 1000            # background job queue (503 when full); 0 = unbounded
    workers: 4
    per_principal: 0         # max concurrent jobs per caller (429); 0 = unlimited
```

To keep the previous behavior exactly, set the caps you don't want to `0`.

### Error responses are generic

5xx responses return `{"error": "Internal server error", "correlation_id": "…"}`.
Match the correlation id in the server logs for detail. Developer-facing 4xx
messages are unchanged.

---

## Defaults summary

| Setting | Old | New |
| --- | --- | --- |
| Bind | `0.0.0.0`, open | `127.0.0.1`; exposing requires a token |
| Auth | off by default | on by default |
| Security headers / CSP | off | on (strict on the API surface) |
| CORS | none | deny-by-default |
| TLS verification | disabled | enabled |
| Redis | no password, port published | password, loopback, not published |
| `output_path` | accepted | removed (artifact store) |
| LLM `base_url` in request | honored | removed |
| Hooks | Python code | declarative actions |
| Background jobs | unbounded | bounded queue (configurable, 0 = unbounded) |

## Operational notes

- **`--no-sandbox`** is still set by default (the container runs as non-root
  without a usable sandbox). To drop it, run the container with an unprivileged
  user namespace (`unprivileged_userns_clone=1`) or a seccomp profile, then set
  `CRAWL4AI_CHROMIUM_SANDBOX=true`. See `SECURITY-VERIFY.md`.
- The hardened `docker-compose.yml` uses `read_only: true` + tmpfs, `cap_drop:
  [ALL]`, `no-new-privileges`, and `shm_size` instead of a host `/dev/shm` bind.
  Mirror these in a custom compose file.
- The `/dashboard` and `/playground` UIs get baseline headers
  (`nosniff`, `X-Frame-Options: DENY`) and are auth-gated; a stricter CSP for
  the UIs is planned in a follow-up.

# Security Hardening — Build/Runtime Verification Runbook

The offline test suite (`pytest deploy/docker/tests/test_security_*.py`) covers
the logic of the hardening. A handful of items can only be confirmed with a real
`docker build` + boot or a browser. This runbook lists those, with exact
commands and expected results. Run it before relying on the hardened image.

Prereqs: Docker + docker compose, a checkout of this branch.

---

## 0. Offline suite (no Docker) — should already pass

```bash
python -m pip install -e . && pip install -r deploy/docker/requirements.txt pytest pytest-asyncio
pytest deploy/docker/tests/test_security_*.py -q
```
Expected: all pass, `1 xfailed` (the `--no-sandbox` posture test, see §3).

---

## 1. Build the hardened image

```bash
IMAGE=local-sec docker compose build
# or: docker build -t unclecode/crawl4ai:local-sec .
```
Expected: build succeeds. Note the `/app` dir is now root-owned + read-only and
the artifact dir `/var/lib/crawl4ai/outputs` is created 0700.

---

## 2. Boot + bind posture (entrypoint)

### 2a. No credential -> loopback only (refuses to expose)

```bash
docker run --rm -p 11235:11235 unclecode/crawl4ai:local-sec &
sleep 8
docker logs <id> 2>&1 | grep -i "binding loopback only"   # expect this line
curl -fsS http://localhost:11235/health                   # expect: NOT reachable
```
Expected: entrypoint logs "no CRAWL4AI_API_TOKEN set; binding loopback only";
the mapped port is **not** reachable from the host (gunicorn bound 127.0.0.1
inside the container). This is the fail-closed default.

### 2b. With a credential -> may expose 0.0.0.0

```bash
TOKEN=$(openssl rand -hex 32)
docker run --rm -e CRAWL4AI_API_TOKEN=$TOKEN -p 11235:11235 unclecode/crawl4ai:local-sec &
sleep 8
curl -fsS http://localhost:11235/health                            # expect 200
curl -fsS http://localhost:11235/schema                            # expect 401
curl -fsS -H "Authorization: Bearer $TOKEN" http://localhost:11235/schema  # expect 200
```

---

## 3. Chromium sandbox (`--no-sandbox`)

Default keeps `--no-sandbox` (works as today). To verify the hardened path:

### Option A — unprivileged user namespace (preferred)
Host: `sysctl -w kernel.unprivileged_userns_clone=1` (Debian/Ubuntu).
```bash
docker run --rm -e CRAWL4AI_API_TOKEN=$TOKEN -e CRAWL4AI_CHROMIUM_SANDBOX=true \
  -p 11235:11235 unclecode/crawl4ai:local-sec &
sleep 8
curl -fsS -X POST http://localhost:11235/crawl \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"urls":["https://example.com"]}'
```
Expected: a successful crawl (Chromium started sandboxed). If it fails to launch,
the host lacks userns — keep the default or use Option B.

### Option B — seccomp profile
Provide a Chrome seccomp profile and wire it in compose:
```yaml
security_opt:
  - seccomp=./seccomp-chrome.json
```
then set `CRAWL4AI_CHROMIUM_SANDBOX=true` and re-run the crawl above.

If verified, flip the default: remove `--no-sandbox` from `config.yml` and the
`test_no_no_sandbox_flag` xfail in `test_security_default_posture.py` becomes a
normal pass.

---

## 4. Read-only rootfs + tmpfs (compose)

```bash
docker compose up -d              # uses read_only: true + tmpfs
sleep 8
# Writes outside tmpfs must fail:
docker compose exec crawl4ai sh -c 'echo x > /app/should_fail' ; echo "exit=$?"   # expect non-zero
# Artifact write (tmpfs) must work via the API:
curl -fsS -X POST http://localhost:11235/screenshot \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}' | grep artifact_id
```
Expected: `/app` write fails (read-only), screenshot returns an `artifact_id`,
and `GET /artifacts/{id}` (with the token) returns the PNG.

---

## 5. Redis is loopback + password-protected, not exposed

```bash
docker compose exec crawl4ai sh -c 'redis-cli -p 6379 ping'                 # expect: NOAUTH / error
docker compose exec crawl4ai sh -c 'redis-cli -a "$REDIS_PASSWORD" ping'    # expect: PONG
# From the host, the redis port must NOT be reachable (no EXPOSE / publish):
nc -z localhost 6379 ; echo "exit=$?"                                        # expect non-zero
```

---

## 6. Browser egress proxy (DNS-rebinding control)

The browser is routed through the localhost pinning proxy. To confirm end to end:
```bash
# A normal public crawl works:
curl -fsS -X POST http://localhost:11235/crawl -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"urls":["https://example.com"]}' | grep '"success": true'
# An internal target is refused up front (and the proxy would 403 a rebind):
curl -s -X POST http://localhost:11235/crawl -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"urls":["http://169.254.169.254/"]}'  # expect 400 blocked
```
(For a true rebinding test, point a host at a TTL-0 record that flips public->
internal and confirm the crawl never reaches the internal IP.)

---

## 7. Dashboard / playground (browser, CSP)

Open `http://localhost:11235/dashboard` and `/playground` in a browser (send the
token). Expected today: they load and work; response headers include
`X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY`, but **no** strict
CSP (they still use inline scripts + CDN assets). Extending the strict CSP to
these mounts requires the externalization work noted in MIGRATION.md.

---

## Sign-off checklist

- [ ] §0 offline suite green (1 xfail)
- [ ] §2a loopback-only without a token; §2b exposed + gated with a token
- [ ] §3 Chromium starts sandboxed under userns/seccomp (if pursuing no-sandbox removal)
- [ ] §4 `/app` read-only; artifacts work on tmpfs
- [ ] §5 redis requires auth + not host-reachable
- [ ] §6 public crawl works; internal target blocked
- [ ] §7 dashboard/playground load with baseline headers

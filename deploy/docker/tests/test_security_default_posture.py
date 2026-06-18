"""
HEADLINE SECURITY POSTURE GATE  —  test_security_default_posture

This is the acceptance gate for the Docker-server security hardening
(root causes R1-R7). It boots the server *with the shipped config.yml* and
asserts the secure-by-default end state:

  - every mutating + read endpoint, static mount, and MCP transport requires
    auth out of the box (R1); only the health check is public,
  - the token endpoint will not freely mint credentials when no api_token /
    secret is configured (R1),
  - strong security headers + a strict CSP are present on every response even
    when `security.enabled` is false (R6),
  - the effective browser launch flags carry no `--no-sandbox` and no
    TLS-verification-disabling flags (R3/R7),
  - Redis requires a password and security is on by default (R7),
  - dangerous request->code features are off by default (R2).

IT IS EXPECTED TO BE RED TODAY. Each failing assertion names one gap the
hardening must close. As R1-R7 land, methods flip green; when the whole class
is green, the default Docker deploy is safe and CI can gate on it.

Run:  pytest deploy/docker/tests/test_security_default_posture.py -v
"""

import pytest

pytestmark = pytest.mark.posture

HEALTH = "/health"

# (method, path, json-body-or-None) for every endpoint that must NOT be
# reachable without authentication. Bodies are intentionally minimal/invalid so
# that in the *current* (open) state the request fails fast at validation
# rather than launching a real crawl — the assertion (== 401) still fails,
# which is the RED signal we want, with no browser/network side effects.
PROTECTED_ENDPOINTS = [
    # mutating / action endpoints
    ("post", "/crawl", {}),
    ("post", "/crawl/stream", {}),
    ("post", "/md", {}),
    ("post", "/html", {}),
    ("post", "/screenshot", {}),
    ("post", "/pdf", {}),
    ("post", "/execute_js", {}),
    ("post", "/config/dump", {}),
    ("post", "/crawl/job", {}),
    ("post", "/llm/job", {}),
    # monitor mutating actions (must additionally require *admin* scope; here we
    # only assert they are not anonymously reachable). Pools are empty without a
    # lifespan, so probing these performs no destructive action.
    ("post", "/monitor/actions/cleanup", {}),
    ("post", "/monitor/actions/kill_browser", {}),
    ("post", "/monitor/actions/restart_browser", {}),
    ("post", "/monitor/stats/reset", {}),
    # read / info endpoints that currently have NO auth dependency at all
    ("get", "/schema", None),
    ("get", "/hooks/info", None),
    ("get", "/ask", None),
    ("get", "/metrics", None),
    ("get", "/llm/example.com", None),  # no `q` -> fast 400 today, must be 401
    ("get", "/monitor/health", None),
    ("get", "/monitor/requests", None),
    ("get", "/monitor/browsers", None),
    ("get", "/monitor/endpoints/stats", None),
    ("get", "/monitor/timeline", None),
    # MCP transport (must be gated; today it is open AND launders credentials)
    ("get", "/mcp/schema", None),
    # static mounts (dashboard / playground served unauthenticated today)
    ("get", "/dashboard/", None),
    ("get", "/playground/", None),
]


def _call(client, method, path, body):
    fn = getattr(client, method)
    if body is not None:
        return fn(path, json=body)
    return fn(path)


class TestDefaultDeployIsSafe:
    """The shipped Docker image must be secure with an empty/default config."""

    # ───────────────────────── R1: authentication ─────────────────────────

    def test_health_check_is_public(self, stock_client):
        """The health endpoint is the one intentionally public route."""
        r = stock_client.get(HEALTH)
        assert r.status_code == 200

    @pytest.mark.parametrize(
        "method,path,body",
        PROTECTED_ENDPOINTS,
        ids=[f"{m.upper()} {p}" for m, p, _ in PROTECTED_ENDPOINTS],
    )
    def test_endpoint_requires_auth_by_default(self, stock_client, method, path, body):
        """Without a credential, every non-health route must refuse (401)."""
        r = _call(stock_client, method, path, body)
        assert r.status_code == 401, (
            f"{method.upper()} {path} returned {r.status_code} unauthenticated; "
            f"expected 401. Endpoint is reachable without a credential."
        )

    def test_token_endpoint_does_not_freely_mint(self, stock_client, server_module, monkeypatch):
        """With no api_token configured, /token must not hand a JWT to anyone.

        Force the email-domain MX check to pass so the test exercises the real
        vulnerability (anonymous token minting) rather than passing for the
        wrong reason when offline.
        """
        monkeypatch.setattr(server_module, "verify_email_domain", lambda email: True)
        r = stock_client.post("/token", json={"email": "attacker@example.com"})
        if r.status_code == 200:
            assert "access_token" not in r.json(), (
                "/token minted a credential for an anonymous caller with no "
                "api_token configured — anyone can self-issue a valid JWT."
            )

    # ─────────────────────── R6: headers / CSP / framing ──────────────────

    def test_security_headers_present_by_default(self, stock_client):
        """Baseline security headers must be emitted even when security.enabled is false."""
        r = stock_client.get(HEALTH)
        h = {k.lower(): v for k, v in r.headers.items()}
        assert h.get("x-content-type-options") == "nosniff"
        assert h.get("x-frame-options", "").upper() == "DENY"
        assert "content-security-policy" in h, "no CSP header on a default response"

    def test_csp_is_strict(self, stock_client):
        """CSP must lock script execution to self and forbid inline/unsafe + framing."""
        r = stock_client.get(HEALTH)
        csp = r.headers.get("content-security-policy", "")
        assert "script-src 'self'" in csp, f"CSP missing strict script-src: {csp!r}"
        assert "frame-ancestors 'none'" in csp, f"CSP allows framing: {csp!r}"
        assert "unsafe-inline" not in csp, f"CSP permits unsafe-inline: {csp!r}"

    # ─────────────────── R3 / R7: browser & TLS launch flags ───────────────

    @pytest.mark.xfail(
        reason="build-gated: --no-sandbox stays until the container runs with an "
        "unprivileged userns or a verified seccomp profile and a docker build "
        "confirms Chromium still starts. Tracked, not yet done.",
        strict=False,
    )
    def test_no_no_sandbox_flag(self, effective_browser_args):
        """Chromium must not run with --no-sandbox by default (renderer escape)."""
        assert "--no-sandbox" not in effective_browser_args, (
            "default config launches Chromium with --no-sandbox"
        )

    def test_tls_verification_not_disabled(self, effective_browser_args):
        """TLS verification must not be disabled by default."""
        assert "--ignore-certificate-errors" not in effective_browser_args
        assert "--allow-insecure-localhost" not in effective_browser_args

    # ───────────────────────── R7: deploy posture ─────────────────────────

    def test_security_enabled_by_default(self, effective_config):
        """The security middleware block must be on out of the box."""
        assert effective_config["security"]["enabled"] is True

    def test_redis_is_not_network_exposed(self, effective_redis_url, effective_config):
        """Redis must not be open on the network: loopback host or a password.

        The container runs redis loopback-only with --requirepass (supervisord)
        and no EXPOSE (asserted in the container-posture suite); a password also
        satisfies this for an external redis.
        """
        rc = effective_config.get("redis", {})
        host = str(rc.get("host", "localhost")).lower()
        pw = rc.get("password", "") or ""
        loopback = host in ("localhost", "127.0.0.1", "::1")
        assert loopback or pw, (
            "redis is neither loopback-bound nor password-protected"
        )

    def test_trusted_hosts_not_wildcard_when_exposed(self, effective_config):
        """A wildcard trusted_hosts on a non-loopback bind silently disables the host guard."""
        host = effective_config["app"]["host"]
        trusted = effective_config["security"]["trusted_hosts"]
        exposed = host not in ("127.0.0.1", "localhost", "::1")
        assert not (exposed and trusted == ["*"]), (
            f"app binds {host} but trusted_hosts is {trusted} (host guard disabled)"
        )

    # ───────────────────── R2: dangerous features off by default ───────────

    def test_hooks_disabled_by_default(self, server_module):
        """User-supplied hook code (exec path) must be off unless explicitly enabled."""
        assert server_module.HOOKS_ENABLED is False

    def test_execute_js_disabled_by_default(self, server_module):
        """Arbitrary JS execution endpoint must be off unless explicitly enabled."""
        assert server_module.EXECUTE_JS_ENABLED is False

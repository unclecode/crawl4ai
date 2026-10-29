"""
R6 headers / CSP / CORS behavioral tests.

Security headers are emitted unconditionally (independent of security.enabled).
The strict CSP applies to the API / error surface; the still-inline dashboard /
playground keep the baseline headers but not the strict CSP until they are
externalized (CSP-compat refactor - tracked separately). CORS is deny-by-default.
"""

import pytest

pytestmark = pytest.mark.posture


class TestBaselineHeaders:
    def test_present_on_api_response(self, stock_client):
        r = stock_client.get("/health")
        h = {k.lower(): v for k, v in r.headers.items()}
        assert h.get("x-content-type-options") == "nosniff"
        assert h.get("x-frame-options", "").upper() == "DENY"
        assert h.get("referrer-policy") == "no-referrer"
        assert h.get("cross-origin-opener-policy") == "same-origin"

    def test_present_even_with_security_disabled(self, stock_client, server_module, monkeypatch):
        # Headers must be emitted independent of the security.enabled flag (the
        # old middleware only added them when enabled). Force it off and verify.
        monkeypatch.setitem(server_module.config["security"], "enabled", False)
        r = stock_client.get("/health")
        h = {k.lower() for k in r.headers}
        assert "content-security-policy" in h
        assert "x-content-type-options" in h

    def test_baseline_on_dashboard_mount(self, stock_client, server_module):
        from auth import create_access_token
        h = {"Authorization": f"Bearer {create_access_token({'sub': 'u@x.com'}, scope='admin')}"}
        r = stock_client.get("/dashboard/", headers=h)
        hh = {k.lower(): v for k, v in r.headers.items()}
        assert hh.get("x-content-type-options") == "nosniff"
        assert hh.get("x-frame-options", "").upper() == "DENY"


class TestStrictCsp:
    def test_api_csp_is_strict(self, stock_client):
        csp = stock_client.get("/health").headers.get("content-security-policy", "")
        assert "script-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "default-src 'none'" in csp
        assert "unsafe-inline" not in csp

    def test_ui_mount_not_given_strict_csp(self, stock_client, server_module):
        # The inline-script UI must not get the strict CSP yet (it would break).
        from auth import create_access_token
        h = {"Authorization": f"Bearer {create_access_token({'sub': 'u@x.com'}, scope='admin')}"}
        csp = stock_client.get("/playground/", headers=h).headers.get("content-security-policy")
        assert csp is None


class TestCorsDenyByDefault:
    def test_no_cors_allow_origin_by_default(self, stock_client):
        r = stock_client.get("/health", headers={"Origin": "https://evil.example"})
        assert "access-control-allow-origin" not in {k.lower() for k in r.headers}


class TestErrorSanitization:
    def test_5xx_is_generic_with_correlation_id(self, stock_client, server_module):
        from auth import create_access_token
        h = {"Authorization": f"Bearer {create_access_token({'sub': 'u@x.com'}, scope='admin')}"}
        # /monitor/stats/reset has no monitor singleton without a lifespan -> the
        # handler raises -> our central handler returns a sanitized 500.
        r = stock_client.post("/monitor/stats/reset", headers=h)
        assert r.status_code >= 500
        body = r.json()
        assert body.get("error") == "Internal server error"
        assert "correlation_id" in body
        # No internal detail (exception text / paths) leaked.
        assert "Traceback" not in r.text and "/home/" not in r.text

    def test_4xx_detail_preserved(self, stock_client):
        # /token is public; with no api_token configured it raises a 4xx, which
        # the central handler passes through with its developer-facing detail.
        r = stock_client.post("/token", json={"email": "x@y.com"})
        assert 400 <= r.status_code < 500
        assert "detail" in r.json() and r.json()["detail"]


class TestWebhookHeaderSanitization:
    def test_crlf_in_value_rejected(self):
        from webhook import sanitize_webhook_headers
        with pytest.raises(ValueError):
            sanitize_webhook_headers({"X-Foo": "bar\r\nInjected: 1"})

    def test_hop_by_hop_denied(self):
        from webhook import sanitize_webhook_headers
        for bad in ("Host", "Content-Length", "Transfer-Encoding", "Authorization"):
            with pytest.raises(ValueError):
                sanitize_webhook_headers({bad: "x"})

    def test_bad_name_rejected(self):
        from webhook import sanitize_webhook_headers
        with pytest.raises(ValueError):
            sanitize_webhook_headers({"X Foo": "bar"})

    def test_good_headers_pass(self):
        from webhook import sanitize_webhook_headers
        assert sanitize_webhook_headers({"X-Trace-Id": "abc123"}) == {"X-Trace-Id": "abc123"}

    def test_schema_validator_rejects_early(self):
        from schemas import WebhookConfig
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            WebhookConfig(webhook_url="https://example.com/cb",
                          webhook_headers={"Host": "evil"})


class TestCRLFSafeLogging:
    def test_crlf_stripped_from_log_message(self):
        import logging
        from utils import CRLFSafeFilter
        rec = logging.LogRecord("t", logging.INFO, __file__, 1,
                                "url=http://x/\r\nINJECTED admin login", None, None)
        CRLFSafeFilter().filter(rec)
        msg = rec.getMessage()
        assert "\r" not in msg and "\n" not in msg
        assert "INJECTED" in msg  # content kept, just de-fanged

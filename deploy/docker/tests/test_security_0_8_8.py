"""
Behavioral tests for the 0.8.8 non-breaking security patch.

Each fix here is backward-compatible: features keep working, only the unsafe
behavior is closed. (The full secure-by-default redesign is the later major.)

Covers:
  - SSRF blocklist gaps closed (NAT64 / 6to4 / :: / v4-mapped, not-is_global)
    + opaque error (no resolved IP leak)
  - output_path symlink/TOCTOU hardening (realpath containment + O_NOFOLLOW)
    with the feature kept
  - request-supplied LLM base_url ignored (key-exfil vector)
  - env:SECRET_KEY exfil gadget blocked in LLMConfig (provider keys still work)
  - CRLF-safe logging
  - webhook header sanitization
"""

import os
import socket
import sys

import pytest

DOCKER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if DOCKER_DIR not in sys.path:
    sys.path.insert(0, DOCKER_DIR)


def _patch_dns(monkeypatch, ip):
    def fake(host, port=None, *a, **k):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port or 0))]
    monkeypatch.setattr(socket, "getaddrinfo", fake)


class TestSsrfGapsClosed:
    @pytest.mark.parametrize("ip", [
        "169.254.169.254",       # metadata
        "127.0.0.1", "10.0.0.5", "192.168.1.1", "100.64.0.1",
        "::1", "::",             # v6 loopback + unspecified (was a gap)
        "::ffff:169.254.169.254",  # v4-mapped metadata
        "64:ff9b::a9fe:a9fe",    # NAT64 -> 169.254.169.254 (was a gap)
        "2002:a9fe:a9fe::1",     # 6to4 embedding 169.254.169.254 (was a gap)
    ])
    def test_internal_blocked(self, monkeypatch, ip):
        import utils
        _patch_dns(monkeypatch, ip)
        with pytest.raises(ValueError):
            utils.validate_webhook_url("http://target.example/cb")

    @pytest.mark.parametrize("ip", ["8.8.8.8", "1.1.1.1"])
    def test_public_allowed(self, monkeypatch, ip):
        import utils
        _patch_dns(monkeypatch, ip)
        utils.validate_webhook_url("http://target.example/cb")  # no raise

    def test_error_is_opaque(self, monkeypatch):
        import utils
        _patch_dns(monkeypatch, "169.254.169.254")
        with pytest.raises(ValueError) as e:
            utils.validate_webhook_url("http://target.example/")
        assert "169.254" not in str(e.value)  # no resolved-IP leak


class TestOutputPathHardening:
    def test_symlink_escape_rejected(self, monkeypatch, tmp_path):
        import utils
        allowed = tmp_path / "outputs"
        allowed.mkdir()
        monkeypatch.setattr(utils, "ALLOWED_OUTPUT_DIR", str(allowed))
        # Plant a symlinked subdir that points outside the allowed dir.
        outside = tmp_path / "outside"
        outside.mkdir()
        (allowed / "evil").symlink_to(outside)
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            utils.validate_output_path("evil/pwned.png")  # realpath escapes

    def test_normal_path_ok(self, monkeypatch, tmp_path):
        import utils
        allowed = tmp_path / "outputs"
        allowed.mkdir()
        monkeypatch.setattr(utils, "ALLOWED_OUTPUT_DIR", str(allowed))
        p = utils.validate_output_path("sub/shot.png")
        assert p.startswith(str(allowed))

    def test_write_refuses_symlink_final_component(self, monkeypatch, tmp_path):
        import utils
        allowed = tmp_path / "outputs"
        allowed.mkdir()
        target = allowed / "shot.png"
        # Pre-plant a symlink at the final path pointing at a secret.
        secret = tmp_path / "secret"
        secret.write_text("SECRET")
        target.symlink_to(secret)
        with pytest.raises(OSError):
            utils.write_output_file(str(target), b"data")  # O_NOFOLLOW refuses


class TestLlmBaseUrlIgnored:
    def test_request_base_url_not_honored_in_source(self):
        # base_url from the request must never be passed to the LLM call.
        with open(os.path.join(DOCKER_DIR, "api.py")) as f:
            src = f.read()
        assert "base_url or get_llm_base_url" not in src
        assert "base_url=get_llm_base_url(config" in src


class TestEnvSecretGuard:
    def test_env_secret_key_blocked(self):
        from crawl4ai.async_configs import LLMConfig
        with pytest.raises(ValueError):
            LLMConfig(api_token="env:SECRET_KEY")

    @pytest.mark.parametrize("name", ["REDIS_PASSWORD", "CRAWL4AI_API_TOKEN", "MY_PRIVATE_KEY"])
    def test_other_secrets_blocked(self, name):
        from crawl4ai.async_configs import LLMConfig
        with pytest.raises(ValueError):
            LLMConfig(api_token=f"env:{name}")

    def test_provider_key_still_works(self, monkeypatch):
        from crawl4ai.async_configs import LLMConfig
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-123")
        cfg = LLMConfig(provider="openai/gpt-4o-mini", api_token="env:OPENAI_API_KEY")
        assert cfg.api_token == "sk-test-123"  # normal provider key unaffected


class TestCRLFSafeLogging:
    def test_crlf_stripped(self):
        import logging
        from utils import CRLFSafeFilter
        rec = logging.LogRecord("t", logging.INFO, __file__, 1,
                                "url=http://x/\r\nINJECTED login ok", None, None)
        CRLFSafeFilter().filter(rec)
        msg = rec.getMessage()
        assert "\r" not in msg and "\n" not in msg and "INJECTED" in msg


class TestWebhookHeaderSanitization:
    def test_crlf_value_rejected(self):
        from webhook import sanitize_webhook_headers
        with pytest.raises(ValueError):
            sanitize_webhook_headers({"X-Foo": "bar\r\nInjected: 1"})

    @pytest.mark.parametrize("bad", ["Host", "Content-Length", "Authorization", "Cookie"])
    def test_hop_by_hop_denied(self, bad):
        from webhook import sanitize_webhook_headers
        with pytest.raises(ValueError):
            sanitize_webhook_headers({bad: "x"})

    def test_good_header_passes(self):
        from webhook import sanitize_webhook_headers
        assert sanitize_webhook_headers({"X-Trace-Id": "abc"}) == {"X-Trace-Id": "abc"}

    def test_schema_rejects_early(self):
        from schemas import WebhookConfig
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            WebhookConfig(webhook_url="https://example.com/cb", webhook_headers={"Host": "evil"})

"""
R2 trust-boundary behavioral tests (library-level provenance machinery).

Untrusted request bodies may only construct a strict subset of types and may
only set scalar, non-power fields, which are then clamped. Trusted (SDK /
in-process) construction is unchanged.

Docker-layer wiring tests (handlers passing UNTRUSTED, /config/dump
validate-only, declarative hooks) live alongside as the docker pieces land.
"""

import pytest

from crawl4ai.async_configs import (
    BrowserConfig,
    CrawlerRunConfig,
    Provenance,
    UntrustedConfigError,
)

T = Provenance.TRUSTED
U = Provenance.UNTRUSTED

pytestmark = pytest.mark.posture


class TestTrustedUnchanged:
    """SDK/in-process callers (default TRUSTED) keep full power."""

    def test_trusted_keeps_power_fields(self):
        c = CrawlerRunConfig.load(
            {"js_code": "x=1", "page_timeout": 999999, "word_count_threshold": 5},
            provenance=T,
        )
        assert c.js_code == "x=1"
        assert c.page_timeout == 999999

    def test_trusted_is_the_default(self):
        # No provenance argument => behaves exactly as before.
        c = CrawlerRunConfig.load({"js_code": "y=2"})
        assert c.js_code == "y=2"

    def test_trusted_roundtrip(self):
        c = CrawlerRunConfig(js_code="z=3", screenshot=True, page_timeout=120000)
        c2 = CrawlerRunConfig.load(c.dump())
        assert c2.js_code == "z=3" and c2.page_timeout == 120000


class TestUntrustedForbiddenFields:
    @pytest.mark.parametrize(
        "field,value",
        [
            ("js_code", "alert(1)"),
            ("js_code_before_wait", "x"),
            ("deep_crawl_strategy", {"type": "BFSDeepCrawlStrategy", "params": {}}),
            ("proxy_config", {"server": "http://evil"}),
            ("base_url", "http://evil"),
            ("simulate_user", True),
            ("magic", True),
            ("process_in_browser", True),
            ("session_id", "shared"),
        ],
    )
    def test_crawler_power_field_rejected(self, field, value):
        with pytest.raises(UntrustedConfigError):
            CrawlerRunConfig.load({field: value}, provenance=U)

    @pytest.mark.parametrize(
        "field,value",
        [
            ("extra_args", ["--proxy-server=http://evil"]),
            ("proxy", "http://evil"),
            ("user_data_dir", "/etc"),
            ("cdp_url", "ws://evil"),
            ("cookies", [{"name": "s", "value": "x"}]),
            ("headers", {"X": "y"}),
            ("init_scripts", ["evil()"]),
        ],
    )
    def test_browser_power_field_rejected(self, field, value):
        with pytest.raises(UntrustedConfigError):
            BrowserConfig.load({field: value}, provenance=U)

    @pytest.mark.parametrize(
        "payload",
        [
            ["--no-zygote", "--utility-cmd-prefix=sh -c id>/tmp/pwn"],
            ["--renderer-cmd-prefix=/bin/sh"],
            ["--gpu-launcher=touch /tmp/x"],
            ["--browser-subprocess-path=/bin/sh"],
        ],
    )
    def test_extra_args_chromium_cmd_injection_rejected(self, payload):
        """Y4tacker RCE: Chromium launch-arg command injection via extra_args.
        extra_args is a forbidden field for untrusted bodies, so ANY value
        (including the --*-cmd-prefix / --no-zygote exec primitives) is rejected
        outright rather than scrubbed by an always-incomplete denylist."""
        with pytest.raises(UntrustedConfigError):
            BrowserConfig.load({"extra_args": payload}, provenance=U)


class TestUntrustedTypeGate:
    def test_llm_strategy_rejected(self):
        body = {
            "type": "CrawlerRunConfig",
            "params": {
                "extraction_strategy": {
                    "type": "LLMExtractionStrategy",
                    "params": {},
                }
            },
        }
        with pytest.raises(UntrustedConfigError):
            CrawlerRunConfig.load(body, provenance=U)

    def test_env_exfil_poc_rejected(self):
        """The verified os.getenv-via-'env:' credential-exfil PoC must 400."""
        poc = {
            "type": "CrawlerRunConfig",
            "params": {
                "extraction_strategy": {
                    "type": "LLMExtractionStrategy",
                    "params": {
                        "llm_config": {
                            "type": "LLMConfig",
                            "params": {"api_token": "env:SECRET_KEY"},
                        }
                    },
                }
            },
        }
        with pytest.raises(UntrustedConfigError):
            CrawlerRunConfig.load(poc, provenance=U)

    def test_allowed_non_llm_strategy_accepted(self):
        body = {
            "type": "CrawlerRunConfig",
            "params": {
                "extraction_strategy": {
                    "type": "JsonCssExtractionStrategy",
                    "params": {"schema": {"name": "x", "baseSelector": "div", "fields": []}},
                }
            },
        }
        c = CrawlerRunConfig.load(body, provenance=U)
        assert c.extraction_strategy is not None


class TestUntrustedClampAndDrop:
    def test_timeout_zero_becomes_cap(self):
        c = CrawlerRunConfig.load({"page_timeout": 0}, provenance=U)
        assert c.page_timeout == 60_000  # 0 ("no timeout") clamped, never unbounded

    def test_timeout_clamped(self):
        c = CrawlerRunConfig.load({"wait_for_timeout": 500000}, provenance=U)
        assert c.wait_for_timeout == 60_000

    def test_unknown_field_dropped_not_raised(self):
        c = CrawlerRunConfig.load(
            {"css_selector": ".x", "totally_unknown_field": 1}, provenance=U
        )
        assert c.css_selector == ".x"

    def test_viewport_clamped(self):
        b = BrowserConfig.load({"viewport_width": 99999, "headless": True}, provenance=U)
        assert b.viewport_width == 4000
        assert b.headless is True

    def test_safe_scalar_kept(self):
        c = CrawlerRunConfig.load(
            {"word_count_threshold": 7, "screenshot": True, "wait_until": "load"},
            provenance=U,
        )
        assert c.word_count_threshold == 7 and c.screenshot is True


class TestLlmConfigGuard:
    def test_untrusted_env_token_rejected(self):
        from crawl4ai.async_configs import LLMConfig
        with pytest.raises(UntrustedConfigError):
            LLMConfig(api_token="env:SECRET_KEY", provenance=U)

    def test_untrusted_never_reads_env(self, monkeypatch):
        from crawl4ai.async_configs import LLMConfig
        monkeypatch.setenv("OPENAI_API_KEY", "leak-me")
        cfg = LLMConfig(provider="openai/gpt-4o-mini", provenance=U)
        assert cfg.api_token != "leak-me"


class TestDockerHandlersEnforceUntrusted:
    """The Docker endpoints map UntrustedConfigError -> HTTP 400 (not 500)."""

    def _auth(self, server_module):
        from auth import create_access_token
        return {"Authorization": f"Bearer {create_access_token({'sub': 'u@x.com'})}"}

    def test_crawl_rejects_js_code(self, stock_client, server_module):
        r = stock_client.post(
            "/crawl",
            json={"urls": ["https://example.com"], "crawler_config": {"js_code": "fetch('http://169.254.169.254')"}},
            headers=self._auth(server_module),
        )
        assert r.status_code == 400, r.status_code

    def test_crawl_rejects_proxy_config(self, stock_client, server_module):
        r = stock_client.post(
            "/crawl",
            json={"urls": ["https://example.com"],
                  "browser_config": {"proxy_config": {"server": "http://evil"}}},
            headers=self._auth(server_module),
        )
        assert r.status_code == 400, r.status_code

    def test_config_dump_rejects_power_field(self, stock_client, server_module):
        r = stock_client.post(
            "/config/dump",
            json={"type": "BrowserConfig", "params": {"extra_args": ["--proxy-server=x"]}},
            headers=self._auth(server_module),
        )
        assert r.status_code == 400, r.status_code

    def test_config_dump_validates_safe_config(self, stock_client, server_module):
        r = stock_client.post(
            "/config/dump",
            json={"type": "CrawlerRunConfig", "params": {"word_count_threshold": 5, "screenshot": True}},
            headers=self._auth(server_module),
        )
        assert r.status_code == 200, r.status_code

    def test_config_dump_drops_unknown_keeps_safe(self, stock_client, server_module):
        r = stock_client.post(
            "/config/dump",
            json={"type": "CrawlerRunConfig", "params": {"css_selector": ".x", "bogus_field": 1}},
            headers=self._auth(server_module),
        )
        assert r.status_code == 200, r.status_code

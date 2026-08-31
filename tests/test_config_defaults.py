"""Tests for BrowserConfig.set_defaults / CrawlerRunConfig.set_defaults."""

import pytest
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig


@pytest.fixture(autouse=True)
def _reset_defaults():
    """Ensure every test starts and ends with a clean slate."""
    BrowserConfig.reset_defaults()
    CrawlerRunConfig.reset_defaults()
    yield
    BrowserConfig.reset_defaults()
    CrawlerRunConfig.reset_defaults()


# ── Basic API ──────────────────────────────────────────────────────────


class TestBasicAPI:
    def test_set_and_get_defaults(self):
        BrowserConfig.set_defaults(headless=False, viewport_width=1920)
        d = BrowserConfig.get_defaults()
        assert d == {"headless": False, "viewport_width": 1920}

    def test_get_defaults_returns_copy(self):
        BrowserConfig.set_defaults(headers={"X-Foo": "bar"})
        d = BrowserConfig.get_defaults()
        d["headers"]["X-Foo"] = "changed"
        assert BrowserConfig.get_defaults()["headers"]["X-Foo"] == "bar"

    def test_reset_all(self):
        BrowserConfig.set_defaults(headless=False)
        BrowserConfig.reset_defaults()
        assert BrowserConfig.get_defaults() == {}

    def test_reset_selective(self):
        BrowserConfig.set_defaults(headless=False, viewport_width=1920)
        BrowserConfig.reset_defaults("headless")
        assert BrowserConfig.get_defaults() == {"viewport_width": 1920}

    def test_invalid_param_raises(self):
        with pytest.raises(ValueError, match="Invalid parameter"):
            BrowserConfig.set_defaults(not_a_real_param=42)

    def test_invalid_param_among_valid(self):
        with pytest.raises(ValueError):
            BrowserConfig.set_defaults(headless=False, bogus=True)
        # Nothing should have been stored
        assert BrowserConfig.get_defaults() == {}

    def test_set_defaults_overwrites(self):
        BrowserConfig.set_defaults(headless=False)
        BrowserConfig.set_defaults(headless=True)
        assert BrowserConfig.get_defaults()["headless"] is True

    def test_crawler_run_config_basic(self):
        CrawlerRunConfig.set_defaults(verbose=False, scan_full_page=True)
        d = CrawlerRunConfig.get_defaults()
        assert d == {"verbose": False, "scan_full_page": True}


# ── Default injection ──────────────────────────────────────────────────


class TestDefaultInjection:
    def test_browser_config_defaults_applied(self):
        BrowserConfig.set_defaults(
            headless=False,
            cache_cdp_connection=True,
            cdp_close_delay=0,
        )
        cfg = BrowserConfig()
        assert cfg.headless is False
        assert cfg.cache_cdp_connection is True
        assert cfg.cdp_close_delay == 0

    def test_crawler_run_config_defaults_applied(self):
        CrawlerRunConfig.set_defaults(verbose=False, scan_full_page=True)
        cfg = CrawlerRunConfig()
        assert cfg.verbose is False
        assert cfg.scan_full_page is True

    def test_partial_defaults(self):
        BrowserConfig.set_defaults(headless=False)
        cfg = BrowserConfig()
        assert cfg.headless is False
        # Other params keep their hardcoded defaults
        assert cfg.browser_type == "chromium"
        assert cfg.viewport_width == 1080

    def test_multiple_instances_get_defaults(self):
        BrowserConfig.set_defaults(headless=False)
        c1 = BrowserConfig()
        c2 = BrowserConfig()
        assert c1.headless is False
        assert c2.headless is False


# ── Explicit override ──────────────────────────────────────────────────


class TestExplicitOverride:
    def test_explicit_kwarg_wins(self):
        BrowserConfig.set_defaults(headless=False)
        cfg = BrowserConfig(headless=True)
        assert cfg.headless is True

    def test_explicit_same_as_default_still_wins(self):
        """Even if user passes the same value as user-default, it should be treated as explicit."""
        BrowserConfig.set_defaults(headless=False)
        cfg = BrowserConfig(headless=False)
        assert cfg.headless is False

    def test_explicit_none_wins(self):
        BrowserConfig.set_defaults(cdp_url="ws://localhost:9222")
        cfg = BrowserConfig(cdp_url=None)
        assert cfg.cdp_url is None

    def test_mixed_explicit_and_default(self):
        BrowserConfig.set_defaults(headless=False, viewport_width=1920)
        cfg = BrowserConfig(headless=True)
        assert cfg.headless is True  # explicit
        assert cfg.viewport_width == 1920  # from user default


# ── Mutable isolation ──────────────────────────────────────────────────


class TestMutableIsolation:
    def test_list_default_not_shared(self):
        BrowserConfig.set_defaults(cookies=[{"name": "a", "value": "1"}])
        c1 = BrowserConfig()
        c2 = BrowserConfig()
        c1.cookies.append({"name": "b", "value": "2"})
        assert len(c2.cookies) == 1  # c2 should be unaffected

    def test_dict_default_not_shared(self):
        BrowserConfig.set_defaults(headers={"X-Foo": "bar"})
        c1 = BrowserConfig()
        c2 = BrowserConfig()
        c1.headers["X-New"] = "val"
        assert "X-New" not in c2.headers

    def test_set_defaults_input_not_mutated(self):
        original = {"X-Foo": "bar"}
        BrowserConfig.set_defaults(headers=original)
        cfg = BrowserConfig()
        cfg.headers["X-Added"] = "val"
        assert "X-Added" not in original
        assert "X-Added" not in BrowserConfig.get_defaults()["headers"]


# ── Special processing ─────────────────────────────────────────────────


class TestSpecialProcessing:
    def test_browser_mode_builtin_sets_managed(self):
        BrowserConfig.set_defaults(browser_mode="builtin")
        cfg = BrowserConfig()
        assert cfg.use_managed_browser is True

    def test_viewport_dict_overrides_dimensions(self):
        BrowserConfig.set_defaults(viewport={"width": 1920, "height": 1080})
        cfg = BrowserConfig()
        assert cfg.viewport_width == 1920
        assert cfg.viewport_height == 1080

    def test_proxy_string_converted_to_proxy_config(self):
        BrowserConfig.set_defaults(proxy="http://user:pass@proxy:8080")
        cfg = BrowserConfig()
        assert cfg.proxy_config is not None
        assert cfg.proxy_config.server == "http://proxy:8080"

    def test_crawler_run_config_proxy_dict_converted(self):
        CrawlerRunConfig.set_defaults(
            proxy_config={"server": "http://proxy:8080"}
        )
        cfg = CrawlerRunConfig()
        from crawl4ai.async_configs import ProxyConfig
        assert isinstance(cfg.proxy_config, ProxyConfig)


# ── Clone / from_kwargs ────────────────────────────────────────────────


class TestCloneAndFromKwargs:
    def test_clone_preserves_user_default_values(self):
        BrowserConfig.set_defaults(headless=False, viewport_width=1920)
        cfg = BrowserConfig()
        cloned = cfg.clone()
        assert cloned.headless is False
        assert cloned.viewport_width == 1920

    def test_clone_with_override(self):
        BrowserConfig.set_defaults(headless=False)
        cfg = BrowserConfig()
        cloned = cfg.clone(headless=True)
        assert cloned.headless is True

    def test_from_kwargs_explicit_values(self):
        BrowserConfig.set_defaults(headless=False)
        cfg = BrowserConfig.from_kwargs({"headless": True})
        assert cfg.headless is True


# ── Dump / Load round-trip ─────────────────────────────────────────────


class TestDumpLoad:
    def test_dump_load_preserves_user_defaults(self):
        BrowserConfig.set_defaults(headless=False, viewport_width=1920)
        cfg = BrowserConfig()
        data = cfg.dump()
        loaded = BrowserConfig.load(data)
        assert loaded.headless is False
        assert loaded.viewport_width == 1920

    def test_dump_load_survives_reset(self):
        """Values should be baked into serialized data, independent of class defaults."""
        BrowserConfig.set_defaults(headless=False)
        cfg = BrowserConfig()
        data = cfg.dump()
        BrowserConfig.reset_defaults()
        loaded = BrowserConfig.load(data)
        assert loaded.headless is False

    def test_crawler_run_config_dump_load(self):
        CrawlerRunConfig.set_defaults(verbose=False, scan_full_page=True)
        cfg = CrawlerRunConfig()
        data = cfg.dump()
        CrawlerRunConfig.reset_defaults()
        loaded = CrawlerRunConfig.load(data)
        assert loaded.verbose is False
        assert loaded.scan_full_page is True

    def test_to_dict_includes_user_default_values(self):
        BrowserConfig.set_defaults(headless=False)
        cfg = BrowserConfig()
        d = cfg.to_dict()
        assert d["headless"] is False


# ── Class isolation ────────────────────────────────────────────────────


class TestClassIsolation:
    def test_browser_defaults_dont_leak_to_crawler(self):
        BrowserConfig.set_defaults(verbose=False)
        cfg = CrawlerRunConfig()
        assert cfg.verbose is True  # CrawlerRunConfig hardcoded default

    def test_crawler_defaults_dont_leak_to_browser(self):
        CrawlerRunConfig.set_defaults(verbose=False)
        cfg = BrowserConfig()
        assert cfg.verbose is True  # BrowserConfig hardcoded default

    def test_independent_reset(self):
        BrowserConfig.set_defaults(headless=False)
        CrawlerRunConfig.set_defaults(verbose=False)
        BrowserConfig.reset_defaults()
        assert BrowserConfig.get_defaults() == {}
        assert CrawlerRunConfig.get_defaults() == {"verbose": False}

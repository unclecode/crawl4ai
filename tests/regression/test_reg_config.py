"""
Regression tests for Crawl4AI configuration objects.

Covers BrowserConfig, CrawlerRunConfig, ProxyConfig, GeolocationConfig,
deep_merge logic, and serialization roundtrips.
"""

import copy
import pytest

from crawl4ai import (
    BrowserConfig,
    CrawlerRunConfig,
    ProxyConfig,
    GeolocationConfig,
    CacheMode,
)
from crawl4ai.async_configs import to_serializable_dict, from_serializable_dict


# ---------------------------------------------------------------------------
# Helper: deep_merge (copied from deploy/docker/utils.py to avoid dns dep)
# ---------------------------------------------------------------------------

def _deep_merge(base, override):
    """Recursively merge override into base dict."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# ===================================================================
# BrowserConfig
# ===================================================================

class TestBrowserConfigDefaults:
    """Verify BrowserConfig default values are sensible."""

    def test_headless_default(self):
        """Default headless should be True."""
        cfg = BrowserConfig()
        assert cfg.headless is True

    def test_browser_type_default(self):
        """Default browser_type should be 'chromium'."""
        cfg = BrowserConfig()
        assert cfg.browser_type == "chromium"

    def test_viewport_defaults(self):
        """Default viewport should be 1080x600."""
        cfg = BrowserConfig()
        assert cfg.viewport_width == 1080
        assert cfg.viewport_height == 600

    def test_javascript_enabled_default(self):
        """JavaScript should be enabled by default."""
        cfg = BrowserConfig()
        assert cfg.java_script_enabled is True

    def test_ignore_https_errors_default(self):
        """HTTPS errors should be ignored by default."""
        cfg = BrowserConfig()
        assert cfg.ignore_https_errors is True

    def test_stealth_disabled_default(self):
        """Stealth should be disabled by default."""
        cfg = BrowserConfig()
        assert cfg.enable_stealth is False

    def test_browser_mode_default(self):
        """Default browser_mode should be 'dedicated'."""
        cfg = BrowserConfig()
        assert cfg.browser_mode == "dedicated"


class TestBrowserConfigRoundtrip:
    """Verify to_dict -> from_kwargs roundtrip preserves fields."""

    def test_basic_roundtrip(self):
        """to_dict -> from_kwargs should preserve basic scalar fields."""
        original = BrowserConfig(
            headless=False,
            viewport_width=1920,
            viewport_height=1080,
            browser_type="firefox",
            text_mode=True,
        )
        d = original.to_dict()
        restored = BrowserConfig.from_kwargs(d)

        assert restored.headless is False
        assert restored.viewport_width == 1920
        assert restored.viewport_height == 1080
        assert restored.browser_type == "firefox"
        assert restored.text_mode is True

    def test_roundtrip_preserves_extra_args(self):
        """Extra args list should survive roundtrip."""
        original = BrowserConfig(extra_args=["--no-sandbox", "--disable-dev-shm-usage"])
        d = original.to_dict()
        restored = BrowserConfig.from_kwargs(d)
        assert restored.extra_args == ["--no-sandbox", "--disable-dev-shm-usage"]

    def test_roundtrip_preserves_headers(self):
        """Custom headers dict should survive roundtrip."""
        headers = {"X-Custom": "test-value", "Accept-Language": "en-US"}
        original = BrowserConfig(headers=headers)
        d = original.to_dict()
        restored = BrowserConfig.from_kwargs(d)
        assert restored.headers["X-Custom"] == "test-value"
        assert restored.headers["Accept-Language"] == "en-US"

    def test_roundtrip_preserves_cookies(self):
        """Cookies list should survive roundtrip."""
        cookies = [{"name": "session", "value": "abc123", "url": "http://example.com"}]
        original = BrowserConfig(cookies=cookies)
        d = original.to_dict()
        restored = BrowserConfig.from_kwargs(d)
        assert len(restored.cookies) == 1
        assert restored.cookies[0]["name"] == "session"


class TestBrowserConfigClone:
    """Verify clone() creates independent copy with overrides."""

    def test_clone_with_override(self):
        """Clone should apply overrides while keeping other fields."""
        original = BrowserConfig(headless=True, viewport_width=1080)
        cloned = original.clone(headless=False, viewport_width=1920)

        assert cloned.headless is False
        assert cloned.viewport_width == 1920
        # Original unchanged
        assert original.headless is True
        assert original.viewport_width == 1080

    def test_clone_independence(self):
        """Clone should produce a distinct object with same scalar values."""
        original = BrowserConfig(headless=True, viewport_width=1080)
        cloned = original.clone()
        cloned.headless = False
        cloned.viewport_width = 1920
        # Scalar mutations on clone should not affect original
        assert original.headless is True
        assert original.viewport_width == 1080

    def test_clone_preserves_unmodified(self):
        """Fields not in overrides should be preserved."""
        original = BrowserConfig(
            browser_type="firefox",
            text_mode=True,
            verbose=False,
        )
        cloned = original.clone(verbose=True)
        assert cloned.browser_type == "firefox"
        assert cloned.text_mode is True
        assert cloned.verbose is True


class TestBrowserConfigClassDefaults:
    """Verify set_defaults / get_defaults / reset_defaults class-level defaults."""

    def test_set_defaults_affects_new_instances(self):
        """set_defaults(headless=False) should make new instances headless=False."""
        try:
            BrowserConfig.set_defaults(headless=False)
            cfg = BrowserConfig()
            assert cfg.headless is False
        finally:
            BrowserConfig.reset_defaults()

    def test_explicit_arg_overrides_class_default(self):
        """Explicit constructor arg should override class-level default."""
        try:
            BrowserConfig.set_defaults(headless=False)
            cfg = BrowserConfig(headless=True)
            assert cfg.headless is True
        finally:
            BrowserConfig.reset_defaults()

    def test_get_defaults_returns_copy(self):
        """get_defaults() should return the current overrides."""
        try:
            BrowserConfig.set_defaults(viewport_width=1920)
            defaults = BrowserConfig.get_defaults()
            assert defaults["viewport_width"] == 1920
        finally:
            BrowserConfig.reset_defaults()

    def test_reset_defaults_clears_all(self):
        """reset_defaults() should clear all overrides."""
        try:
            BrowserConfig.set_defaults(headless=False, viewport_width=1920)
            BrowserConfig.reset_defaults()
            defaults = BrowserConfig.get_defaults()
            assert len(defaults) == 0
            cfg = BrowserConfig()
            assert cfg.headless is True
            assert cfg.viewport_width == 1080
        finally:
            BrowserConfig.reset_defaults()

    def test_reset_defaults_selective(self):
        """reset_defaults('headless') should only clear that one override."""
        try:
            BrowserConfig.set_defaults(headless=False, viewport_width=1920)
            BrowserConfig.reset_defaults("headless")
            cfg = BrowserConfig()
            assert cfg.headless is True  # reset to hardcoded default
            assert cfg.viewport_width == 1920  # still overridden
        finally:
            BrowserConfig.reset_defaults()

    def test_set_defaults_invalid_param_raises(self):
        """set_defaults with invalid parameter name should raise ValueError."""
        try:
            with pytest.raises(ValueError):
                BrowserConfig.set_defaults(nonexistent_param=42)
        finally:
            BrowserConfig.reset_defaults()


class TestBrowserConfigDumpLoad:
    """Verify dump() and load() serialization includes type info."""

    def test_dump_includes_type(self):
        """dump() should produce a dict with 'type' key."""
        cfg = BrowserConfig(headless=False)
        dumped = cfg.dump()
        assert isinstance(dumped, dict)
        assert dumped.get("type") == "BrowserConfig"
        assert "params" in dumped

    def test_dump_load_roundtrip(self):
        """dump() -> load() should reproduce equivalent config."""
        original = BrowserConfig(
            headless=False,
            viewport_width=1920,
            text_mode=True,
        )
        dumped = original.dump()
        restored = BrowserConfig.load(dumped)

        assert isinstance(restored, BrowserConfig)
        assert restored.headless is False
        assert restored.viewport_width == 1920
        assert restored.text_mode is True


# ===================================================================
# CrawlerRunConfig
# ===================================================================

class TestCrawlerRunConfigDefaults:
    """Verify CrawlerRunConfig default values."""

    def test_cache_mode_default(self):
        """Default cache_mode should be CacheMode.BYPASS."""
        cfg = CrawlerRunConfig()
        assert cfg.cache_mode == CacheMode.BYPASS

    def test_word_count_threshold_default(self):
        """Default word_count_threshold should match MIN_WORD_THRESHOLD (1)."""
        from crawl4ai.config import MIN_WORD_THRESHOLD
        cfg = CrawlerRunConfig()
        assert cfg.word_count_threshold == MIN_WORD_THRESHOLD

    def test_wait_until_default(self):
        """Default wait_until should be 'domcontentloaded'."""
        cfg = CrawlerRunConfig()
        assert cfg.wait_until == "domcontentloaded"

    def test_page_timeout_default(self):
        """Default page_timeout should be 60000 ms."""
        cfg = CrawlerRunConfig()
        assert cfg.page_timeout == 60000

    def test_delay_before_return_html_default(self):
        """Default delay_before_return_html should be 0.1."""
        cfg = CrawlerRunConfig()
        assert cfg.delay_before_return_html == 0.1

    def test_magic_default_false(self):
        """Magic mode should be off by default."""
        cfg = CrawlerRunConfig()
        assert cfg.magic is False

    def test_screenshot_default_false(self):
        """Screenshot should be off by default."""
        cfg = CrawlerRunConfig()
        assert cfg.screenshot is False

    def test_verbose_default_true(self):
        """Verbose should be on by default."""
        cfg = CrawlerRunConfig()
        assert cfg.verbose is True


class TestCrawlerRunConfigRoundtrip:
    """Verify to_dict -> from_kwargs roundtrip."""

    def test_basic_roundtrip(self):
        """Scalar fields should survive roundtrip."""
        original = CrawlerRunConfig(
            word_count_threshold=500,
            wait_until="load",
            page_timeout=30000,
            magic=True,
        )
        d = original.to_dict()
        restored = CrawlerRunConfig.from_kwargs(d)

        assert restored.word_count_threshold == 500
        assert restored.wait_until == "load"
        assert restored.page_timeout == 30000
        assert restored.magic is True

    def test_roundtrip_preserves_js_code(self):
        """js_code should survive roundtrip."""
        original = CrawlerRunConfig(js_code=["document.title", "console.log('hi')"])
        d = original.to_dict()
        restored = CrawlerRunConfig.from_kwargs(d)
        assert restored.js_code == ["document.title", "console.log('hi')"]

    def test_roundtrip_preserves_excluded_tags(self):
        """excluded_tags should survive roundtrip."""
        original = CrawlerRunConfig(excluded_tags=["nav", "footer", "aside"])
        d = original.to_dict()
        restored = CrawlerRunConfig.from_kwargs(d)
        assert "nav" in restored.excluded_tags
        assert "footer" in restored.excluded_tags


class TestCrawlerRunConfigClone:
    """Verify clone() with overrides."""

    def test_clone_with_override(self):
        """Clone should apply overrides while keeping other fields."""
        original = CrawlerRunConfig(magic=False, verbose=True)
        cloned = original.clone(magic=True)

        assert cloned.magic is True
        assert cloned.verbose is True
        # Original unchanged
        assert original.magic is False

    def test_clone_cache_mode_override(self):
        """Clone should be able to change cache_mode."""
        original = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
        cloned = original.clone(cache_mode=CacheMode.ENABLED)
        assert cloned.cache_mode == CacheMode.ENABLED
        assert original.cache_mode == CacheMode.BYPASS


class TestCrawlerRunConfigClassDefaults:
    """Verify set_defaults / reset_defaults for CrawlerRunConfig."""

    def test_set_defaults_affects_new_instances(self):
        """set_defaults(verbose=False) should make new instances verbose=False."""
        try:
            CrawlerRunConfig.set_defaults(verbose=False)
            cfg = CrawlerRunConfig()
            assert cfg.verbose is False
        finally:
            CrawlerRunConfig.reset_defaults()

    def test_reset_defaults_restores_original(self):
        """reset_defaults should restore hardcoded defaults."""
        try:
            CrawlerRunConfig.set_defaults(page_timeout=5000)
            CrawlerRunConfig.reset_defaults()
            cfg = CrawlerRunConfig()
            assert cfg.page_timeout == 60000
        finally:
            CrawlerRunConfig.reset_defaults()

    def test_set_defaults_invalid_param_raises(self):
        """set_defaults with invalid parameter name should raise ValueError."""
        try:
            with pytest.raises(ValueError):
                CrawlerRunConfig.set_defaults(totally_bogus=42)
        finally:
            CrawlerRunConfig.reset_defaults()


class TestCrawlerRunConfigSerialization:
    """Verify extraction_strategy and deep_crawl_strategy serialize correctly."""

    def test_dump_load_basic(self):
        """dump -> load roundtrip for basic CrawlerRunConfig."""
        original = CrawlerRunConfig(
            word_count_threshold=300,
            magic=True,
            wait_until="load",
        )
        dumped = original.dump()
        assert dumped["type"] == "CrawlerRunConfig"
        restored = CrawlerRunConfig.load(dumped)
        assert isinstance(restored, CrawlerRunConfig)
        assert restored.magic is True

    def test_dump_with_extraction_strategy(self):
        """CrawlerRunConfig with extraction_strategy should serialize."""
        try:
            from crawl4ai import JsonCssExtractionStrategy
            schema = {
                "name": "test",
                "baseSelector": "div.item",
                "fields": [{"name": "title", "selector": "h2", "type": "text"}],
            }
            strategy = JsonCssExtractionStrategy(schema)
            cfg = CrawlerRunConfig(extraction_strategy=strategy)
            dumped = cfg.dump()
            assert dumped["type"] == "CrawlerRunConfig"
            # extraction_strategy should be serialized with type info
            es_data = dumped["params"].get("extraction_strategy", {})
            assert es_data.get("type") == "JsonCssExtractionStrategy"
        except ImportError:
            pytest.skip("JsonCssExtractionStrategy not available")

    def test_dump_with_deep_crawl_strategy(self):
        """CrawlerRunConfig with deep_crawl_strategy should serialize."""
        try:
            from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
            strategy = BFSDeepCrawlStrategy(max_depth=2, max_pages=10)
            cfg = CrawlerRunConfig(deep_crawl_strategy=strategy)
            dumped = cfg.dump()
            ds_data = dumped["params"].get("deep_crawl_strategy", {})
            assert ds_data.get("type") == "BFSDeepCrawlStrategy"
        except ImportError:
            pytest.skip("BFSDeepCrawlStrategy not available")


# ===================================================================
# ProxyConfig
# ===================================================================

class TestProxyConfigFromString:
    """Verify ProxyConfig.from_string() parsing."""

    def test_simple_http_url(self):
        """from_string('http://proxy:8080') should parse server correctly."""
        pc = ProxyConfig.from_string("http://proxy:8080")
        assert pc.server == "http://proxy:8080"
        assert pc.username is None
        assert pc.password is None

    def test_http_url_with_credentials(self):
        """from_string('http://user:pass@proxy:8080') should parse credentials."""
        pc = ProxyConfig.from_string("http://user:pass@proxy:8080")
        assert pc.server == "http://proxy:8080"
        assert pc.username == "user"
        assert pc.password == "pass"

    def test_ip_port_user_pass_format(self):
        """from_string('1.2.3.4:8080:user:pass') should parse ip:port:user:pass."""
        pc = ProxyConfig.from_string("1.2.3.4:8080:user:pass")
        assert pc.server == "http://1.2.3.4:8080"
        assert pc.username == "user"
        assert pc.password == "pass"

    def test_ip_port_format(self):
        """from_string('1.2.3.4:8080') should parse ip:port without credentials."""
        pc = ProxyConfig.from_string("1.2.3.4:8080")
        assert pc.server == "http://1.2.3.4:8080"
        assert pc.username is None
        assert pc.password is None

    def test_socks5_url(self):
        """from_string('socks5://proxy:1080') should preserve socks5 scheme."""
        pc = ProxyConfig.from_string("socks5://proxy:1080")
        assert pc.server == "socks5://proxy:1080"

    def test_invalid_format_raises(self):
        """from_string with invalid format should raise ValueError."""
        with pytest.raises(ValueError):
            ProxyConfig.from_string("invalid")

    def test_password_with_colon(self):
        """Password containing a colon should be preserved via split(':', 1)."""
        # Format: http://user:complex:pass@proxy:8080
        # The @ split gives auth="http://user:complex:pass", server="proxy:8080"
        # Then protocol split gives credentials="user:complex:pass"
        # Then credentials.split(":", 1) gives user="user", password="complex:pass"
        pc = ProxyConfig.from_string("http://user:complex:pass@proxy:8080")
        assert pc.username == "user"
        assert pc.password == "complex:pass"
        assert pc.server == "http://proxy:8080"


class TestProxyConfigRoundtrip:
    """Verify to_dict -> from_dict roundtrip."""

    def test_basic_roundtrip(self):
        """to_dict -> from_dict should preserve all fields."""
        original = ProxyConfig(
            server="http://proxy:8080",
            username="user",
            password="secret",
        )
        d = original.to_dict()
        restored = ProxyConfig.from_dict(d)
        assert restored.server == original.server
        assert restored.username == original.username
        assert restored.password == original.password

    def test_roundtrip_without_credentials(self):
        """Roundtrip should work without username/password."""
        original = ProxyConfig(server="http://proxy:3128")
        d = original.to_dict()
        restored = ProxyConfig.from_dict(d)
        assert restored.server == "http://proxy:3128"
        assert restored.username is None
        assert restored.password is None


class TestProxyConfigClone:
    """Verify clone() with override."""

    def test_clone_with_server_override(self):
        """Clone should apply server override."""
        original = ProxyConfig(server="http://proxy1:8080", username="user1")
        cloned = original.clone(server="http://proxy2:9090")
        assert cloned.server == "http://proxy2:9090"
        assert cloned.username == "user1"
        # Original unchanged
        assert original.server == "http://proxy1:8080"

    def test_clone_with_credentials_override(self):
        """Clone should be able to override credentials."""
        original = ProxyConfig(server="http://proxy:8080", username="old", password="old")
        cloned = original.clone(username="new", password="new")
        assert cloned.username == "new"
        assert cloned.password == "new"
        assert original.username == "old"


class TestProxyConfigSentinel:
    """Verify ProxyConfig.DIRECT sentinel."""

    def test_direct_sentinel_exists(self):
        """ProxyConfig.DIRECT should exist and be 'direct'."""
        assert ProxyConfig.DIRECT == "direct"

    def test_direct_is_string(self):
        """DIRECT sentinel should be a string."""
        assert isinstance(ProxyConfig.DIRECT, str)


# ===================================================================
# GeolocationConfig
# ===================================================================

class TestGeolocationConfig:
    """Verify GeolocationConfig construction and roundtrip."""

    def test_constructor(self):
        """Constructor should set lat/lon/accuracy."""
        geo = GeolocationConfig(latitude=37.7749, longitude=-122.4194, accuracy=10.0)
        assert geo.latitude == 37.7749
        assert geo.longitude == -122.4194
        assert geo.accuracy == 10.0

    def test_default_accuracy(self):
        """Default accuracy should be 0.0."""
        geo = GeolocationConfig(latitude=0.0, longitude=0.0)
        assert geo.accuracy == 0.0

    def test_to_dict_from_dict_roundtrip(self):
        """to_dict -> from_dict should preserve all fields."""
        original = GeolocationConfig(latitude=48.8566, longitude=2.3522, accuracy=50.0)
        d = original.to_dict()
        restored = GeolocationConfig.from_dict(d)
        assert restored.latitude == original.latitude
        assert restored.longitude == original.longitude
        assert restored.accuracy == original.accuracy

    def test_clone_with_overrides(self):
        """Clone should apply overrides while preserving other fields."""
        original = GeolocationConfig(latitude=40.7128, longitude=-74.0060, accuracy=5.0)
        cloned = original.clone(accuracy=100.0)
        assert cloned.latitude == 40.7128
        assert cloned.longitude == -74.0060
        assert cloned.accuracy == 100.0
        # Original unchanged
        assert original.accuracy == 5.0

    def test_clone_independence(self):
        """Clone should be a fully independent object."""
        original = GeolocationConfig(latitude=0.0, longitude=0.0)
        cloned = original.clone(latitude=1.0)
        assert original.latitude == 0.0
        assert cloned.latitude == 1.0

    def test_negative_coordinates(self):
        """Negative lat/lon (southern/western hemisphere) should work."""
        geo = GeolocationConfig(latitude=-33.8688, longitude=151.2093)
        assert geo.latitude == -33.8688
        assert geo.longitude == 151.2093


# ===================================================================
# Deep merge tests
# ===================================================================

class TestDeepMerge:
    """Verify _deep_merge helper for server config merging."""

    def test_empty_override_returns_base(self):
        """Empty override should return base unchanged."""
        base = {"a": 1, "b": 2}
        result = _deep_merge(base, {})
        assert result == {"a": 1, "b": 2}

    def test_flat_key_override(self):
        """Flat key in override should replace base value."""
        base = {"a": 1, "b": 2}
        result = _deep_merge(base, {"b": 99})
        assert result == {"a": 1, "b": 99}

    def test_nested_dict_merge_preserves_siblings(self):
        """Nested dict merge should preserve sibling keys."""
        base = {"server": {"host": "localhost", "port": 8080}}
        override = {"server": {"port": 9090}}
        result = _deep_merge(base, override)
        assert result["server"]["host"] == "localhost"
        assert result["server"]["port"] == 9090

    def test_override_with_non_dict_replaces_dict(self):
        """Non-dict override should replace entire dict value."""
        base = {"server": {"host": "localhost", "port": 8080}}
        override = {"server": "http://remote:9090"}
        result = _deep_merge(base, override)
        assert result["server"] == "http://remote:9090"

    def test_deep_nesting_three_levels(self):
        """3+ levels of nesting should merge correctly."""
        base = {"a": {"b": {"c": 1, "d": 2}, "e": 3}}
        override = {"a": {"b": {"c": 99}}}
        result = _deep_merge(base, override)
        assert result["a"]["b"]["c"] == 99
        assert result["a"]["b"]["d"] == 2
        assert result["a"]["e"] == 3

    def test_new_key_in_override(self):
        """Override can add entirely new keys."""
        base = {"a": 1}
        result = _deep_merge(base, {"b": 2})
        assert result == {"a": 1, "b": 2}

    def test_base_not_mutated(self):
        """Original base dict should not be mutated."""
        base = {"a": {"b": 1}}
        override = {"a": {"b": 2}}
        _deep_merge(base, override)
        assert base["a"]["b"] == 1

    def test_empty_base(self):
        """Empty base should return override contents."""
        result = _deep_merge({}, {"a": 1, "b": {"c": 2}})
        assert result == {"a": 1, "b": {"c": 2}}


# ===================================================================
# Serialization: to_serializable_dict / from_serializable_dict
# ===================================================================

class TestSerializableDict:
    """Verify to_serializable_dict / from_serializable_dict roundtrips."""

    def test_browser_config_roundtrip(self):
        """BrowserConfig should survive serialization roundtrip."""
        original = BrowserConfig(
            headless=False,
            viewport_width=1920,
            browser_type="firefox",
        )
        serialized = to_serializable_dict(original)
        assert serialized["type"] == "BrowserConfig"
        restored = from_serializable_dict(serialized)
        assert isinstance(restored, BrowserConfig)
        assert restored.headless is False
        assert restored.viewport_width == 1920

    def test_crawler_run_config_roundtrip(self):
        """CrawlerRunConfig should survive serialization roundtrip."""
        original = CrawlerRunConfig(
            word_count_threshold=500,
            magic=True,
            wait_until="load",
        )
        serialized = to_serializable_dict(original)
        assert serialized["type"] == "CrawlerRunConfig"
        restored = from_serializable_dict(serialized)
        assert isinstance(restored, CrawlerRunConfig)
        assert restored.magic is True

    def test_crawler_run_config_with_extraction_strategy(self):
        """CrawlerRunConfig with extraction strategy should roundtrip."""
        try:
            from crawl4ai import JsonCssExtractionStrategy
            schema = {
                "name": "products",
                "baseSelector": "div.product",
                "fields": [
                    {"name": "title", "selector": "h2", "type": "text"},
                    {"name": "price", "selector": ".price", "type": "text"},
                ],
            }
            strategy = JsonCssExtractionStrategy(schema)
            original = CrawlerRunConfig(extraction_strategy=strategy)
            serialized = to_serializable_dict(original)
            restored = from_serializable_dict(serialized)
            assert isinstance(restored, CrawlerRunConfig)
            assert isinstance(restored.extraction_strategy, JsonCssExtractionStrategy)
        except ImportError:
            pytest.skip("JsonCssExtractionStrategy not available")

    def test_none_value(self):
        """None should serialize to None."""
        assert to_serializable_dict(None) is None

    def test_basic_types_passthrough(self):
        """Strings, ints, floats, bools should pass through unchanged."""
        assert to_serializable_dict("hello") == "hello"
        assert to_serializable_dict(42) == 42
        assert to_serializable_dict(3.14) == 3.14
        assert to_serializable_dict(True) is True

    def test_enum_serialization(self):
        """CacheMode enum should serialize with type info."""
        serialized = to_serializable_dict(CacheMode.ENABLED)
        assert serialized["type"] == "CacheMode"
        assert serialized["params"] == "enabled"
        restored = from_serializable_dict(serialized)
        assert restored == CacheMode.ENABLED

    def test_list_serialization(self):
        """Lists should serialize element-by-element."""
        result = to_serializable_dict([1, "two", 3.0])
        assert result == [1, "two", 3.0]

    def test_dict_serialization(self):
        """Plain dicts should be wrapped with type='dict'."""
        result = to_serializable_dict({"key": "value"})
        assert result["type"] == "dict"
        assert result["value"]["key"] == "value"

    def test_disallowed_type_returns_none(self):
        """Deserializing a non-allowlisted type should return None (not instantiate it)."""
        bad_data = {"type": "os.system", "params": {"command": "rm -rf /"}}
        result = from_serializable_dict(bad_data)
        assert result is None

    def test_geolocation_config_roundtrip(self):
        """GeolocationConfig should survive serialization roundtrip."""
        original = GeolocationConfig(latitude=37.7749, longitude=-122.4194, accuracy=10.0)
        serialized = to_serializable_dict(original)
        assert serialized["type"] == "GeolocationConfig"
        restored = from_serializable_dict(serialized)
        assert isinstance(restored, GeolocationConfig)
        assert restored.latitude == 37.7749

    def test_proxy_config_roundtrip(self):
        """ProxyConfig should survive serialization roundtrip."""
        original = ProxyConfig(server="http://proxy:8080", username="user", password="pass")
        serialized = to_serializable_dict(original)
        assert serialized["type"] == "ProxyConfig"
        restored = from_serializable_dict(serialized)
        assert isinstance(restored, ProxyConfig)
        assert restored.server == "http://proxy:8080"
        assert restored.username == "user"

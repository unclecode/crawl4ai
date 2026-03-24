"""Unit tests for BrowserConfig avoid_ads / avoid_css flags.

Tests the config plumbing: defaults, serialization, cloning, roundtrips.
No browser or network required.
"""

import pytest
from crawl4ai.async_configs import BrowserConfig


@pytest.fixture(autouse=True)
def _reset_defaults():
    """Ensure clean slate for each test."""
    BrowserConfig.reset_defaults()
    yield
    BrowserConfig.reset_defaults()


class TestResourceFilteringDefaults:
    """Both flags must default to False (opt-in only)."""

    def test_default_values_are_false(self):
        config = BrowserConfig()
        assert config.avoid_ads is False
        assert config.avoid_css is False

    def test_custom_values(self):
        config = BrowserConfig(avoid_ads=True, avoid_css=True)
        assert config.avoid_ads is True
        assert config.avoid_css is True

    def test_mixed_values(self):
        c1 = BrowserConfig(avoid_ads=True, avoid_css=False)
        assert c1.avoid_ads is True
        assert c1.avoid_css is False

        c2 = BrowserConfig(avoid_ads=False, avoid_css=True)
        assert c2.avoid_ads is False
        assert c2.avoid_css is True


class TestResourceFilteringSerialization:
    """Flags must survive to_dict / from_kwargs / dump / load roundtrips."""

    def test_to_dict_includes_flags(self):
        config = BrowserConfig(avoid_ads=True, avoid_css=True)
        d = config.to_dict()
        assert "avoid_ads" in d
        assert "avoid_css" in d
        assert d["avoid_ads"] is True
        assert d["avoid_css"] is True

    def test_to_dict_includes_false_values(self):
        config = BrowserConfig()
        d = config.to_dict()
        assert d["avoid_ads"] is False
        assert d["avoid_css"] is False

    def test_from_kwargs_roundtrip(self):
        original = BrowserConfig(avoid_ads=True, avoid_css=False)
        d = original.to_dict()
        restored = BrowserConfig.from_kwargs(d)
        assert restored.avoid_ads is True
        assert restored.avoid_css is False

    def test_from_kwargs_with_true_values(self):
        restored = BrowserConfig.from_kwargs({"avoid_ads": True, "avoid_css": True})
        assert restored.avoid_ads is True
        assert restored.avoid_css is True

    def test_dump_load_roundtrip(self):
        original = BrowserConfig(avoid_ads=True, avoid_css=True)
        dumped = original.dump()
        restored = BrowserConfig.load(dumped)
        assert restored.avoid_ads is True
        assert restored.avoid_css is True


class TestResourceFilteringClone:
    """clone() must preserve flags and allow overrides."""

    def test_clone_preserves_flags(self):
        config = BrowserConfig(avoid_ads=True, avoid_css=True)
        cloned = config.clone()
        assert cloned.avoid_ads is True
        assert cloned.avoid_css is True

    def test_clone_allows_override(self):
        config = BrowserConfig(avoid_ads=True, avoid_css=False)
        cloned = config.clone(avoid_css=True)
        assert cloned.avoid_ads is True
        assert cloned.avoid_css is True
        # original unchanged
        assert config.avoid_css is False

    def test_clone_can_disable_flag(self):
        config = BrowserConfig(avoid_ads=True, avoid_css=True)
        cloned = config.clone(avoid_ads=False)
        assert cloned.avoid_ads is False
        assert cloned.avoid_css is True

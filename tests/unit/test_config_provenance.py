"""Untrusted config provenance gate.

Regression test for the {"type": "dict", "value": <typed object>} laundering
bypass: wrapping a forbidden typed object in a plain-dict envelope hid it from
the type gate, and from_kwargs then re-deserialized it as TRUSTED, which
resolves api_token="env:NAME" through os.getenv.
"""
import pytest

from crawl4ai.async_configs import (
    BrowserConfig,
    CrawlerRunConfig,
    Provenance,
    UntrustedConfigError,
)

UNTRUSTED = Provenance.UNTRUSTED


def _llm_strategy(env_var):
    return {
        "type": "LLMExtractionStrategy",
        "params": {
            "llm_config": {
                "type": "dict",
                "value": {"type": "LLMConfig", "params": {"api_token": f"env:{env_var}"}},
            }
        },
    }


def test_forbidden_type_refused_directly():
    data = {"type": "CrawlerRunConfig", "params": {"extraction_strategy": _llm_strategy("SECRET_KEY")}}
    with pytest.raises(UntrustedConfigError):
        CrawlerRunConfig.load(data, provenance=UNTRUSTED)


def test_forbidden_type_refused_when_wrapped(monkeypatch):
    """The bypass: the whole strategy hidden behind {"type":"dict","value":...}."""
    monkeypatch.setenv("SECRET_KEY", "canary-secret-key-value")
    data = {
        "type": "CrawlerRunConfig",
        "extraction_strategy": {"type": "dict", "value": _llm_strategy("SECRET_KEY")},
    }
    with pytest.raises(UntrustedConfigError):
        CrawlerRunConfig.load(data, provenance=UNTRUSTED)


def test_forbidden_type_refused_when_wrapped_in_params(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-canary-9f3a")
    data = {
        "type": "CrawlerRunConfig",
        "params": {"extraction_strategy": {"type": "dict", "value": _llm_strategy("OPENAI_API_KEY")}},
    }
    with pytest.raises(UntrustedConfigError):
        CrawlerRunConfig.load(data, provenance=UNTRUSTED)


def test_browser_config_wrapped_proxy_refused():
    """Same envelope, other config class, other forbidden type."""
    data = {
        "type": "BrowserConfig",
        "params": {
            "proxy_config": {
                "type": "dict",
                "value": {"type": "ProxyConfig", "params": {"server": "http://evil:8080"}},
            }
        },
    }
    with pytest.raises(UntrustedConfigError):
        BrowserConfig.load(data, provenance=UNTRUSTED)


def test_trusted_load_is_unchanged(monkeypatch):
    """TRUSTED (SDK) callers keep the old behavior: no raise, and the wrapped
    envelope still unwraps to the same plain dict it did before the fix."""
    monkeypatch.setenv("CRAWL4AI_TEST_TOKEN", "tok-123")
    cfg = CrawlerRunConfig.load(
        {"type": "CrawlerRunConfig", "params": {"extraction_strategy": _llm_strategy("CRAWL4AI_TEST_TOKEN")}}
    )
    assert cfg.extraction_strategy.llm_config == {
        "type": "LLMConfig",
        "params": {"api_token": "env:CRAWL4AI_TEST_TOKEN"},
    }


def test_trusted_top_level_kwargs_still_deserialize(monkeypatch):
    """from_kwargs still builds typed objects for TRUSTED callers."""
    monkeypatch.setenv("CRAWL4AI_TEST_TOKEN", "tok-123")
    cfg = CrawlerRunConfig.load(
        {
            "type": "CrawlerRunConfig",
            "extraction_strategy": {"type": "dict", "value": _llm_strategy("CRAWL4AI_TEST_TOKEN")},
        }
    )
    assert cfg.extraction_strategy.llm_config.api_token == "tok-123"


def test_untrusted_delay_fields_are_capped():
    """delay_before_return_html / mean_delay / max_range are seconds held on a
    live browser page or used as a rate-limiter base delay. Unclamped, an
    untrusted body can hold a page (or a whole arun_many batch) open forever."""
    cfg = CrawlerRunConfig.load(
        {
            "type": "CrawlerRunConfig",
            "params": {
                "delay_before_return_html": 1e9,
                "mean_delay": 1e9,
                "max_range": 1e9,
            },
        },
        provenance=UNTRUSTED,
    )
    assert cfg.delay_before_return_html <= 60
    assert cfg.mean_delay <= 60
    assert cfg.max_range <= 60


def test_untrusted_delay_fields_negative_or_non_numeric_fall_back_to_default():
    cfg = CrawlerRunConfig.load(
        {
            "type": "CrawlerRunConfig",
            "params": {
                "delay_before_return_html": -5,
                "mean_delay": "not-a-number",
                "max_range": None,
            },
        },
        provenance=UNTRUSTED,
    )
    assert cfg.delay_before_return_html == 0.1
    assert cfg.mean_delay == 0.1
    assert cfg.max_range == 0.3


def test_trusted_delay_fields_are_not_clamped():
    """TRUSTED (SDK) callers keep the old behavior: no cap applied."""
    cfg = CrawlerRunConfig.load(
        {
            "type": "CrawlerRunConfig",
            "params": {
                "delay_before_return_html": 1e9,
                "mean_delay": 1e9,
                "max_range": 1e9,
            },
        }
    )
    assert cfg.delay_before_return_html == 1e9
    assert cfg.mean_delay == 1e9
    assert cfg.max_range == 1e9


def test_plain_business_dict_with_type_key_still_passes():
    """A JsonCss schema carries "type" keys but is data, not a typed object."""
    schema = {
        "name": "Items",
        "baseSelector": ".item",
        "fields": [{"name": "title", "selector": "h1", "type": "text"}],
    }
    cfg = CrawlerRunConfig.load(
        {
            "type": "CrawlerRunConfig",
            "params": {
                "extraction_strategy": {
                    "type": "JsonCssExtractionStrategy",
                    "params": {"schema": {"type": "dict", "value": schema}},
                }
            },
        },
        provenance=UNTRUSTED,
    )
    assert cfg.extraction_strategy.schema["baseSelector"] == ".item"

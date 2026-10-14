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


def _deep_crawl(**params):
    return {
        "type": "CrawlerRunConfig",
        "params": {"deep_crawl_strategy": {"type": "BFSDeepCrawlStrategy", "params": {"max_depth": 2, **params}}},
    }


def test_deep_crawl_allowed_with_opt_in(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_ALLOW_DEEP_CRAWL", "true")
    chain = {"type": "FilterChain", "params": {"filters": [
        {"type": "URLPatternFilter", "params": {"patterns": ["*/blog/*"]}}]}}
    cfg = CrawlerRunConfig.load(_deep_crawl(filter_chain=chain, max_pages=50), provenance=UNTRUSTED)
    assert type(cfg.deep_crawl_strategy).__name__ == "BFSDeepCrawlStrategy"
    assert cfg.deep_crawl_strategy.max_pages == 50


@pytest.mark.parametrize("pattern", ["^(a+)+$", "tag*x"])
def test_deep_crawl_unsafe_pattern_refused(monkeypatch, pattern):
    monkeypatch.setenv("CRAWL4AI_ALLOW_DEEP_CRAWL", "true")
    chain = {"type": "FilterChain", "params": {"filters": [
        {"type": "URLPatternFilter", "params": {"patterns": [pattern]}}]}}
    with pytest.raises(UntrustedConfigError, match="URLPatternFilter"):
        CrawlerRunConfig.load(_deep_crawl(filter_chain=chain), provenance=UNTRUSTED)


def test_deep_crawl_resume_state_refused(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_ALLOW_DEEP_CRAWL", "true")
    data = _deep_crawl(resume_state={"pending": [{"url": "http://169.254.169.254/", "depth": 1}]})
    with pytest.raises(UntrustedConfigError, match="resume_state"):
        CrawlerRunConfig.load(data, provenance=UNTRUSTED)


def test_deep_crawl_ssl_certificate_refused(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_ALLOW_DEEP_CRAWL", "true")
    data = _deep_crawl()
    data["params"]["fetch_ssl_certificate"] = True
    with pytest.raises(UntrustedConfigError, match="fetch_ssl_certificate"):
        CrawlerRunConfig.load(data, provenance=UNTRUSTED)


def _pattern_chain(*sizes):
    return {"type": "FilterChain", "params": {"filters": [
        {"type": "URLPatternFilter", "params": {"patterns": [f"*/p{i}/*" for i in range(n)]}}
        for n in sizes]}}


@pytest.mark.parametrize("strategy, match", [
    ({"filter_chain": _pattern_chain(101)}, "limited to 100 items"),
    ({"filter_chain": _pattern_chain(*(1,) * 20)}, "in total"),
    ({"filter_chain": _pattern_chain(100, 100, 1)}, "in total"),
    ({"url_scorer": {"type": "KeywordRelevanceScorer", "params": {
        "keywords": {"type": "dict", "value": {f"k{i}": 1 for i in range(201)}}}}}, "in total"),
])
def test_deep_crawl_size_budget_refused(monkeypatch, strategy, match):
    monkeypatch.setenv("CRAWL4AI_ALLOW_DEEP_CRAWL", "true")
    with pytest.raises(UntrustedConfigError, match=match):
        CrawlerRunConfig.load(_deep_crawl(**strategy), provenance=UNTRUSTED)


def test_deep_crawl_nested_composite_scorer_refused(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_ALLOW_DEEP_CRAWL", "true")
    inner = {"type": "CompositeScorer", "params": {"scorers": [{"type": "PathDepthScorer", "params": {}}]}}
    data = _deep_crawl(url_scorer={"type": "CompositeScorer", "params": {"scorers": [inner]}})
    with pytest.raises(UntrustedConfigError, match="nested"):
        CrawlerRunConfig.load(data, provenance=UNTRUSTED)


def test_url_pattern_star_led_glob_is_linear_and_unchanged():
    import time
    from crawl4ai.deep_crawling.filters import URLPatternFilter

    f = URLPatternFilter(["*/blog/*"])
    assert f.apply("https://x.com/blog/post")
    assert not f.apply("https://x.com/news/post")
    start = time.time()
    assert not f.apply("https://x.com/" + "a" * 50000)
    assert time.time() - start < 0.5


def test_cache_mode_string_is_converted_and_invalid_one_refused():
    from crawl4ai import CacheMode

    cfg = CrawlerRunConfig.load(
        {"type": "CrawlerRunConfig", "params": {"cache_mode": "Enabled"}}, provenance=UNTRUSTED
    )
    assert cfg.cache_mode == CacheMode.ENABLED
    # A bad value must be a 400 (UntrustedConfigError), not a ValueError (500).
    with pytest.raises(UntrustedConfigError, match="cache_mode"):
        CrawlerRunConfig.load(
            {"type": "CrawlerRunConfig", "params": {"cache_mode": "nope"}}, provenance=UNTRUSTED
        )

"""Allowlisted untrusted fields that reached code, model-load or regex sinks.

Three 0.9.5 reports, one gate (crawl4ai/async_configs.py): a field the
untrusted gate let through by name still carried code (wait_for "js:..."), a
HuggingFace repo id (CosineStrategy.model_name), or a regex that backtracks
for hours with the GIL held (RegexExtractionStrategy.custom,
RegexChunking.patterns, schema fields of type "regex").

No browser, no network, no model download: everything here is the gate.
"""
import pytest

from crawl4ai.async_configs import CrawlerRunConfig, Provenance, UntrustedConfigError


def _load(params, provenance=Provenance.UNTRUSTED):
    return CrawlerRunConfig.load(
        {"type": "CrawlerRunConfig", "params": params}, provenance=provenance
    )


# ── wait_for ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "value",
    [
        "js:() => { fetch('http://x/'); return true; }",
        "() => { fetch('http://x/'); return true; }",
        "function () { return true; }",
    ],
)
def test_untrusted_wait_for_javascript_refused(value):
    with pytest.raises(UntrustedConfigError):
        _load({"wait_for": value})


def test_untrusted_bare_wait_for_is_pinned_to_css():
    """A bare value used to fall back to JS when it was not a valid selector."""
    assert _load({"wait_for": "fetch('http://x/'); return true;"}).wait_for == (
        "css:fetch('http://x/'); return true;"
    )
    assert _load({"wait_for": "#main"}).wait_for == "css:#main"
    assert _load({"wait_for": "css:#main"}).wait_for == "css:#main"


def test_trusted_wait_for_unchanged():
    value = "js:() => true"
    assert _load({"wait_for": value}, Provenance.TRUSTED).wait_for == value

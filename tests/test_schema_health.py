"""Serve-time health checking for generated extraction schemas.

A schema is validated once, against the snapshot it was generated from, and then applied
for months while the site keeps changing. When a selector stops matching, extraction does
not raise: it returns fewer records, or records with a silently empty column. These tests
pin both shapes of that failure and the report that now names them.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from crawl4ai.extraction_strategy import (  # noqa: E402
    JsonCssExtractionStrategy,
    JsonElementExtractionStrategy,
)

SCHEMA = {
    "name": "Products",
    "baseSelector": "article.product",
    "fields": [
        {"name": "title", "selector": "h3", "type": "text"},
        {"name": "price", "selector": "p.price", "type": "text"},
    ],
}

PAGE = """
<html><body>
  <article class="product"><h3>First</h3><p class="price">10</p></article>
  <article class="product"><h3>Second</h3><p class="price">20</p></article>
</body></html>
"""

# The two shapes a redesign takes.
PAGE_CONTAINER_RENAMED = PAGE.replace('class="product"', 'class="product-card"')
PAGE_FIELD_RENAMED = PAGE.replace('class="price"', 'class="product-price"')


def test_off_by_default_and_silent():
    """No threshold: behaviour is exactly as before, including on a broken page."""
    strategy = JsonCssExtractionStrategy(schema=SCHEMA)
    assert len(strategy.extract(url="", html_content=PAGE)) == 2
    assert strategy.extract(url="", html_content=PAGE_CONTAINER_RENAMED) == []


def test_healthy_page_reports_nothing():
    seen = []
    strategy = JsonCssExtractionStrategy(
        schema=SCHEMA, health_threshold=0.9, on_degraded=seen.append)
    results = strategy.extract(url="http://x/", html_content=PAGE)
    assert len(results) == 2
    assert seen == []


def test_container_renamed_is_reported():
    """The obvious rot: nothing matches, the result is empty."""
    seen = []
    strategy = JsonCssExtractionStrategy(
        schema=SCHEMA, health_threshold=0.9, on_degraded=seen.append)
    results = strategy.extract(url="http://x/", html_content=PAGE_CONTAINER_RENAMED)
    assert results == []
    assert len(seen) == 1
    assert seen[0]["records"] == 0
    assert seen[0]["coverage"] == 0.0
    assert seen[0]["url"] == "http://x/"


def test_field_renamed_is_reported_although_record_count_is_unchanged():
    """The dangerous rot: the same number of records, one column silently empty."""
    seen = []
    strategy = JsonCssExtractionStrategy(
        schema=SCHEMA, health_threshold=0.9, on_degraded=seen.append)
    results = strategy.extract(url="http://x/", html_content=PAGE_FIELD_RENAMED)
    assert len(results) == 2, "the count is unchanged - this is why it goes unnoticed"
    assert all("price" not in r or not r["price"] for r in results)
    assert len(seen) == 1
    assert seen[0]["empty_fields"] == ["price"]
    assert seen[0]["coverage"] == pytest.approx(0.5)


def test_threshold_is_respected():
    """Half the fields populated passes at 0.5 and fails at 0.6."""
    lenient, strict = [], []
    JsonCssExtractionStrategy(schema=SCHEMA, health_threshold=0.5,
                             on_degraded=lenient.append
                             ).extract(url="", html_content=PAGE_FIELD_RENAMED)
    JsonCssExtractionStrategy(schema=SCHEMA, health_threshold=0.6,
                             on_degraded=strict.append
                             ).extract(url="", html_content=PAGE_FIELD_RENAMED)
    assert lenient == []
    assert len(strict) == 1


def test_default_reporter_warns_without_a_callback(capsys):
    JsonCssExtractionStrategy(schema=SCHEMA, health_threshold=0.9).extract(
        url="http://x/", html_content=PAGE_FIELD_RENAMED)
    err = capsys.readouterr().err
    assert "looks stale" in err
    assert "price" in err


# --- regeneration -----------------------------------------------------------------
# The generator is stubbed: these pin the POLICY around regeneration - when it fires,
# what it accepts, what it refuses, how often - which is what can go wrong without a
# model being involved.

REPAIRED = {
    "name": "Products",
    "baseSelector": "article.product",
    "fields": [
        {"name": "title", "selector": "h3", "type": "text"},
        {"name": "price", "selector": "p.product-price", "type": "text"},
    ],
}
USELESS = dict(REPAIRED, fields=[{"name": "title", "selector": "h3", "type": "text"},
                                 {"name": "price", "selector": "p.gone", "type": "text"}])


@pytest.fixture
def stub_generator(monkeypatch):
    calls = []

    def make(schema_to_return):
        def fake(**kwargs):
            calls.append(kwargs)
            return schema_to_return
        monkeypatch.setattr(JsonElementExtractionStrategy, "generate_schema",
                            staticmethod(fake))
        return calls
    return make


def test_heal_adopts_a_schema_that_actually_fixes_the_page(stub_generator):
    calls = stub_generator(REPAIRED)
    seen = []
    strategy = JsonCssExtractionStrategy(
        schema=dict(SCHEMA), health_threshold=0.9, on_degraded=seen.append,
        heal_llm_config=object())
    results = strategy.extract(url="http://x/", html_content=PAGE_FIELD_RENAMED)
    assert len(calls) == 1, "one regeneration, from the page that degraded"
    assert all(r.get("price") for r in results), "the served records are the healed ones"
    assert strategy.schema == REPAIRED, "and the strategy keeps the new schema"
    assert seen[0]["heal"]["outcome"] == "schema regenerated and adopted"
    assert seen[0]["heal"]["coverage_before"] == pytest.approx(0.5)
    assert seen[0]["heal"]["coverage_after"] == pytest.approx(1.0)


def test_heal_refuses_a_replacement_that_is_no_better(stub_generator):
    stub_generator(USELESS)
    seen = []
    original = dict(SCHEMA)
    strategy = JsonCssExtractionStrategy(
        schema=dict(SCHEMA), health_threshold=0.9, on_degraded=seen.append,
        heal_llm_config=object())
    strategy.extract(url="http://x/", html_content=PAGE_FIELD_RENAMED)
    assert strategy.schema == original, "a repair that does not repair is discarded"
    assert "no better" in seen[0]["heal"]["outcome"]


def test_heal_carries_the_field_names_into_the_request(stub_generator):
    calls = stub_generator(REPAIRED)
    JsonCssExtractionStrategy(
        schema=dict(SCHEMA), health_threshold=0.9, heal_llm_config=object()
    ).extract(url="http://x/", html_content=PAGE_FIELD_RENAMED)
    example = calls[0]["target_json_example"]
    assert "title" in example and "price" in example, (
        "downstream is keyed on the field names - a repair may not rename a column")


def test_heal_is_bounded(stub_generator):
    calls = stub_generator(USELESS)
    strategy = JsonCssExtractionStrategy(
        schema=dict(SCHEMA), health_threshold=0.9, heal_llm_config=object(),
        max_regenerations=1)
    for _ in range(5):
        strategy.extract(url="http://x/", html_content=PAGE_FIELD_RENAMED)
    assert len(calls) == 1, "a permanently unreadable site must not bill per page"


def test_heal_failure_does_not_break_the_crawl(monkeypatch):
    def boom(**kwargs):
        raise RuntimeError("provider is down")
    monkeypatch.setattr(JsonElementExtractionStrategy, "generate_schema",
                        staticmethod(boom))
    seen = []
    strategy = JsonCssExtractionStrategy(
        schema=dict(SCHEMA), health_threshold=0.9, on_degraded=seen.append,
        heal_llm_config=object())
    results = strategy.extract(url="http://x/", html_content=PAGE_FIELD_RENAMED)
    assert len(results) == 2, "the original records are still served"
    assert "regeneration failed" in seen[0]["heal"]["outcome"]


def test_no_heal_config_means_no_generation(stub_generator):
    calls = stub_generator(REPAIRED)
    JsonCssExtractionStrategy(schema=dict(SCHEMA), health_threshold=0.9).extract(
        url="http://x/", html_content=PAGE_FIELD_RENAMED)
    assert calls == [], "reporting stays available without opting into model calls"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))

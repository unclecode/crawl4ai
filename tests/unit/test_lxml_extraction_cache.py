"""Selector compilation may be cached, but matches belong to one document."""

import asyncio

import pytest

from crawl4ai import JsonLxmlExtractionStrategy

SCHEMA = {
    "baseSelector": "article",
    "fields": [
        {"name": "title", "selector": "h1", "type": "text", "default": "missing"}
    ],
}


def extract(strategy, method, content):
    """Exercise both public synchronous entry points without a crawler."""
    if method == "run":
        return strategy.run("https://example.invalid/", [content])
    return strategy.extract("https://example.invalid/", content)


@pytest.mark.parametrize("method", ["extract", "run"])
@pytest.mark.parametrize("use_caching", [True, False])
@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ('<article id="content"><h1>Second title</h1></article>', "Second title"),
        ('<article id="content"><p>No heading</p></article>', "missing"),
    ],
)
def test_reused_strategy_extracts_current_document(
    method, use_caching, content, expected
):
    """A reused component ID must not keep its previous field matches."""
    strategy = JsonLxmlExtractionStrategy(SCHEMA, use_caching=use_caching)
    first = '<article id="content"><h1>First title</h1></article>'

    assert extract(strategy, method, first) == [{"title": "First title"}]
    assert extract(strategy, method, content) == [{"title": expected}]


@pytest.mark.parametrize("method", ["extract", "run"])
def test_reused_root_id_selects_current_base_elements(method):
    """An HTML root ID must not reuse the previous document's base elements."""
    strategy = JsonLxmlExtractionStrategy(SCHEMA)
    first = '<html id="page"><body><article><h1>First</h1></article></body></html>'
    second = '<html id="page"><body><article><h1>Second</h1></article></body></html>'

    assert extract(strategy, method, first) == [{"title": "First"}]
    assert extract(strategy, method, second) == [{"title": "Second"}]


@pytest.mark.parametrize("use_caching", [True, False])
def test_duplicate_ids_within_document_keep_distinct_records(use_caching):
    """Repeated IDs in imperfect HTML must not duplicate another record's fields."""
    strategy = JsonLxmlExtractionStrategy(SCHEMA, use_caching=use_caching)
    content = (
        '<article id="content"><h1>First</h1></article>'
        '<article id="content"><h1>Second</h1></article>'
    )

    assert strategy.extract("https://example.invalid/", content) == [
        {"title": "First"},
        {"title": "Second"},
    ]


@pytest.mark.parametrize("use_caching", [True, False])
def test_compiled_selectors_are_reused(use_caching):
    """Document-specific matches do not prevent reusing compiled selectors."""
    strategy = JsonLxmlExtractionStrategy(SCHEMA, use_caching=use_caching)
    content = '<article id="content"><h1>Title</h1></article>'

    assert strategy.extract("https://example.invalid/", content) == [{"title": "Title"}]
    selectors = dict(strategy._selector_cache)
    assert set(selectors) == {"article", "h1"}
    assert strategy.extract("https://example.invalid/", content) == [{"title": "Title"}]
    assert all(
        strategy._selector_cache[key] is value for key, value in selectors.items()
    )


def test_shared_arun_strategy_keeps_documents_independent():
    """The public threaded async path must not share matches between documents."""
    strategy = JsonLxmlExtractionStrategy(SCHEMA)
    first = '<article id="content"><h1>First</h1></article>'
    assert strategy.extract("https://example.invalid/", first) == [{"title": "First"}]

    async def run_documents():
        return await asyncio.gather(
            *(
                strategy.arun(
                    f"https://example.invalid/{index}",
                    [f'<article id="content"><h1>Title {index}</h1></article>'],
                )
                for index in range(8)
            )
        )

    assert asyncio.run(run_documents()) == [
        [{"title": f"Title {index}"}] for index in range(8)
    ]

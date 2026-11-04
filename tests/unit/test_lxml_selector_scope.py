"""Public-API regression for CSS scope preservation; no browser required."""

import pytest

from crawl4ai import JsonCssExtractionStrategy, JsonLxmlExtractionStrategy

HTML = """<html><body>
<aside><h2 class="name">Outside catalog</h2></aside>
<div id="catalog"><div class="product"><h2 class="name">Inside catalog</h2></div></div>
</body></html>"""


@pytest.mark.parametrize("method", ["extract", "run"])
@pytest.mark.parametrize("location", ["baseSelector", "field selector"])
@pytest.mark.parametrize(
    "mode", ["lxml default", "lxml enabled", "lxml disabled", "css"]
)
def test_complex_selector_keeps_scope(method, location, mode):
    selector = "#catalog > .product > .name"
    if location == "baseSelector":
        schema = {
            "baseSelector": selector,
            "fields": [{"name": "name", "type": "text"}],
        }
    else:
        schema = {
            "baseSelector": "body",
            "fields": [{"name": "name", "selector": selector, "type": "text"}],
        }

    # Fresh instance for every case, so no cross-document result cache is involved.
    if mode == "css":
        strategy = JsonCssExtractionStrategy(schema)
    elif mode == "lxml default":
        strategy = JsonLxmlExtractionStrategy(schema)
    else:
        strategy = JsonLxmlExtractionStrategy(
            schema, optimize_common_patterns=mode == "lxml enabled"
        )

    content = [HTML] if method == "run" else HTML
    result = getattr(strategy, method)("https://example.test/catalog", content)
    assert result == [{"name": "Inside catalog"}]


@pytest.mark.parametrize(
    "selector, html, expected",
    [
        pytest.param(
            ".catalog .list .product .name",
            '<aside><h2 class="name">Outside catalog</h2></aside>'
            '<div class="catalog"><section class="list"><div class="product">'
            '<h2 class="name">Inside catalog</h2></div></section></div>',
            [{"name": "Inside catalog"}],
            id="descendant",
        ),
        pytest.param(
            ".anchor + .product .name",
            '<aside><h2 class="name">Outside catalog</h2></aside>'
            '<div class="anchor"></div><div class="product">'
            '<h2 class="name">Inside catalog</h2></div>',
            [{"name": "Inside catalog"}],
            id="adjacent-sibling",
        ),
        pytest.param(
            ".anchor ~ .product .name",
            '<aside><h2 class="name">Outside catalog</h2></aside>'
            '<div class="anchor"></div><hr><div class="product">'
            '<h2 class="name">Inside catalog</h2></div>',
            [{"name": "Inside catalog"}],
            id="general-sibling",
        ),
        pytest.param(
            '#catalog > .product > .name[data-kind="title"]',
            HTML.replace('class="name"', 'class="name" data-kind="title"'),
            [{"name": "Inside catalog"}],
            id="class-with-attribute",
        ),
        pytest.param(
            "#catalog > .product > .name:first-child",
            HTML,
            [{"name": "Inside catalog"}],
            id="class-with-pseudo",
        ),
        pytest.param(
            '#catalog > .product > #outside[data-kind="title"]',
            HTML.replace(
                '<aside><h2 class="name">', '<aside><h2 id="outside" data-kind="title">'
            ),
            [],
            id="id-with-attribute-outside-scope",
        ),
        pytest.param(
            "#catalog > .product > h2.name",
            HTML.replace("</h2>", "</h2><p>Other text</p>"),
            [{"name": "Inside catalog"}],
            id="keep-final-tag-selector",
        ),
        pytest.param(
            ".name",
            HTML,
            [{"name": "Outside catalog"}, {"name": "Inside catalog"}],
            id="simple-selector-control",
        ),
    ],
)
def test_base_selector_preserves_css_semantics(selector, html, expected):
    schema = {
        "baseSelector": selector,
        "fields": [{"name": "name", "type": "text"}],
    }
    # Base selection does not use field-selector fallbacks. The no-match case
    # therefore exercises only the scope-changing optimization fixed here.
    for strategy in (
        JsonLxmlExtractionStrategy(schema),
        JsonCssExtractionStrategy(schema),
    ):
        assert strategy.extract("https://example.test/catalog", html) == expected

"""Regression: JsonCssExtractionStrategy must preserve whitespace
around inline children when extracting text fields.

Without ``separator=" "``, ``element.get_text(strip=True)`` strips
each child text node and concatenates them with no separator,
turning ``<span>foo <b>bar</b> baz</span>`` into ``"foobarbaz"``.
"""

from crawl4ai.extraction_strategy import JsonCssExtractionStrategy


HTML = """\
<html><body>
  <ul>
    <li class="item"><span class="name">Wireless <b>Logitech</b> Mouse M325</span></li>
    <li class="item"><span class="name">USB-C <strong>Anker</strong> Hub</span></li>
    <li class="item"><span class="name">No inline tags here</span></li>
  </ul>
</body></html>
"""

SCHEMA = {
    "baseSelector": "body",
    "fields": [
        {
            "name": "items",
            "type": "list",
            "selector": "ul li.item",
            "fields": [
                {"name": "name", "selector": "span.name", "type": "text"},
            ],
        }
    ],
}


def test_jsoncss_preserves_spaces_around_inline_tags() -> None:
    [record] = JsonCssExtractionStrategy(SCHEMA).extract(url="x", html_content=HTML)
    names = [item["name"] for item in record["items"]]

    assert names == [
        "Wireless Logitech Mouse M325",
        "USB-C Anker Hub",
        "No inline tags here",
    ]

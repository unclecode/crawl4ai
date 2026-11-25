import pytest

from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


@pytest.mark.parametrize(
    ("margin", "spaces"),
    [("36pt", 2), ("36.5pt", 2), ("72.5px", 4), ("0", 0), ("auto", 0)],
)
def test_google_doc_list_margin_preserves_document(margin, spaces):
    html = (
        f'<h1>Agenda</h1><ol><li style="margin-left:{margin}">Minutes</li></ol>'
        "<p>Adjourned.</p>"
    )
    result = DefaultMarkdownGenerator(options={"google_doc": True}).generate_markdown(html)
    assert [line.rstrip() for line in result.raw_markdown.splitlines()] == [
        "# Agenda", " " * spaces + "1. Minutes", "Adjourned."
    ]

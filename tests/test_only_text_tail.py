import pytest
from lxml import html as lhtml

from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ("Alpha<sup>1</sup>Beta", "Alpha1Beta"),
        ("<b>Bold</b>, <i>italics</i> and prose.", "Bold, italics and prose."),
        (
            "Keep <b>bold <em>inner</em> end</b> tail.",
            "Keep bold inner end tail.",
        ),
        ("<i>Adjacent</i><b>words</b>", "Adjacentwords"),
        ("<b>End</b>", "End"),
        ("Plain text.", "Plain text."),
    ],
)
def test_only_text_preserves_full_paragraph_text(body, expected):
    result = LXMLWebScrapingStrategy().scrap(
        "https://example.com/", f"<p>{body}</p>", only_text=True
    )

    assert result.success
    paragraph = lhtml.fromstring(result.cleaned_html).xpath("//p")[0]
    assert paragraph.text_content() == expected
    assert not paragraph.xpath(".//b | .//em | .//i | .//sup")


def test_default_scraping_preserves_inline_markup_and_tail():
    result = LXMLWebScrapingStrategy().scrap(
        "https://example.com/", "<p>Alpha<sup>1</sup>Beta</p>"
    )

    assert result.success
    paragraph = lhtml.fromstring(result.cleaned_html).xpath("//p")[0]
    assert paragraph.text_content() == "Alpha1Beta"
    assert paragraph.find("sup").tail == "Beta"

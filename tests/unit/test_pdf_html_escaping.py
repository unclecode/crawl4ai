"""Regression test for GHSA-7g3g-vhm6-79f3.

PDF paragraph text is attacker-controlled and flows verbatim into cleaned_html
(clean_pdf_text_to_html -> pdf_page.html -> cleaned_html -> crawl JSON). It must
be HTML-escaped so injected markup cannot execute when the result is rendered.

The escaping was disabled at the paragraph sink; every other sink in the
function already escaped. These tests pin the paragraph sink specifically and
assert the advisory's acceptance criterion: < > " ' survive only as entities.
"""

import pytest

from crawl4ai.processors.pdf.utils import clean_pdf_text_to_html


# A leading short line becomes an <h2> title (its own escaped path); the blank
# line then starts a fresh paragraph, which is the sink under test.
TITLE = "Quarterly Financial Report\n\n"


def _paragraph_html(body: str) -> str:
    return clean_pdf_text_to_html(2, TITLE + body)


def test_event_handler_markup_does_not_survive_as_live_html():
    payload = "<img src=x onerror=alert(document.cookie)>"
    body = f"Attackers embed {payload} inside pdf paragraph body text that an operator later views in the playground here."

    html = _paragraph_html(body)

    assert "<img" not in html, "raw <img tag reached cleaned_html (XSS)"
    assert "&lt;img" in html, "payload should appear escaped"
    # The event handler must not survive in a live tag context.
    assert "onerror=alert" not in html or "&lt;img" in html


def test_svg_onload_with_quotes_is_escaped():
    payload = "\"><svg onload='steal()'>"
    body = f"A crafted string {payload} placed in the paragraph flow of the document body for testing purposes here now."

    html = _paragraph_html(body)

    assert "<svg" not in html
    assert "&lt;svg" in html


@pytest.mark.parametrize(
    "char, entity",
    [("<", "&lt;"), (">", "&gt;"), ('"', "&quot;"), ("'", "&#x27;")],
)
def test_dangerous_chars_appear_only_as_entities(char, entity):
    body = (
        f"Paragraph body text containing a raw {char} character that must be "
        f"escaped before it reaches cleaned html output for safety reasons here."
    )

    html = _paragraph_html(body)
    paragraph = html.split('<div class="paragraph">', 1)[1]

    assert entity in paragraph, f"{char!r} should be emitted as {entity}"
    # The only literal angle brackets/quotes allowed in the paragraph region are
    # the ones this code emits itself (<p>, </p>, <div>, <hr/>). The injected
    # char must not appear raw inside the text.
    text = paragraph.replace("<p>", "").replace("</p>", "")
    text = text.replace('<div class="paragraph">', "").replace("</div><hr/>", "")
    assert char not in text, f"raw {char!r} survived into paragraph text"


def test_benign_paragraph_text_is_unchanged():
    body = "An ordinary paragraph of report text with no special characters at all in it whatsoever today."

    html = _paragraph_html(body)

    assert "ordinary paragraph of report text" in html
    assert "&lt;" not in html and "&amp;" not in html

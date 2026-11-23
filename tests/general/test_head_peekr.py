"""HeadPeekr must report the document head only, exactly as it was sent."""

import pytest

from crawl4ai.utils import _head_section_of


def test_head_ends_at_its_close_tag():
    content = b"<html><head><title>x</title></head><body>b</body></html>"
    assert _head_section_of(content) == b"<html><head><title>x</title></head>"


@pytest.mark.parametrize(
    "close_tag",
    [b"</head>", b"</HEAD>", b"</Head >", b"</head\n>"],
)
def test_close_tag_is_case_and_whitespace_insensitive(close_tag):
    content = b"<html><head><title>x</title>" + close_tag + b"<body>b</body>"
    assert _head_section_of(content) == b"<html><head><title>x</title>" + close_tag


def test_page_without_head_is_returned_unchanged():
    # Regression: a synthetic </head> used to be appended, so the whole body
    # was read back as head metadata.
    content = b"<html><body><p>no head element</p></body></html>"
    assert _head_section_of(content) == content


def test_only_the_first_head_is_taken():
    content = b"<head><meta charset='utf-8'></head><head><title>late</title></head>"
    assert _head_section_of(content) == b"<head><meta charset='utf-8'></head>"

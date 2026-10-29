"""Standard metadata names are ASCII case-insensitive in HTML."""

import pytest

from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy


def scrape(head):
    html = (
        "<html><head><title>Keep title</title>"
        f"{head}</head><body><p>Meaningful article content remains here.</p>"
        "</body></html>"
    )
    result = LXMLWebScrapingStrategy().scrap("https://example.test/article", html)
    assert result.success
    assert result.metadata["title"] == "Keep title"
    return result.metadata


@pytest.mark.parametrize("field", ["description", "keywords", "author"])
@pytest.mark.parametrize("name_case", ["mixed", "upper", "lower"])
def test_standard_metadata_names(field, name_case):
    name = {"mixed": field.title(), "upper": field.upper(), "lower": field}[name_case]
    content = "  Preserve MiXeD CASE and Café 中文  "
    metadata = scrape(f'<meta name="{name}" content="{content}">')
    assert metadata[field] == content.strip()


def test_missing_metadata_fields():
    metadata = scrape("")
    assert {
        field: metadata[field] for field in ["description", "keywords", "author"]
    } == {"description": None, "keywords": None, "author": None}


@pytest.mark.parametrize("name", ["Keywords", "keywordſ", "x-description"])
def test_nonstandard_names_remain_unmatched(name):
    metadata = scrape(f'<meta name="{name}" content="Must not match">')
    assert metadata["description"] is None
    assert metadata["keywords"] is None
    assert metadata["author"] is None


def test_duplicate_lowercase_names_keep_first_content():
    metadata = scrape(
        '<meta name="description" content="First VALUE">'
        '<meta name="description" content="Second value">'
    )
    assert metadata["description"] == "First VALUE"


def test_other_metadata_is_preserved():
    metadata = scrape(
        '<meta property="og:description" content="OG Summary">'
        '<meta name="twitter:description" content="Twitter Summary">'
        '<meta property="article:author" content="Article Author">'
    )
    assert metadata["og:description"] == "OG Summary"
    assert metadata["twitter:description"] == "Twitter Summary"
    assert metadata["article:author"] == "Article Author"
    assert metadata["description"] is None
    assert metadata["author"] is None


@pytest.mark.parametrize("field", ["description", "keywords", "author"])
@pytest.mark.parametrize("first_upper", [False, True])
def test_duplicate_mixed_case_names_keep_first_content(field, first_upper):
    first, second = (field.upper(), field) if first_upper else (field, field.upper())
    metadata = scrape(
        f'<meta name="{first}" content="First VALUE">'
        f'<meta name="{second}" content="Second value">'
    )
    assert metadata[field] == "First VALUE"


@pytest.mark.parametrize("field", ["description", "keywords", "author"])
@pytest.mark.parametrize("name_case", ["lower", "upper"])
def test_missing_content_is_skipped(field, name_case):
    name = field if name_case == "lower" else field.upper()
    metadata = scrape(
        f'<meta name="{name}">' f'<meta name="{name}" content="Available VALUE">'
    )
    assert metadata[field] == "Available VALUE"


@pytest.mark.parametrize("field", ["description", "keywords", "author"])
def test_no_content_attribute_remains_none(field):
    metadata = scrape(f'<meta name="{field}">')
    assert metadata[field] is None


@pytest.mark.parametrize("field", ["description", "keywords", "author"])
def test_empty_content_remains_first_value(field):
    metadata = scrape(
        f'<meta name="{field}" content="">'
        f'<meta name="{field}" content="Second value">'
    )
    assert metadata[field] == ""


def test_social_names_keep_existing_case_matching():
    metadata = scrape(
        '<meta property="OG:description" content="Upper OG">'
        '<meta name="Twitter:description" content="Mixed Twitter">'
        '<meta property="Article:author" content="Mixed Article">'
    )
    assert "OG:description" not in metadata
    assert "Twitter:description" not in metadata
    assert "Article:author" not in metadata


@pytest.mark.parametrize(
    "head, expected",
    [
        ('<meta property="og:title" content="OpenGraph Title">', "OpenGraph Title"),
        ('<meta name="twitter:title" content="Twitter Title">', "Twitter Title"),
    ],
)
def test_existing_social_title_fallback_is_unchanged(head, expected):
    html = f"<html><head>{head}</head><body><p>Article text is here.</p></body></html>"
    result = LXMLWebScrapingStrategy().scrap("https://example.test/article", html)
    assert result.success
    assert result.metadata["title"] == expected

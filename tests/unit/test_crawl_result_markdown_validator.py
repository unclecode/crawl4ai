from crawl4ai.models import CrawlResult


def test_crawl_result_converts_markdown_dict_input():
    result = CrawlResult(
        url="https://example.com",
        html="<html></html>",
        success=True,
        markdown={
            "raw_markdown": "# Hello",
            "markdown_with_citations": "# Hello",
            "references_markdown": "",
            "fit_markdown": "Hello",
            "fit_html": "<p>Hello</p>",
        },
    )

    assert result.markdown is not None
    assert result.markdown.raw_markdown == "# Hello"
    assert str(result.markdown) == "# Hello"
    assert "Hello" in result.markdown
    assert result.model_dump()["markdown"]["raw_markdown"] == "# Hello"

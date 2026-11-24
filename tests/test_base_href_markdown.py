"""A relative <base href> must be resolved against the page URL in markdown links (#2550).

Before the fix, ``<base href="/sub/">`` gave markdown links like ``/sub/page.html``,
with no scheme or host.
"""

import asyncio

import pytest

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

PAGE_URL = "https://example.com/app/index.html"


def _page(base_href):
    head = f"<base href='{base_href}'>" if base_href else ""
    return (
        f"<html><head>{head}</head>"
        "<body><p>Read the <a href='page.html'>page</a> for more text here.</p></body></html>"
    )


CASES = [
    ("/sub/", "https://example.com/sub/page.html"),
    ("sub/", "https://example.com/app/sub/page.html"),
    ("https://cdn.example.com/docs/", "https://cdn.example.com/docs/page.html"),
    (None, "https://example.com/app/page.html"),
]


@pytest.mark.parametrize("base_href, expected", CASES)
@pytest.mark.parametrize("content_source", ["cleaned_html", "raw_html"])
def test_markdown_links_use_resolved_base(base_href, expected, content_source):
    async def run():
        crawler = AsyncWebCrawler()
        config = CrawlerRunConfig(
            markdown_generator=DefaultMarkdownGenerator(content_source=content_source)
        )
        return await crawler.aprocess_html(
            url=PAGE_URL,
            html=_page(base_href),
            extracted_content=None,
            config=config,
            screenshot_data=None,
            pdf_data=None,
            verbose=False,
        )

    result = asyncio.run(run())
    assert f"[page]({expected})" in result.markdown.raw_markdown
    assert f"⟨1⟩ {expected}:" in result.markdown.references_markdown

"""
A link that fails to crawl must not be marked as crawled in place of another
link from the same batch.
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from crawl4ai import AdaptiveConfig
from crawl4ai.adaptive_crawler import AdaptiveCrawler
from crawl4ai.models import CrawlResult

START = "https://site.test/"
HEAD_DATA = {"title": "page", "meta": {}}


class FakeCrawler:
    """The start page links to /a, which fails, and /b, which succeeds."""

    async def arun(self, url, config=None):
        markdown = {
            "raw_markdown": f"content for {url} python",
            "markdown_with_citations": "",
            "references_markdown": "",
            "fit_markdown": "",
            "fit_html": "",
        }
        if url == START:
            links = {
                "internal": [
                    {"href": START + "a", "text": "python a", "head_data": HEAD_DATA},
                    {"href": START + "b", "text": "python b", "head_data": HEAD_DATA},
                ],
                "external": [],
            }
            return CrawlResult(
                url=url, html="", success=True, markdown=markdown, links=links
            )
        if url.endswith("/a"):
            return CrawlResult(url=url, html="", success=False, error_message="boom")
        return CrawlResult(url=url, html="", success=True, markdown=markdown)


def test_failed_link_is_not_marked_crawled():
    config = AdaptiveConfig(
        max_depth=2,
        top_k_links=2,
        max_pages=10,
        confidence_threshold=1.0,
        min_gain_threshold=0.0,
        saturation_threshold=2.0,
    )
    crawler = AdaptiveCrawler(crawler=FakeCrawler(), config=config)

    state = asyncio.run(crawler.digest(START, "python"))

    assert START + "b" in state.crawled_urls
    assert START + "a" not in state.crawled_urls
    kb_urls = [result.url for result in state.knowledge_base]
    assert kb_urls.count(START + "b") == 1

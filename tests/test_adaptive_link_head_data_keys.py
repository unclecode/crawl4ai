"""Adaptive-crawler link ranking must read <head> data with the right keys.

``AsyncUrlSeeder._parse_head`` returns ``{"title": ..., "meta": {...}, ...}``
(see ``_extract_text_context``, which reads it that way), but the statistical
strategy looked the title up under ``head_data["meta"]["title"]`` and the
description/keywords under ``head_data["description"]``/``["keywords"]``. Every
such lookup was empty, so a link whose only match was its page title scored 0
relevance and a link whose only new terms were in its meta description got the
"unknown novelty" fallback.
"""

from crawl4ai.adaptive_crawler import CrawlState, StatisticalStrategy
from crawl4ai.async_url_seeder import _parse_head
from crawl4ai.models import Link


def _state(query: str) -> CrawlState:
    return CrawlState(query=query)


def test_relevance_sees_page_title():
    head = _parse_head("<html><head><title>Asyncio tutorial</title></head></html>")
    link = Link(href="https://example.com/a", head_data=head)

    assert StatisticalStrategy()._calculate_relevance(link, _state("asyncio tutorial")) == 1.0


def test_novelty_sees_meta_description_and_keywords():
    head = _parse_head(
        '<html><head><meta name="description" content="asyncio tutorial">'
        '<meta name="keywords" content="event loop"></head></html>'
    )
    link = Link(href="https://example.com/b", head_data=head)

    state = _state("asyncio tutorial")
    # Non-empty knowledge base so novelty is not short-circuited to 1.0.
    state.knowledge_base = [object()]
    state.term_frequencies["unrelated"] = 1

    assert StatisticalStrategy()._calculate_novelty(link, state) == 1.0

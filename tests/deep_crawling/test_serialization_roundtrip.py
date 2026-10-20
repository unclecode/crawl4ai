"""Deep-crawl filters and scorers survive CrawlerRunConfig.dump()/load().

to_serializable_dict() rebuilds an object from attributes named after its
constructor arguments. Filters and scorers that kept those arguments only in
private slots lost them: a DomainFilter came back allowing every domain, and
KeywordRelevanceScorer, DomainAuthorityScorer and CompositeScorer could not be
loaded at all.
"""

import asyncio
import json

import pytest

from crawl4ai import CrawlerRunConfig
from crawl4ai.async_configs import from_serializable_dict, to_serializable_dict
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy, BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import (
    ContentTypeFilter,
    DomainFilter,
    FilterChain,
    URLPatternFilter,
)
from crawl4ai.deep_crawling.scorers import (
    CompositeScorer,
    DomainAuthorityScorer,
    FreshnessScorer,
    KeywordRelevanceScorer,
    PathDepthScorer,
)

URLS = [
    "https://docs.example.com/guide/api/2025/index.html",
    "https://ads.example.com/banner",
    "https://evil.example.net/page.pdf",
    "https://python.org/a/b/c/d",
    "https://Docs.Example.com/API",
    "https://blog.example.com/2019/old-post",
]


def round_trip(obj):
    return from_serializable_dict(json.loads(json.dumps(to_serializable_dict(obj))))


@pytest.mark.parametrize(
    "url_filter",
    [
        DomainFilter(allowed_domains=["docs.example.com"]),
        DomainFilter(blocked_domains=["ads.example.com", "evil.example.net"]),
        ContentTypeFilter(allowed_types=["text/html"], check_extension=False),
        URLPatternFilter(patterns=["*docs*"], reverse=True),
    ],
    ids=lambda f: type(f).__name__,
)
def test_filters_behave_the_same_after_a_round_trip(url_filter):
    back = round_trip(url_filter)
    assert type(back) is type(url_filter)
    assert [back.apply(u) for u in URLS] == [url_filter.apply(u) for u in URLS]


@pytest.mark.parametrize(
    "scorer",
    [
        KeywordRelevanceScorer(keywords=["API", "Guide"], weight=0.5),
        KeywordRelevanceScorer(keywords=["API"], case_sensitive=True),
        PathDepthScorer(optimal_depth=1, weight=0.5),
        FreshnessScorer(weight=0.5, current_year=2026),
        DomainAuthorityScorer(
            domain_weights={"python.org": 0.9}, default_weight=0.1, weight=0.5
        ),
        CompositeScorer(
            scorers=[
                PathDepthScorer(optimal_depth=1),
                FreshnessScorer(current_year=2026),
            ],
            normalize=False,
        ),
    ],
    ids=lambda s: type(s).__name__,
)
def test_scorers_behave_the_same_after_a_round_trip(scorer):
    back = round_trip(scorer)
    assert type(back) is type(scorer)
    assert [back.score(u) for u in URLS] == pytest.approx(
        [scorer.score(u) for u in URLS]
    )


def test_domain_restriction_survives_crawler_run_config_dump_and_load():
    cfg = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=2,
            filter_chain=FilterChain(
                [DomainFilter(allowed_domains=["docs.example.com"])]
            ),
        )
    )
    back = CrawlerRunConfig.load(json.loads(json.dumps(cfg.dump())))
    chain = back.deep_crawl_strategy.filter_chain
    assert asyncio.run(chain.apply("https://evil.example.net/page")) is False
    assert asyncio.run(chain.apply("https://docs.example.com/page")) is True


def test_best_first_scorer_with_required_arguments_loads():
    cfg = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=2,
            url_scorer=KeywordRelevanceScorer(keywords=["api", "guide"], weight=0.7),
        )
    )
    back = CrawlerRunConfig.load(json.loads(json.dumps(cfg.dump())))
    assert back.deep_crawl_strategy.url_scorer.keywords == ["api", "guide"]

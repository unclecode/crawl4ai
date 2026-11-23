"""Regression tests for the mutable-default-argument bug in deep-crawl strategy
constructors: filter_chain defaulted to a single FilterChain() instance shared
across every strategy created without an explicit filter_chain=, leaking
FilterChain.stats counters and add_filter() mutations across unrelated
strategy instances.
"""

from crawl4ai.deep_crawling.bff_strategy import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.bfs_strategy import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.dfs_strategy import DFSDeepCrawlStrategy


def test_bfs_strategy_instances_get_independent_default_filter_chains():
    a = BFSDeepCrawlStrategy(max_depth=2)
    b = BFSDeepCrawlStrategy(max_depth=3)
    assert a.filter_chain is not b.filter_chain


def test_dfs_strategy_instances_get_independent_default_filter_chains():
    a = DFSDeepCrawlStrategy(max_depth=2)
    b = DFSDeepCrawlStrategy(max_depth=3)
    assert a.filter_chain is not b.filter_chain


def test_best_first_strategy_instances_get_independent_default_filter_chains():
    a = BestFirstCrawlingStrategy(max_depth=2)
    b = BestFirstCrawlingStrategy(max_depth=3)
    assert a.filter_chain is not b.filter_chain


def test_adding_a_filter_to_one_default_chain_does_not_leak_to_another_instance():
    a = BFSDeepCrawlStrategy(max_depth=2)
    b = BFSDeepCrawlStrategy(max_depth=3)

    class _DummyFilter:
        def apply(self, url):
            return True

    a.filter_chain.add_filter(_DummyFilter())

    assert len(a.filter_chain.filters) == 1
    assert len(b.filter_chain.filters) == 0

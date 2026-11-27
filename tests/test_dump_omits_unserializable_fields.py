"""dump() leaves out fields whose value cannot be serialized.

to_serializable_dict() turns objects that cannot be deserialized (a Logger, a
callable) into None but still wrote the field, so a deep crawl strategy dumped
as {"logger": null}. The server forbids `logger` on deep crawl strategies from
an untrusted request even when it is null, so every deep crawl sent with
CrawlerRunConfig.dump(), e.g. by Crawl4aiDockerClient, was rejected with a 400.
"""

import json

from crawl4ai import CrawlerRunConfig
from crawl4ai.async_configs import Provenance, to_serializable_dict
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, DFSDeepCrawlStrategy


async def _on_state_change(state):
    pass


def test_strategy_dump_has_no_logger_or_callback_fields():
    strategy = BFSDeepCrawlStrategy(max_depth=2, on_state_change=_on_state_change)
    params = to_serializable_dict(strategy)["params"]

    assert "logger" not in params
    assert "on_state_change" not in params
    assert params["max_depth"] == 2


def test_deep_crawl_dump_passes_the_untrusted_load(monkeypatch):
    monkeypatch.setenv("CRAWL4AI_ALLOW_DEEP_CRAWL", "true")
    for strategy in (
        BFSDeepCrawlStrategy(max_depth=1),
        DFSDeepCrawlStrategy(max_depth=1),
    ):
        cfg = CrawlerRunConfig(deep_crawl_strategy=strategy)
        payload = json.loads(json.dumps(cfg.dump()))

        back = CrawlerRunConfig.load(payload, provenance=Provenance.UNTRUSTED)

        assert type(back.deep_crawl_strategy) is type(strategy)
        assert back.deep_crawl_strategy.max_depth == 1


def test_a_field_explicitly_set_to_none_is_still_written():
    # Only objects the serializer skips are left out; a real None value stays.
    cfg = CrawlerRunConfig(wait_until=None)
    assert cfg.dump()["params"]["wait_until"] is None


def test_dfs_strategy_keeps_its_arguments():
    # DFSDeepCrawlStrategy.__init__ only forwards *args/**kwargs, so its
    # arguments are read back through the BFS signature.
    serialized = to_serializable_dict(DFSDeepCrawlStrategy(max_depth=3, max_pages=7))

    assert serialized == {
        "type": "DFSDeepCrawlStrategy",
        "params": {"max_depth": 3, "max_pages": 7},
    }

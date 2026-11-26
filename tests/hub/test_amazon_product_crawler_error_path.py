"""The amazon_product hub crawler must return its JSON error payload when ``run`` fails.

The error path calls ``json.dumps`` but the module did not import ``json``, so a
failure inside ``run`` raised ``NameError`` instead of returning the error payload.
"""

import asyncio
import json

from crawl4ai.crawlers.amazon_product.crawler import AmazonProductCrawler


def test_run_returns_json_error_payload_on_failure():
    crawler = AmazonProductCrawler()
    crawler.meta = {"version": "test"}

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    crawler.logger.info = boom

    payload = json.loads(asyncio.run(crawler.run("https://amazon.com/test")))

    assert payload == {"error": "boom", "metadata": {"version": "test"}}

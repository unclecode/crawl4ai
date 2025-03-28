# test.py
import json
import sys
from pathlib import Path

import pytest

from crawl4ai import CrawlerHub


@pytest.mark.asyncio
async def test_amazon():
    crawler_cls = CrawlerHub.get("amazon_product")
    assert crawler_cls is not None

    crawler = crawler_cls()
    print(f"Crawler version: {crawler.meta['version']}")
    print(f"Rate limits: {crawler.meta.get('rate_limit', 'Unlimited')}")
    print(await crawler.run("https://amazon.com/test"))


@pytest.mark.asyncio
@pytest.mark.skip("crawler not implemented doesn't pass llm_config to generate_schema")
async def test_google(tmp_path: Path):
    # Get crawler dynamically
    crawler_cls = CrawlerHub.get("google_search")
    assert crawler_cls is not None
    crawler = crawler_cls()

    # Text search
    schema_cache_path: Path = tmp_path / ".crawl4ai"
    text_results = await crawler.run(
        query="apple inc",
        search_type="text",
        schema_cache_path=schema_cache_path.as_posix(),
    )
    print(json.dumps(json.loads(text_results), indent=4))

    # Image search
    # image_results = await crawler.run(query="apple inc", search_type="image")
    # print(image_results)


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", "-v", str(__file__)]))

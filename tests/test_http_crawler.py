import asyncio
import unittest
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, HTTPCrawlerConfig
from crawl4ai.async_crawler_strategy import AsyncHTTPCrawlerStrategy

class TestHttpCrawler(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        http_crawler_config = HTTPCrawlerConfig(
            method="GET",
            headers={"User-Agent": "MyCustomBot/1.0"},
            follow_redirects=True,
            verify_ssl=True,
        )
        self._crawler = AsyncWebCrawler(
            crawler_strategy=AsyncHTTPCrawlerStrategy(
                browser_config=http_crawler_config
            )
        )
        await self._crawler.start()

    async def asyncTearDown(self):
        await self._crawler.close()
        await asyncio.sleep(0.250)

    async def test_run_many_without_stream(self):
        config = CrawlerRunConfig(stream=False)
        results = await self._crawler.arun_many(["https://example.com"] * 3, config=config)
        for result in results:
            self.assertTrue(result.success)

    async def test_run_many_with_stream(self):
        config = CrawlerRunConfig(stream=True)
        async for result in await self._crawler.arun_many(["https://example.com"] * 3, config=config):
            self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()

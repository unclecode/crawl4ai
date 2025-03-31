import os
import sys
import unittest

import pytest

from crawl4ai import CacheMode
from crawl4ai.async_configs import LLMConfig
from crawl4ai.chunking_strategy import (
    FixedLengthWordChunking,
    RegexChunking,
    SlidingWindowChunking,
    TopicSegmentationChunking,
)
from crawl4ai.extraction_strategy import (
    CosineStrategy,
    LLMExtractionStrategy,
    NoExtractionStrategy,
)
from crawl4ai.legacy.web_crawler import WebCrawler


class TestWebCrawler(unittest.TestCase):
    def setUp(self):
        self.crawler = WebCrawler()

    def test_warmup(self):
        self.crawler.warmup()
        self.assertTrue(self.crawler.ready, "WebCrawler failed to warm up")

    def test_run_default_strategies(self):
        result = self.crawler.run(
            url="https://www.nbcnews.com/business",
            word_count_threshold=5,
            chunking_strategy=RegexChunking(),
            extraction_strategy=CosineStrategy(),
            cache_mode=CacheMode.BYPASS,
            warmup=False,
        )
        self.assertTrue(
            result.success, "Failed to crawl and extract using default strategies"
        )

    def test_run_different_strategies(self):
        if not os.getenv("OPENAI_API_KEY"):
            self.skipTest("Skipping env OPENAI_API_KEY not set")
        url = "https://www.nbcnews.com/business"

        # Test with FixedLengthWordChunking and LLMExtractionStrategy
        result = self.crawler.run(
            url=url,
            word_count_threshold=5,
            chunking_strategy=FixedLengthWordChunking(chunk_size=100),
            extraction_strategy=LLMExtractionStrategy(
                llm_config=LLMConfig(provider="openai/gpt-3.5-turbo", api_token=os.getenv("OPENAI_API_KEY"))
            ),
            cache_mode=CacheMode.BYPASS,
            warmup=False
        )
        self.assertTrue(
            result.success,
            "Failed to crawl and extract with FixedLengthWordChunking and LLMExtractionStrategy",
        )

        # Test with SlidingWindowChunking and TopicExtractionStrategy
        result = self.crawler.run(
            url=url,
            word_count_threshold=5,
            chunking_strategy=TopicSegmentationChunking(
                window_size=100, step=50, num_keywords=5
            ),
            cache_mode=CacheMode.BYPASS,
            warmup=False,
        )
        self.assertTrue(
            result.success,
            "Failed to crawl and extract with SlidingWindowChunking and TopicExtractionStrategy",
        )

    def test_invalid_url(self):
        result = self.crawler.run(
            url="invalid_url", cache_mode=CacheMode.BYPASS, warmup=False
        )
        self.assertFalse(result.success, "Extraction should fail with invalid URL")
        msg = "" if not result.error_message else result.error_message
        self.assertTrue("invalid argument" in msg)

    def test_unsupported_extraction_strategy(self):
        result = self.crawler.run(
            url="https://www.nbcnews.com/business",
            extraction_strategy="UnsupportedStrategy", # pyright: ignore[reportArgumentType]
            cache_mode=CacheMode.BYPASS,
        )
        self.assertFalse(
            result.success, "Extraction should fail with unsupported strategy"
        )
        self.assertEqual("Unsupported extraction strategy", result.error_message)

    @pytest.mark.skip("Skipping InvalidCSSSelectorError is no longer raised")
    def test_invalid_css_selector(self):
        result = self.crawler.run(
            url="https://www.nbcnews.com/business",
            css_selector="invalid_selector",
            cache_mode=CacheMode.BYPASS,
            warmup=False
        )
        self.assertFalse(
            result.success, "Extraction should fail with invalid CSS selector"
        )
        self.assertEqual("Invalid CSS selector", result.error_message)

    def test_crawl_with_cache_and_bypass_cache(self):
        url = "https://www.nbcnews.com/business"

        # First crawl with cache enabled
        result = self.crawler.run(url=url, bypass_cache=False, warmup=False)
        self.assertTrue(result.success, "Failed to crawl and cache the result")

        # Second crawl with cache_mode=CacheMode.BYPASS
        result = self.crawler.run(url=url, cache_mode=CacheMode.BYPASS, warmup=False)
        self.assertTrue(result.success, "Failed to bypass cache and fetch fresh data")

    def test_fetch_multiple_pages(self):
        urls = ["https://www.nbcnews.com/business", "https://www.bbc.com/news"]
        results = []
        for url in urls:
            result = self.crawler.run(
                url=url,
                word_count_threshold=5,
                chunking_strategy=RegexChunking(),
                extraction_strategy=CosineStrategy(),
                cache_mode=CacheMode.BYPASS,
                warmup=False
            )
            results.append(result)

        self.assertEqual(len(results), 2, "Failed to crawl and extract multiple pages")
        for result in results:
            self.assertTrue(
                result.success, "Failed to crawl and extract a page in the list"
            )

    def test_run_fixed_length_word_chunking_and_no_extraction(self):
        result = self.crawler.run(
            url="https://www.nbcnews.com/business",
            word_count_threshold=5,
            chunking_strategy=FixedLengthWordChunking(chunk_size=100),
            extraction_strategy=NoExtractionStrategy(),
            cache_mode=CacheMode.BYPASS,
            warmup=False,
        )
        self.assertTrue(
            result.success,
            "Failed to crawl and extract with FixedLengthWordChunking and NoExtractionStrategy",
        )

    def test_run_sliding_window_and_no_extraction(self):
        result = self.crawler.run(
            url="https://www.nbcnews.com/business",
            word_count_threshold=5,
            chunking_strategy=SlidingWindowChunking(window_size=100, step=50),
            extraction_strategy=NoExtractionStrategy(),
            cache_mode=CacheMode.BYPASS,
            warmup=False
        )
        self.assertTrue(
            result.success,
            "Failed to crawl and extract with SlidingWindowChunking and NoExtractionStrategy",
        )


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))

import json
import os
import sys

import pytest

from crawl4ai import CacheMode
from crawl4ai.async_configs import LLMConfig
from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.chunking_strategy import RegexChunking
from crawl4ai.extraction_strategy import CosineStrategy, LLMExtractionStrategy, NoExtractionStrategy


@pytest.mark.asyncio
async def test_regex_chunking():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        chunking_strategy = RegexChunking(patterns=["\n\n"])
        result = await crawler.arun(
            url=url,
            chunking_strategy=chunking_strategy,
            extraction_strategy=NoExtractionStrategy(),
            cache_mode=CacheMode.BYPASS,
        )
        assert result.success
        assert result.extracted_content
        chunks = json.loads(result.extracted_content)
        assert len(chunks) > 1  # Ensure multiple chunks were created

@pytest.mark.asyncio
async def test_cosine_strategy():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        extraction_strategy = CosineStrategy(word_count_threshold=10, max_dist=0.2, linkage_method="ward", top_k=3, sim_threshold=0.3)
        result = await crawler.arun(
            url=url,
            extraction_strategy=extraction_strategy,
            cache_mode=CacheMode.BYPASS
        )
        assert result.success
        assert result.extracted_content
        extracted_data = json.loads(result.extracted_content)
        assert len(extracted_data) > 0
        assert all('tags' in item for item in extracted_data)


@pytest.mark.asyncio
async def test_llm_extraction_strategy():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("Skipping env OPENAI_API_KEY not set")
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        extraction_strategy = LLMExtractionStrategy(
            llm_config=LLMConfig(provider="openai/gpt-4o-mini", api_token=os.getenv("OPENAI_API_KEY")),
            instruction="Extract only content related to technology",
        )
        result = await crawler.arun(url=url, extraction_strategy=extraction_strategy, cache_mode=CacheMode.BYPASS)
        assert result.success
        assert result.extracted_content
        extracted_data = json.loads(result.extracted_content)
        assert len(extracted_data) > 0
        assert all("content" in item for item in extracted_data)


@pytest.mark.asyncio
async def test_combined_chunking_and_extraction():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        chunking_strategy = RegexChunking(patterns=["\n\n"])
        extraction_strategy = CosineStrategy(
            word_count_threshold=10, max_dist=0.2, linkage_method="ward", top_k=3, sim_threshold=0.3
        )
        result = await crawler.arun(
            url=url,
            chunking_strategy=chunking_strategy,
            extraction_strategy=extraction_strategy,
            cache_mode=CacheMode.BYPASS,
        )
        assert result.success
        assert result.extracted_content
        extracted_data = json.loads(result.extracted_content)
        assert len(extracted_data) > 0
        assert all('tags' in item for item in extracted_data)
        assert all('content' in item for item in extracted_data)


# Entry point for debugging
if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))

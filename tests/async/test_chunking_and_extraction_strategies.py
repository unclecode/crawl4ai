import os
import sys
import pytest
import asyncio
import json

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from crawl4ai.async_webcrawler import AsyncWebCrawler
from crawl4ai.chunking_strategy import RegexChunking, NlpSentenceChunking
from crawl4ai.extraction_strategy import CosineStrategy, LLMExtractionStrategy

@pytest.mark.asyncio
async def test_regex_chunking():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        chunking_strategy = RegexChunking(patterns=["\n\n"])
        result = await crawler.arun(
            url=url,
            chunking_strategy=chunking_strategy,
            bypass_cache=True
        )
        assert result.success
        assert result.extracted_content
        chunks = json.loads(result.extracted_content)
        assert len(chunks) > 1  # Ensure multiple chunks were created

# @pytest.mark.asyncio
# async def test_cosine_strategy():
#     async with AsyncWebCrawler(verbose=True) as crawler:
#         url = "https://www.nbcnews.com/business"
#         extraction_strategy = CosineStrategy(word_count_threshold=10, max_dist=0.2, linkage_method="ward", top_k=3, sim_threshold=0.3)
#         result = await crawler.arun(
#             url=url,
#             extraction_strategy=extraction_strategy,
#             bypass_cache=True
#         )
#         assert result.success
#         assert result.extracted_content
#         extracted_data = json.loads(result.extracted_content)
#         assert len(extracted_data) > 0
#         assert all('tags' in item for item in extracted_data)

@pytest.mark.asyncio
async def test_llm_extraction_strategy():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        extraction_strategy = LLMExtractionStrategy(
            provider="openai/gpt-4o-mini",
            api_token=os.getenv('OPENAI_API_KEY'),
            instruction="Extract only content related to technology"
        )
        result = await crawler.arun(
            url=url,
            extraction_strategy=extraction_strategy,
            bypass_cache=True
        )
        assert result.success
        assert result.extracted_content
        extracted_data = json.loads(result.extracted_content)
        assert len(extracted_data) > 0
        assert all('content' in item for item in extracted_data)

# @pytest.mark.asyncio
# async def test_combined_chunking_and_extraction():
#     async with AsyncWebCrawler(verbose=True) as crawler:
#         url = "https://www.nbcnews.com/business"
#         chunking_strategy = RegexChunking(patterns=["\n\n"])
#         extraction_strategy = CosineStrategy(word_count_threshold=10, max_dist=0.2, linkage_method="ward", top_k=3, sim_threshold=0.3)
#         result = await crawler.arun(
#             url=url,
#             chunking_strategy=chunking_strategy,
#             extraction_strategy=extraction_strategy,
#             bypass_cache=True
#         )
#         assert result.success
#         assert result.extracted_content
#         extracted_data = json.loads(result.extracted_content)
#         assert len(extracted_data) > 0
#         assert all('tags' in item for item in extracted_data)
#         assert all('content' in item for item in extracted_data)

# Entry point for debugging
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
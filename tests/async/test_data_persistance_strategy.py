import os
import sys
import pytest
from datasets import load_dataset
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.data_persistence_strategy import HFDataPersistenceStrategy

# Add the parent directory to the Python path
parent_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(parent_dir)

from crawl4ai.async_webcrawler import AsyncWebCrawler


@pytest.mark.asyncio
async def test_save_with_unsupported_data_persistence_strategy():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        unsupported_data_persistence_strategy = JsonCssExtractionStrategy({})

        result = await crawler.arun(
            url=url,
            bypass_cache=True,
            data_persistence_strategy=unsupported_data_persistence_strategy,
        )
        assert not result.success
        assert result.url == url
        assert not result.html
        assert "data_persistence_strategy must be an instance of DataPersistenceStrategy" in result.error_message
        assert result.storage_metadata is None


@pytest.mark.asyncio
async def test_save_to_hf():
    async with AsyncWebCrawler(verbose=True) as crawler:
        url = "https://www.nbcnews.com/business"
        schema = {
            "name": "News Teaser Extractor",
            "baseSelector": ".wide-tease-item__wrapper",
            "fields": [
                {
                    "name": "category",
                    "selector": ".unibrow span[data-testid='unibrow-text']",
                    "type": "text",
                },
                {
                    "name": "headline",
                    "selector": ".wide-tease-item__headline",
                    "type": "text",
                },
                {
                    "name": "summary",
                    "selector": ".wide-tease-item__description",
                    "type": "text",
                },
                {
                    "name": "link",
                    "selector": "a[href]",
                    "type": "attribute",
                    "attribute": "href",
                },
            ],
        }

        extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)
        repo_id = "test_repo"
        data_persistence_strategy = HFDataPersistenceStrategy(
            repo_id=repo_id, private=False, verbose=True
        )

        result = await crawler.arun(
            url=url,
            bypass_cache=True,
            extraction_strategy=extraction_strategy,
            data_persistence_strategy=data_persistence_strategy,
        )
        assert result.success
        assert result.url == url
        assert result.html
        assert result.markdown
        assert result.cleaned_html
        assert result.storage_metadata
        assert result.storage_metadata["split"] == "https___www_nbcnews_com_business"
        created_repo_id = result.storage_metadata["repo_id"]
        new_dataset = load_dataset(created_repo_id, split="train")
        assert len(new_dataset) > 0


# Entry point for debugging
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

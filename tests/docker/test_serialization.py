import sys
from typing import Any, List

import pytest
from _pytest.mark import ParameterSet

from crawl4ai import (
    BM25ContentFilter,
    CacheMode,
    CrawlerRunConfig,
    DefaultMarkdownGenerator,
    JsonCssExtractionStrategy,
    LLMContentFilter,
    LXMLWebScrapingStrategy,
    PruningContentFilter,
    RegexChunking,
    WebScrapingStrategy,
)
from crawl4ai.async_configs import LLMConfig, from_serializable, to_serializable_dict


def is_empty_value(value: Any) -> bool:
    """Check if a value is effectively empty/null."""
    if value is None:
        return True
    if isinstance(value, (list, tuple, set, dict, str)) and len(value) == 0:
        return True
    return False


def config_params() -> List[ParameterSet]:
    # Test Case 1: BM25 content filtering through markdown generator
    params: List[ParameterSet] = []
    params.append(
        pytest.param(
            CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                markdown_generator=DefaultMarkdownGenerator(
                    content_filter=BM25ContentFilter(
                        user_query="technology articles",
                        bm25_threshold=1.2,
                        language="english",
                    )
                ),
                chunking_strategy=RegexChunking(patterns=[r"\n\n", r"\.\s+"]),
                excluded_tags=["nav", "footer", "aside"],
                remove_overlay_elements=True,
            ),
            id="BM25 Content Filter",
        )
    )

    # Test Case 2: LLM-based extraction with pruning filter
    schema = {
        "baseSelector": "article.post",
        "fields": [
            {"name": "title", "selector": "h1", "type": "text"},
            {"name": "content", "selector": ".content", "type": "html"},
        ],
    }
    params.append(
        pytest.param(
            CrawlerRunConfig(
                extraction_strategy=JsonCssExtractionStrategy(schema=schema),
                markdown_generator=DefaultMarkdownGenerator(
                    content_filter=PruningContentFilter(
                        threshold=0.48, threshold_type="fixed", min_word_threshold=0
                    ),
                    options={"ignore_links": True},
                ),
                scraping_strategy=LXMLWebScrapingStrategy(),
            ),
            id="LLM Pruning Filter",
        )
    )

    # Test Case 3:LLM content filter
    params.append(
        pytest.param(
            CrawlerRunConfig(
                markdown_generator=DefaultMarkdownGenerator(
                    content_filter=LLMContentFilter(
                        llm_config=LLMConfig(provider="openai/gpt-4"),
                        instruction="Extract key technical concepts",
                        chunk_token_threshold=2000,
                        overlap_rate=0.1,
                    ),
                    options={"ignore_images": True},
                ),
                scraping_strategy=WebScrapingStrategy(),
            ),
            id="LLM Content Filter",
        )
    )

    return params


@pytest.mark.parametrize("config", config_params())
def test_serialization(config: CrawlerRunConfig) -> None:
    # Serialize
    serialized = to_serializable_dict(config)
    print("\nSerialized Config:")
    print(serialized)

    # Deserialize
    deserialized = from_serializable(serialized)
    print("\nDeserialized Config:")
    print(to_serializable_dict(deserialized))  # Convert back to dict for comparison

    # Verify they match
    assert to_serializable_dict(config) == to_serializable_dict(deserialized)


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.call(["pytest", *sys.argv[1:], sys.argv[0]]))

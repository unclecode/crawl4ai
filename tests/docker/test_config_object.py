import json
from crawl4ai import (
    CrawlerRunConfig,
    DefaultMarkdownGenerator,
    RegexChunking,
    JsonCssExtractionStrategy,
    BM25ContentFilter,
    CacheMode
)
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FastFilterChain
from crawl4ai.deep_crawling.filters import FastContentTypeFilter, FastDomainFilter
from crawl4ai.deep_crawling.scorers import FastKeywordRelevanceScorer

def create_test_config() -> CrawlerRunConfig:
    # Set up content filtering and markdown generation
    content_filter = BM25ContentFilter(
        user_query="technology articles",
    )
    
    markdown_generator = DefaultMarkdownGenerator(
        content_filter=content_filter,
        options={"ignore_links": False, "body_width": 0}
    )

    # Set up extraction strategy
    extraction_schema = {
        "name": "ArticleExtractor",
        "baseSelector": "article.content",
        "fields": [
            {"name": "title", "selector": "h1", "type": "text"},
            {"name": "content", "selector": ".article-body", "type": "html"}
        ]
    }
    extraction_strategy = JsonCssExtractionStrategy(schema=extraction_schema)

    # Set up deep crawling
    filter_chain = FastFilterChain([
        FastContentTypeFilter(["text/html"]),
        FastDomainFilter(blocked_domains=["ads.*"])
    ])

    url_scorer = FastKeywordRelevanceScorer(
        keywords=["article", "blog"],
        weight=1.0
    )

    deep_crawl_strategy = BFSDeepCrawlStrategy(
        max_depth=3,
        filter_chain=filter_chain,
        url_scorer=url_scorer
    )

    # Create the config
    config = CrawlerRunConfig(
        word_count_threshold=200,
        extraction_strategy=extraction_strategy,
        chunking_strategy=RegexChunking(patterns=[r"\n\n"]),
        markdown_generator=markdown_generator,
        css_selector="main.content",
        excluded_tags=["nav", "footer"],
        keep_attrs=["href", "src"],
        cache_mode=CacheMode.BYPASS,
        wait_until="networkidle",
        page_timeout=30000,
        scan_full_page=True,
        deep_crawl_strategy=deep_crawl_strategy,
        verbose=True,
        stream=True
    )

    return config

def test_config_serialization_cycle():
    # Create original config
    original_config = create_test_config()
    
    # Dump to serializable dictionary
    serialized = original_config.dump()

    print(json.dumps(serialized, indent=2))
    
    # Load back into config object
    deserialized_config = CrawlerRunConfig.load(serialized)
    
    # Verify core attributes
    assert deserialized_config.word_count_threshold == original_config.word_count_threshold
    assert deserialized_config.css_selector == original_config.css_selector
    assert deserialized_config.excluded_tags == original_config.excluded_tags
    assert deserialized_config.keep_attrs == original_config.keep_attrs
    assert deserialized_config.cache_mode == original_config.cache_mode
    assert deserialized_config.wait_until == original_config.wait_until
    assert deserialized_config.page_timeout == original_config.page_timeout
    assert deserialized_config.scan_full_page == original_config.scan_full_page
    assert deserialized_config.verbose == original_config.verbose
    assert deserialized_config.stream == original_config.stream

    # Verify complex objects
    assert isinstance(deserialized_config.extraction_strategy, JsonCssExtractionStrategy)
    assert isinstance(deserialized_config.chunking_strategy, RegexChunking)
    assert isinstance(deserialized_config.markdown_generator, DefaultMarkdownGenerator)
    assert isinstance(deserialized_config.markdown_generator.content_filter, BM25ContentFilter)
    assert isinstance(deserialized_config.deep_crawl_strategy, BFSDeepCrawlStrategy)
    
    # Verify deep crawl strategy configuration
    assert deserialized_config.deep_crawl_strategy.max_depth == 3
    assert isinstance(deserialized_config.deep_crawl_strategy.filter_chain, FastFilterChain)
    assert isinstance(deserialized_config.deep_crawl_strategy.url_scorer, FastKeywordRelevanceScorer)

    print("Serialization cycle test passed successfully!")

if __name__ == "__main__":
    test_config_serialization_cycle()
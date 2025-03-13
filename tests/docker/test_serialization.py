import inspect
from typing import Any, Dict
from enum import Enum

from crawl4ai import LLMConfig

def to_serializable_dict(obj: Any) -> Dict:
    """
    Recursively convert an object to a serializable dictionary using {type, params} structure
    for complex objects.
    """
    if obj is None:
        return None
        
    # Handle basic types
    if isinstance(obj, (str, int, float, bool)):
        return obj
        
    # Handle Enum
    if isinstance(obj, Enum):
        return {
            "type": obj.__class__.__name__,
            "params": obj.value
        }
        
    # Handle datetime objects
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
        
    # Handle lists, tuples, and sets
    if isinstance(obj, (list, tuple, set)):
        return [to_serializable_dict(item) for item in obj]
        
    # Handle dictionaries - preserve them as-is
    if isinstance(obj, dict):
        return {
            "type": "dict",  # Mark as plain dictionary
            "value": {str(k): to_serializable_dict(v) for k, v in obj.items()}
        }
    
    # Handle class instances
    if hasattr(obj, '__class__'):
        # Get constructor signature
        sig = inspect.signature(obj.__class__.__init__)
        params = sig.parameters
        
        # Get current values
        current_values = {}
        for name, param in params.items():
            if name == 'self':
                continue
                
            value = getattr(obj, name, param.default)
            
            # Only include if different from default, considering empty values
            if not (is_empty_value(value) and is_empty_value(param.default)):
                if value != param.default:
                    current_values[name] = to_serializable_dict(value)
        
        return {
            "type": obj.__class__.__name__,
            "params": current_values
        }
        
    return str(obj)

def from_serializable_dict(data: Any) -> Any:
    """
    Recursively convert a serializable dictionary back to an object instance.
    """
    if data is None:
        return None
        
    # Handle basic types
    if isinstance(data, (str, int, float, bool)):
        return data
        
    # Handle typed data
    if isinstance(data, dict) and "type" in data:
        # Handle plain dictionaries
        if data["type"] == "dict":
            return {k: from_serializable_dict(v) for k, v in data["value"].items()}
            
        # Import from crawl4ai for class instances
        import crawl4ai
        cls = getattr(crawl4ai, data["type"])
        
        # Handle Enum
        if issubclass(cls, Enum):
            return cls(data["params"])
            
        # Handle class instances
        constructor_args = {
            k: from_serializable_dict(v) for k, v in data["params"].items()
        }
        return cls(**constructor_args)
        
    # Handle lists
    if isinstance(data, list):
        return [from_serializable_dict(item) for item in data]
        
    # Handle raw dictionaries (legacy support)
    if isinstance(data, dict):
        return {k: from_serializable_dict(v) for k, v in data.items()}
        
    return data
    
def is_empty_value(value: Any) -> bool:
    """Check if a value is effectively empty/null."""
    if value is None:
        return True
    if isinstance(value, (list, tuple, set, dict, str)) and len(value) == 0:
        return True
    return False

# if __name__ == "__main__":
#     from crawl4ai import (
#         CrawlerRunConfig, CacheMode, DefaultMarkdownGenerator, 
#         PruningContentFilter, BM25ContentFilter, LLMContentFilter,
#         JsonCssExtractionStrategy, CosineStrategy, RegexChunking,
#         WebScrapingStrategy, LXMLWebScrapingStrategy
#     )

#     # Test Case 1: BM25 content filtering through markdown generator
#     config1 = CrawlerRunConfig(
#         cache_mode=CacheMode.BYPASS,
#         markdown_generator=DefaultMarkdownGenerator(
#             content_filter=BM25ContentFilter(
#                 user_query="technology articles",
#                 bm25_threshold=1.2,
#                 language="english"
#             )
#         ),
#         chunking_strategy=RegexChunking(patterns=[r"\n\n", r"\.\s+"]),
#         excluded_tags=["nav", "footer", "aside"],
#         remove_overlay_elements=True
#     )

#     # Serialize
#     serialized = to_serializable_dict(config1)
#     print("\nSerialized Config:")
#     print(serialized)
    
#     # Example output structure would now look like:
#     """
#     {
#         "type": "CrawlerRunConfig",
#         "params": {
#             "cache_mode": {
#                 "type": "CacheMode",
#                 "params": "bypass"
#             },
#             "markdown_generator": {
#                 "type": "DefaultMarkdownGenerator",
#                 "params": {
#                     "content_filter": {
#                         "type": "BM25ContentFilter",
#                         "params": {
#                             "user_query": "technology articles",
#                             "bm25_threshold": 1.2,
#                             "language": "english"
#                         }
#                     }
#                 }
#             }
#         }
#     }
#     """
    
#     # Deserialize
#     deserialized = from_serializable_dict(serialized)
#     print("\nDeserialized Config:")
#     print(to_serializable_dict(deserialized))
    
#     # Verify they match
#     assert to_serializable_dict(config1) == to_serializable_dict(deserialized)
#     print("\nVerification passed: Configuration matches after serialization/deserialization!")

if __name__ == "__main__":
    from crawl4ai import (
        CrawlerRunConfig, CacheMode, DefaultMarkdownGenerator, 
        PruningContentFilter, BM25ContentFilter, LLMContentFilter,
        JsonCssExtractionStrategy, RegexChunking,
        WebScrapingStrategy, LXMLWebScrapingStrategy
    )

    # Test Case 1: BM25 content filtering through markdown generator
    config1 = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=BM25ContentFilter(
                user_query="technology articles",
                bm25_threshold=1.2,
                language="english"
            )
        ),
        chunking_strategy=RegexChunking(patterns=[r"\n\n", r"\.\s+"]),
        excluded_tags=["nav", "footer", "aside"],
        remove_overlay_elements=True
    )

    # Test Case 2: LLM-based extraction with pruning filter
    schema = {
        "baseSelector": "article.post",
        "fields": [
            {"name": "title", "selector": "h1", "type": "text"},
            {"name": "content", "selector": ".content", "type": "html"}
        ]
    }
    config2 = CrawlerRunConfig(
        extraction_strategy=JsonCssExtractionStrategy(schema=schema),
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48,
                threshold_type="fixed",
                min_word_threshold=0
            ),
            options={"ignore_links": True}
        ),
        scraping_strategy=LXMLWebScrapingStrategy()
    )

    # Test Case 3:LLM content filter
    config3 = CrawlerRunConfig(
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=LLMContentFilter(
                llm_config = LLMConfig(provider="openai/gpt-4"),
                instruction="Extract key technical concepts",
                chunk_token_threshold=2000,
                overlap_rate=0.1
            ),
            options={"ignore_images": True}
        ),
        scraping_strategy=WebScrapingStrategy()
    )

    # Test all configurations
    test_configs = [config1, config2, config3]
    
    for i, config in enumerate(test_configs, 1):
        print(f"\nTesting Configuration {i}:")
        
        # Serialize
        serialized = to_serializable_dict(config)
        print(f"\nSerialized Config {i}:")
        print(serialized)
        
        # Deserialize
        deserialized = from_serializable_dict(serialized)
        print(f"\nDeserialized Config {i}:")
        print(to_serializable_dict(deserialized))  # Convert back to dict for comparison
        
        # Verify they match
        assert to_serializable_dict(config) == to_serializable_dict(deserialized)
        print(f"\nVerification passed: Configuration {i} matches after serialization/deserialization!")
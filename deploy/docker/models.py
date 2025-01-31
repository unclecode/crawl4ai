from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from crawl4ai import (
    BrowserConfig,
    CrawlerRunConfig,
    DefaultMarkdownGenerator,
    PruningContentFilter,
    BM25ContentFilter,
    LLMContentFilter,
    # Add other strategy classes as needed
    
)

class StrategyConfig(BaseModel):
    """Base class for strategy configurations"""
    type: str
    params: Dict[str, Any]

    def create_instance(self):
        """Convert config to actual strategy instance"""
        strategy_mappings = {
            # Markdown Generators
            'DefaultMarkdownGenerator': DefaultMarkdownGenerator,

            # Content Filters
            'PruningContentFilter': PruningContentFilter,
            'BM25ContentFilter': BM25ContentFilter,
            'LLMContentFilter': LLMContentFilter,

            # Add other mappings as needed
            # 'CustomStrategy': CustomStrategyClass,
        }

        strategy_class = strategy_mappings.get(self.type)
        if not strategy_class:
            raise ValueError(f"Unknown strategy type: {self.type}")

        # Handle nested strategy configurations
        processed_params = {}
        for key, value in self.params.items():
            if isinstance(value, dict) and 'type' in value:
                # Recursively create nested strategy instances
                nested_config = StrategyConfig(type=value['type'], params=value.get('params', {}))
                processed_params[key] = nested_config.create_instance()
            else:
                processed_params[key] = value

        return strategy_class(**processed_params)

class CrawlRequest(BaseModel):
    urls: List[str]
    browser_config: Optional[dict] = None
    crawler_config: Optional[dict] = None

    def get_configs(self):
        """Enhanced conversion of dicts to config objects"""
        browser_config = BrowserConfig.from_kwargs(self.browser_config or {})

        crawler_dict = self.crawler_config or {}

        # Process strategy configurations
        for key, value in crawler_dict.items():
            if isinstance(value, dict) and 'type' in value:
                # Convert strategy configuration to actual instance
                strategy_config = StrategyConfig(
                    type=value['type'],
                    params=value.get('params', {})
                )
                crawler_dict[key] = strategy_config.create_instance()

        crawler_config = CrawlerRunConfig.from_kwargs(crawler_dict)
        return browser_config, crawler_config

class CrawlResponse(BaseModel):
    success: bool
    results: List[dict]  # Will contain serialized CrawlResults

    class Config:
        arbitrary_types_allowed = True
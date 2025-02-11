# deep_crawling/__init__.py
from .base_strategy import DeepCrawlDecorator, DeepCrawlStrategy
from .bfs_strategy import BFSDeepCrawlStrategy
from .bff_strategy import BestFirstCrawlingStrategy
from .dfs_strategy import DFSDeepCrawlStrategy

__all__ = [
    "DeepCrawlDecorator",
    "DeepCrawlStrategy",
    "BFSDeepCrawlStrategy",
    "BestFirstCrawlingStrategy",
    "DFSDeepCrawlStrategy",
]
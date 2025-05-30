# crawl4ai/hub.py
from abc import ABC, abstractmethod
from typing import Dict, Type, Union
import logging
import importlib
from pathlib import Path
import inspect

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
    @abstractmethod
    async def run(self, url: str = "", **kwargs) -> str:
        """
        Implement this method to return JSON string.
        Must accept URL + arbitrary kwargs for flexibility.
        """
        pass

    def __init_subclass__(cls, **kwargs):
        """Enforce interface validation on subclassing"""
        super().__init_subclass__(**kwargs)
        
        # Verify run method signature
        run_method = cls.run
        if not run_method.__code__.co_argcount >= 2:  # self + url
            raise TypeError(f"{cls.__name__} must implement 'run(self, url: str, **kwargs)'")
            
        # Verify async nature
        if not inspect.iscoroutinefunction(run_method):
            raise TypeError(f"{cls.__name__}.run must be async")

class CrawlerHub:
    _crawlers: Dict[str, Type[BaseCrawler]] = {}

    @classmethod
    def _discover_crawlers(cls):
        """Dynamically load crawlers from /crawlers in 3 lines"""
        base_path = Path(__file__).parent / "crawlers"
        for crawler_dir in base_path.iterdir():
            if crawler_dir.is_dir():
                try:
                    module = importlib.import_module(
                        f"crawl4ai.crawlers.{crawler_dir.name}.crawler"
                    )
                    for attr in dir(module):
                        cls._maybe_register_crawler(
                            getattr(module, attr), crawler_dir.name
                        )
                except Exception as e:
                    logger.warning(f"Failed {crawler_dir.name}: {str(e)}")

    @classmethod
    def _maybe_register_crawler(cls, obj, name: str):
        """Brilliant one-liner registration"""
        if isinstance(obj, type) and issubclass(obj, BaseCrawler) and obj != BaseCrawler:
            module = importlib.import_module(obj.__module__)
            obj.meta = getattr(module, "__meta__", {})
            cls._crawlers[name] = obj

    @classmethod
    def get(cls, name: str) -> Union[Type[BaseCrawler], None]:
        if not cls._crawlers:
            cls._discover_crawlers()
        return cls._crawlers.get(name)
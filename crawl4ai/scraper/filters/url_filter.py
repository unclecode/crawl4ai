from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from typing import List
@dataclass
class FilterStats:
    """Statistics for filter applications"""
    total_urls: int = 0
    rejected_urls: int = 0
    passed_urls: int = 0

class URLFilter(ABC):
    """Base class for URL filters"""
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.stats = FilterStats()
        self.logger = logging.getLogger(f"urlfilter.{self.name}")

    @abstractmethod
    def apply(self, url: str) -> bool:
        """Apply the filter to a URL"""
        pass

    def _update_stats(self, passed: bool):
        """Update filter statistics"""
        self.stats.total_urls += 1
        if passed:
            self.stats.passed_urls += 1
        else:
            self.stats.rejected_urls += 1

class FilterChain:
    """Chain of URL filters"""
    
    def __init__(self, filters: List[URLFilter] = None):
        self.filters = filters or []
        self.stats = FilterStats()
        self.logger = logging.getLogger("urlfilter.chain")

    def add_filter(self, filter_: URLFilter) -> 'FilterChain':
        """Add a filter to the chain"""
        self.filters.append(filter_)
        return self  # Enable method chaining

    def apply(self, url: str) -> bool:
        """Apply all filters in the chain"""
        self.stats.total_urls += 1
        
        for filter_ in self.filters:
            if not filter_.apply(url):
                self.stats.rejected_urls += 1
                self.logger.debug(f"URL {url} rejected by {filter_.name}")
                return False
        
        self.stats.passed_urls += 1
        return True
    
# class URLFilter(ABC):
#     @abstractmethod
#     def apply(self, url: str) -> bool:
#         pass

# class FilterChain:
#     def __init__(self):
#         self.filters = []

#     def add_filter(self, filter: URLFilter):
#         self.filters.append(filter)

#     def apply(self, url: str) -> bool:
#         return all(filter.apply(url) for filter in self.filters)
from abc import ABC, abstractmethod

class URLFilter(ABC):
    @abstractmethod
    def apply(self, url: str) -> bool:
        pass

class FilterChain:
    def __init__(self):
        self.filters = []

    def add_filter(self, filter: URLFilter):
        self.filters.append(filter)

    def apply(self, url: str) -> bool:
        return all(filter.apply(url) for filter in self.filters)
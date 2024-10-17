from abc import ABC, abstractmethod

class URLScorer(ABC):
    @abstractmethod
    def score(self, url: str) -> float:
        pass
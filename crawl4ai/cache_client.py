from abc import ABC, abstractmethod

DEFAULT_CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days

_CRAWL4AI_CACHE_KEY_PREFIX = "crawl4ai:"
HTML_CACHE_KEY_PREFIX = f"{_CRAWL4AI_CACHE_KEY_PREFIX}html:"
ROBOTS_CACHE_KEY_PREFIX = f"{_CRAWL4AI_CACHE_KEY_PREFIX}robots:"

class CacheClient(ABC):
    @abstractmethod
    def get(self, key: str) -> str | None:
        pass

    @abstractmethod
    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        pass

    @abstractmethod
    def clear(self, prefix: str) -> None:
        pass

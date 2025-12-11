from abc import ABC, abstractmethod

DEFAULT_CACHE_TTL_SECONDS = 2 * 60  # 2 hours

_CRAWL4AI_CACHE_KEY_PREFIX = "c4ai:"
HTML_CACHE_KEY_PREFIX = f"{_CRAWL4AI_CACHE_KEY_PREFIX}html:"
ROBOTS_CACHE_KEY_PREFIX = f"{_CRAWL4AI_CACHE_KEY_PREFIX}robots:"
URL_SEEDER_CACHE_KEY_PREFIX = f"{_CRAWL4AI_CACHE_KEY_PREFIX}url_seeder:"

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


class NoCacheClient(CacheClient):
    def get(self, key: str) -> str | None:
        return None

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        pass

    def clear(self, prefix: str) -> None:
        pass

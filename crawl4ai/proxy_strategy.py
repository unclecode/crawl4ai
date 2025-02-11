from typing import List, Dict, Optional
from abc import ABC, abstractmethod
from itertools import cycle

class ProxyRotationStrategy(ABC):
    """Base abstract class for proxy rotation strategies"""
    
    @abstractmethod
    async def get_next_proxy(self) -> Optional[Dict]:
        """Get next proxy configuration from the strategy"""
        pass

    @abstractmethod
    def add_proxies(self, proxies: List[Dict]):
        """Add proxy configurations to the strategy"""
        pass

class RoundRobinProxyStrategy(ProxyRotationStrategy):
    """Simple round-robin proxy rotation strategy"""

    def __init__(self, proxies: List[Dict] = None):
        """
        Initialize with optional list of proxy configurations
        
        Args:
            proxies: List of proxy config dictionaries, each containing at least
                    'server' key with proxy URL
        """
        self._proxies = []
        self._proxy_cycle = None
        if proxies:
            self.add_proxies(proxies)

    def add_proxies(self, proxies: List[Dict]):
        """Add new proxies to the rotation pool"""
        self._proxies.extend(proxies)
        self._proxy_cycle = cycle(self._proxies)

    async def get_next_proxy(self) -> Optional[Dict]:
        """Get next proxy in round-robin fashion"""
        if not self._proxy_cycle:
            return None
        return next(self._proxy_cycle)

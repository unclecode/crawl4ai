from typing import List, Dict, Optional
from abc import ABC, abstractmethod
from itertools import cycle
import os
import random
import time
import asyncio
import logging
from collections import defaultdict


########### ATTENTION PEOPLE OF EARTH ###########
# I have moved this config to async_configs.py, kept it here, in case someone still importing it, however
# be a dear and follow `from crawl4ai import ProxyConfig` instead :)
class ProxyConfig:
    def __init__(
        self,
        server: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        ip: Optional[str] = None,
    ):
        """Configuration class for a single proxy.
        
        Args:
            server: Proxy server URL (e.g., "http://127.0.0.1:8080")
            username: Optional username for proxy authentication
            password: Optional password for proxy authentication
            ip: Optional IP address for verification purposes
        """
        self.server = server
        self.username = username
        self.password = password
        
        # Extract IP from server if not explicitly provided
        self.ip = ip or self._extract_ip_from_server()
    
    def _extract_ip_from_server(self) -> Optional[str]:
        """Extract IP address from server URL."""
        try:
            # Simple extraction assuming http://ip:port format
            if "://" in self.server:
                parts = self.server.split("://")[1].split(":")
                return parts[0]
            else:
                parts = self.server.split(":")
                return parts[0]
        except Exception:
            return None
    
    @staticmethod
    def from_string(proxy_str: str) -> "ProxyConfig":
        """Create a ProxyConfig from a string in the format 'ip:port:username:password'."""
        parts = proxy_str.split(":")
        if len(parts) == 4:  # ip:port:username:password
            ip, port, username, password = parts
            return ProxyConfig(
                server=f"http://{ip}:{port}",
                username=username,
                password=password,
                ip=ip
            )
        elif len(parts) == 2:  # ip:port only
            ip, port = parts
            return ProxyConfig(
                server=f"http://{ip}:{port}",
                ip=ip
            )
        else:
            raise ValueError(f"Invalid proxy string format: {proxy_str}")
    
    @staticmethod
    def from_dict(proxy_dict: Dict) -> "ProxyConfig":
        """Create a ProxyConfig from a dictionary."""
        return ProxyConfig(
            server=proxy_dict.get("server"),
            username=proxy_dict.get("username"),
            password=proxy_dict.get("password"),
            ip=proxy_dict.get("ip")
        )
    
    @staticmethod
    def from_env(env_var: str = "PROXIES") -> List["ProxyConfig"]:
        """Load proxies from environment variable.
        
        Args:
            env_var: Name of environment variable containing comma-separated proxy strings
            
        Returns:
            List of ProxyConfig objects
        """
        proxies = []
        try:
            proxy_list = os.getenv(env_var, "").split(",")
            for proxy in proxy_list:
                if not proxy:
                    continue
                proxies.append(ProxyConfig.from_string(proxy))
        except Exception as e:
            print(f"Error loading proxies from environment: {e}")
        return proxies
    
    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "server": self.server,
            "username": self.username,
            "password": self.password,
            "ip": self.ip
        }
    
    def clone(self, **kwargs) -> "ProxyConfig":
        """Create a copy of this configuration with updated values.

        Args:
            **kwargs: Key-value pairs of configuration options to update

        Returns:
            ProxyConfig: A new instance with the specified updates
        """
        config_dict = self.to_dict()
        config_dict.update(kwargs)
        return ProxyConfig.from_dict(config_dict)


class ProxyRotationStrategy(ABC):
    """Base abstract class for proxy rotation strategies"""
    
    @abstractmethod
    async def get_next_proxy(self) -> Optional[ProxyConfig]:
        """Get next proxy configuration from the strategy"""
        pass

    @abstractmethod
    def add_proxies(self, proxies: List[ProxyConfig]):
        """Add proxy configurations to the strategy"""
        pass

class RoundRobinProxyStrategy(ProxyRotationStrategy):
    """Simple round-robin proxy rotation strategy using ProxyConfig objects"""

    def __init__(self, proxies: List[ProxyConfig] = None):
        """
        Initialize with optional list of proxy configurations
        
        Args:
            proxies: List of ProxyConfig objects
        """
        self._proxies = []
        self._proxy_cycle = None
        if proxies:
            self.add_proxies(proxies)

    def add_proxies(self, proxies: List[ProxyConfig]):
        """Add new proxies to the rotation pool"""
        self._proxies.extend(proxies)
        self._proxy_cycle = cycle(self._proxies)

    async def get_next_proxy(self) -> Optional[ProxyConfig]:
        """Get next proxy in round-robin fashion"""
        if not self._proxy_cycle:
            return None
        return next(self._proxy_cycle)


class RandomProxyStrategy(ProxyRotationStrategy):
    """Random proxy selection strategy for unpredictable traffic patterns."""
    
    def __init__(self, proxies: List[ProxyConfig] = None):
        self._proxies = []
        self._lock = asyncio.Lock()
        if proxies:
            self.add_proxies(proxies)
    
    def add_proxies(self, proxies: List[ProxyConfig]):
        """Add new proxies to the rotation pool."""
        self._proxies.extend(proxies)
    
    async def get_next_proxy(self) -> Optional[ProxyConfig]:
        """Get randomly selected proxy."""
        async with self._lock:
            if not self._proxies:
                return None
            return random.choice(self._proxies)


class LeastUsedProxyStrategy(ProxyRotationStrategy):
    """Least used proxy strategy for optimal load distribution."""
    
    def __init__(self, proxies: List[ProxyConfig] = None):
        self._proxies = []
        self._usage_count: Dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()
        if proxies:
            self.add_proxies(proxies)
    
    def add_proxies(self, proxies: List[ProxyConfig]):
        """Add new proxies to the rotation pool."""
        self._proxies.extend(proxies)
        for proxy in proxies:
            self._usage_count[proxy.server] = 0
    
    async def get_next_proxy(self) -> Optional[ProxyConfig]:
        """Get least used proxy for optimal load balancing."""
        async with self._lock:
            if not self._proxies:
                return None
            
            # Find proxy with minimum usage
            min_proxy = min(self._proxies, key=lambda p: self._usage_count[p.server])
            self._usage_count[min_proxy.server] += 1
            return min_proxy


class FailureAwareProxyStrategy(ProxyRotationStrategy):
    """Failure-aware proxy strategy with automatic recovery and health tracking."""
    
    def __init__(self, proxies: List[ProxyConfig] = None, failure_threshold: int = 3, recovery_time: int = 300):
        self._proxies = []
        self._healthy_proxies = []
        self._failure_count: Dict[str, int] = defaultdict(int)
        self._last_failure_time: Dict[str, float] = defaultdict(float)
        self._failure_threshold = failure_threshold
        self._recovery_time = recovery_time  # seconds
        self._lock = asyncio.Lock()
        if proxies:
            self.add_proxies(proxies)
    
    def add_proxies(self, proxies: List[ProxyConfig]):
        """Add new proxies to the rotation pool."""
        self._proxies.extend(proxies)
        self._healthy_proxies.extend(proxies)
        for proxy in proxies:
            self._failure_count[proxy.server] = 0
    
    async def get_next_proxy(self) -> Optional[ProxyConfig]:
        """Get next healthy proxy with automatic recovery."""
        async with self._lock:
            # Recovery check: re-enable proxies after recovery_time
            current_time = time.time()
            recovered_proxies = []
            
            for proxy in self._proxies:
                if (proxy not in self._healthy_proxies and 
                    current_time - self._last_failure_time[proxy.server] > self._recovery_time):
                    recovered_proxies.append(proxy)
                    self._failure_count[proxy.server] = 0
            
            # Add recovered proxies back to healthy pool
            self._healthy_proxies.extend(recovered_proxies)
            
            # If no healthy proxies, reset all (emergency fallback)
            if not self._healthy_proxies and self._proxies:
                logging.warning("All proxies failed, resetting health status")
                self._healthy_proxies = self._proxies.copy()
                for proxy in self._proxies:
                    self._failure_count[proxy.server] = 0
            
            if not self._healthy_proxies:
                return None
                
            return random.choice(self._healthy_proxies)
    
    async def mark_proxy_failed(self, proxy: ProxyConfig):
        """Mark a proxy as failed and remove from healthy pool if threshold exceeded."""
        async with self._lock:
            self._failure_count[proxy.server] += 1
            self._last_failure_time[proxy.server] = time.time()
            
            if (self._failure_count[proxy.server] >= self._failure_threshold and 
                proxy in self._healthy_proxies):
                self._healthy_proxies.remove(proxy)
                logging.warning(f"Proxy {proxy.server} marked as unhealthy after {self._failure_count[proxy.server]} failures")

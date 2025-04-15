from typing import List, Dict, Optional
from abc import ABC, abstractmethod
from itertools import cycle
import os


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

class RoundRobinProxyStrategy:
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

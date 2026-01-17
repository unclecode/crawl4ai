from typing import List, Dict, Optional, Tuple
from abc import ABC, abstractmethod
from itertools import cycle
import os
import asyncio
import time


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

    @abstractmethod
    async def get_proxy_for_session(
        self,
        session_id: str,
        ttl: Optional[int] = None
    ) -> Optional[ProxyConfig]:
        """
        Get or create a sticky proxy for a session.

        If session_id already has an assigned proxy (and hasn't expired), return it.
        If session_id is new, acquire a new proxy and associate it.

        Args:
            session_id: Unique session identifier
            ttl: Optional time-to-live in seconds for this session

        Returns:
            ProxyConfig for this session
        """
        pass

    @abstractmethod
    async def release_session(self, session_id: str) -> None:
        """
        Release a sticky session, making the proxy available for reuse.

        Args:
            session_id: Session to release
        """
        pass

    @abstractmethod
    def get_session_proxy(self, session_id: str) -> Optional[ProxyConfig]:
        """
        Get the proxy for an existing session without creating new one.

        Args:
            session_id: Session to look up

        Returns:
            ProxyConfig if session exists and hasn't expired, None otherwise
        """
        pass

    @abstractmethod
    def get_active_sessions(self) -> Dict[str, ProxyConfig]:
        """
        Get all active sticky sessions.

        Returns:
            Dictionary mapping session_id to ProxyConfig
        """
        pass

class RoundRobinProxyStrategy(ProxyRotationStrategy):
    """Simple round-robin proxy rotation strategy using ProxyConfig objects.

    Supports sticky sessions where a session_id can be bound to a specific proxy
    for the duration of the session. This is useful for deep crawling where
    you want to maintain the same IP address across multiple requests.
    """

    def __init__(self, proxies: List[ProxyConfig] = None):
        """
        Initialize with optional list of proxy configurations

        Args:
            proxies: List of ProxyConfig objects
        """
        self._proxies: List[ProxyConfig] = []
        self._proxy_cycle = None
        # Session tracking: maps session_id -> (ProxyConfig, created_at, ttl)
        self._sessions: Dict[str, Tuple[ProxyConfig, float, Optional[int]]] = {}
        self._session_lock = asyncio.Lock()

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

    async def get_proxy_for_session(
        self,
        session_id: str,
        ttl: Optional[int] = None
    ) -> Optional[ProxyConfig]:
        """
        Get or create a sticky proxy for a session.

        If session_id already has an assigned proxy (and hasn't expired), return it.
        If session_id is new, acquire a new proxy and associate it.

        Args:
            session_id: Unique session identifier
            ttl: Optional time-to-live in seconds for this session

        Returns:
            ProxyConfig for this session
        """
        async with self._session_lock:
            # Check if session exists and hasn't expired
            if session_id in self._sessions:
                proxy, created_at, session_ttl = self._sessions[session_id]

                # Check TTL expiration
                effective_ttl = ttl if ttl is not None else session_ttl
                if effective_ttl is not None:
                    elapsed = time.time() - created_at
                    if elapsed >= effective_ttl:
                        # Session expired, remove it and get new proxy
                        del self._sessions[session_id]
                    else:
                        return proxy
                else:
                    return proxy

            # Acquire new proxy for this session
            proxy = await self.get_next_proxy()
            if proxy:
                self._sessions[session_id] = (proxy, time.time(), ttl)

            return proxy

    async def release_session(self, session_id: str) -> None:
        """
        Release a sticky session, making the proxy available for reuse.

        Args:
            session_id: Session to release
        """
        async with self._session_lock:
            if session_id in self._sessions:
                del self._sessions[session_id]

    def get_session_proxy(self, session_id: str) -> Optional[ProxyConfig]:
        """
        Get the proxy for an existing session without creating new one.

        Args:
            session_id: Session to look up

        Returns:
            ProxyConfig if session exists and hasn't expired, None otherwise
        """
        if session_id not in self._sessions:
            return None

        proxy, created_at, ttl = self._sessions[session_id]

        # Check TTL expiration
        if ttl is not None:
            elapsed = time.time() - created_at
            if elapsed >= ttl:
                return None

        return proxy

    def get_active_sessions(self) -> Dict[str, ProxyConfig]:
        """
        Get all active sticky sessions (excluding expired ones).

        Returns:
            Dictionary mapping session_id to ProxyConfig
        """
        current_time = time.time()
        active_sessions = {}

        for session_id, (proxy, created_at, ttl) in self._sessions.items():
            # Skip expired sessions
            if ttl is not None:
                elapsed = current_time - created_at
                if elapsed >= ttl:
                    continue
            active_sessions[session_id] = proxy

        return active_sessions

    async def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions from tracking.

        Returns:
            Number of sessions removed
        """
        async with self._session_lock:
            current_time = time.time()
            expired = []

            for session_id, (proxy, created_at, ttl) in self._sessions.items():
                if ttl is not None:
                    elapsed = current_time - created_at
                    if elapsed >= ttl:
                        expired.append(session_id)

            for session_id in expired:
                del self._sessions[session_id]

            return len(expired)

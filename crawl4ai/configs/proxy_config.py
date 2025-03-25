import os
from typing import Dict, List, Optional
from ..validators import ProxyValidator



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
        
        # Normalize proxy configuration
        self._normalize_proxy_config()
    
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

    def _normalize_proxy_config(self):
        """
        Normalize proxy configuration to ensure consistency.
        
        Example:
            proxy_config = {
                "server": "http://user:pass@1.1.1.1:8090",
                "username": "",
                "password": "",
            } ->
            normalized_proxy_config = {
                "server": "http://1.1.1.1:8090",
                "username": "user",
                "password": "pass",
            }
        """
        if not self.server:
            return self

        from urllib.parse import urlparse, unquote

        parsed = urlparse(self.server)

        # urlparse("1.1.1.1:8090") -> scheme='', netloc='', path='1.1.1.1:8090'
        # urlparse("localhost:8090") -> scheme='localhost', netloc='', path='8090'
        # if both of these cases, we need to try re-parse URL with `http://` prefix.
        if not parsed.netloc or not parsed.scheme:
            parsed = urlparse(f"http://{self.server}")
        
        
        username = self.username
        password = self.password
        # The server field takes precedence over username and password.
        if "@" in parsed.netloc:
            auth_part, host_part = parsed.netloc.split("@", 1)
            if ":" in auth_part:
                username, password = auth_part.split(":", 1)
                username = unquote(username)
                password = unquote(password)
            else:
                username = unquote(auth_part)

                password = ""
            server = f"{parsed.scheme}://{host_part}"
        else:
            server = f"{parsed.scheme}://{parsed.netloc}"

        self.server = server
        self.username = username
        self.password = password

        # Validate the proxy string
        ProxyValidator().validate(self.server)

        return self
    
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
        )._normalize_proxy_config()
    
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

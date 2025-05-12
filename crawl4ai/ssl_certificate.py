"""SSL Certificate class for handling certificate operations."""

import ssl
import socks
import socket
import base64
from datetime import datetime
import json
from typing import Dict, Any, Optional, Protocol, Tuple
from urllib.parse import urlparse
import OpenSSL.crypto
from pathlib import Path
from .proxy_strategy import ProxyConfig
from .validators import SSLURLValidator


class ConnectionStrategy(Protocol):
    """Strategy interface for creating socket connections."""

    def create_connection(self, hostname: str, port: int, timeout: int) -> socket.socket:
        """
        Create a socket connection to the specified host.

        Args:
            hostname: Target hostname to connect to
            port: Target port to connect to
            timeout: Connection timeout in seconds

        Returns:
            Connected socket object
        """
        pass


class DirectConnectionStrategy:
    """Direct connection strategy without using a proxy."""

    def create_connection(self, hostname: str, port: int, timeout: int) -> socket.socket:
        """Create a direct socket connection without proxy."""
        return socket.create_connection((hostname, port), timeout=timeout)


class HttpProxyConnectionStrategy:
    """HTTP/HTTPS proxy connection strategy."""

    def __init__(self, proxy_config: ProxyConfig):
        """
        Initialize with proxy configuration.

        Args:
            proxy_config: Proxy configuration object
        """
        self.proxy_config = proxy_config

    def create_connection(self, hostname: str, port: int, timeout: int) -> socket.socket:
        """Create a socket connection through HTTP/HTTPS proxy."""
        sock = socks.socksocket()
        parsed = urlparse(self.proxy_config.server)

        sock.set_proxy(
            socks.HTTP,
            parsed.hostname,
            parsed.port or 80,
            username=self.proxy_config.username,
            password=self.proxy_config.password,
        )
        sock.settimeout(timeout)
        sock.connect((hostname, port))
        return sock


class SocksProxyConnectionStrategy:
    """SOCKS proxy connection strategy."""
    
    def __init__(self, proxy_config: ProxyConfig):
        """
        Initialize with proxy configuration.
        
        Args:
            proxy_config: Proxy configuration object
        """
        self.proxy_config = proxy_config
        
    def create_connection(self, hostname: str, port: int, timeout: int) -> socket.socket:
        """Create a socket connection through SOCKS proxy."""
        sock = socks.socksocket()
        parsed = urlparse(self.proxy_config.server)
        protocol = socks.SOCKS5 # socks5 default use socks5
        if parsed.scheme.lower() == "socks4":
            protocol = socks.SOCKS4
        
        sock.set_proxy(
            protocol,
            parsed.hostname,
            parsed.port or 1080,
            username=self.proxy_config.username,
            password=self.proxy_config.password,
        )
        sock.settimeout(timeout)
        sock.connect((hostname, port))
        return sock


class ConnectionStrategyFactory:
    """Factory for creating appropriate connection strategies."""
    
    @staticmethod
    def create_strategy(proxy_config: Optional[ProxyConfig]) -> ConnectionStrategy:
        """
        Create appropriate connection strategy based on proxy configuration.
        
        Args:
            proxy_config: Optional proxy configuration
            
        Returns:
            A connection strategy instance
        """
        if not proxy_config or not proxy_config.server:
            return DirectConnectionStrategy()
        
        proxy_schema = urlparse(proxy_config.server).scheme.lower()

        if proxy_schema.startswith("http"):
            return HttpProxyConnectionStrategy(proxy_config)
        elif proxy_schema.startswith("socks"):
            return SocksProxyConnectionStrategy(proxy_config)
        else:
            raise ValueError(f"Unsupported proxy scheme: {proxy_schema}")


class SSLCertificate:
    """
    A class representing an SSL certificate with methods to export in various formats.

    Attributes:
        cert_info (Dict[str, Any]): The certificate information.

        Methods:
            from_url(url: str, timeout: int = 10, proxy_config: Optional[ProxyConfig] = None) -> Optional['SSLCertificate']: Create SSLCertificate instance from a URL.
            from_file(file_path: str) -> Optional['SSLCertificate']: Create SSLCertificate instance from a file.
            from_binary(binary_data: bytes) -> Optional['SSLCertificate']: Create SSLCertificate instance from binary data.
            to_pem() -> Optional[str]: Export the certificate as PEM format.
            to_der() -> Optional[bytes]: Export the certificate as DER format.
            to_json() -> Optional[str]: Export the certificate as JSON format.
            to_playwright_format() -> Dict[str, Any]: Export the certificate as Playwright format.
    """

    def __init__(self, cert_info: Dict[str, Any]):
        self._cert_info = self._decode_cert_data(cert_info)

    @staticmethod
    def from_url(
        url: str, timeout: int = 10,
        proxy_config: Optional[ProxyConfig] = None,
        verify_ssl: bool = False
    ) -> Tuple[Optional["SSLCertificate"], str]:
        """
        Create SSLCertificate instance from a URL.

        Args:
            url (str): URL of the website.
            timeout (int): Timeout for the connection (default: 10).
            proxy_config (Optional[ProxyConfig]): Proxy configuration (default: None).
            verify_ssl (bool): Whether to verify SSL certificate (default: False).
        Returns:
            Optional[SSLCertificate]: SSLCertificate instance if successful, None otherwise.
        Raises:
            ValueError: If the URL is not a valid SSL URL.
        """
        
        # Validate the URL
        SSLURLValidator().validate(url)

        try:
            # Extract hostname from URL
            hostname = urlparse(url).netloc
            if ":" in hostname:
                hostname = hostname.split(":")[0]
            
            # Get appropriate connection strategy using the factory
            connection_strategy = ConnectionStrategyFactory.create_strategy(proxy_config)
            
            # Create connection and extract certificate
            sock = None
            try:
                sock = connection_strategy.create_connection(hostname, 443, timeout)
                return SSLCertificate._extract_certificate_from_socket(sock, hostname, verify_ssl), None
            finally:
                # Ensure socket is closed if it wasn't transferred
                if sock:
                    try:
                        sock.close()
                    except Exception:
                        pass  # Ignore any errors during closing

        except (socket.gaierror, socket.timeout) as e:
            return None, f"Network error: {e!s}"
        except ssl.SSLCertVerificationError as e:
            return None, f"SSL Verify error: {e!s}"
        except socks.ProxyError as e:
            return None, f"Proxy error: {e!s}"
        except Exception as e:
            return None, f"Error: {e!s}"

    @staticmethod
    def _extract_certificate_from_socket(sock: socket.socket, hostname: str, verify_ssl: bool = False) -> "SSLCertificate":
        """
        Extract certificate information from an open socket.
        
        Args:
            sock: Connected socket to extract certificate from
            hostname: Hostname for SSL verification
            verify_ssl: Whether to verify SSL certificate (default: False)
            
        Returns:
            SSLCertificate object with extracted certificate information
        """
        context = ssl.create_default_context()

        if not verify_ssl:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            # Socket is now managed by the SSL context
            cert_binary = ssock.getpeercert(binary_form=True)
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_ASN1, cert_binary
            )

            cert_info = {
                "subject": dict(x509.get_subject().get_components()),
                "issuer": dict(x509.get_issuer().get_components()),
                "version": x509.get_version(),
                "serial_number": hex(x509.get_serial_number()),
                "not_before": x509.get_notBefore(),
                "not_after": x509.get_notAfter(),
                "fingerprint": x509.digest("sha256").hex(),
                "signature_algorithm": x509.get_signature_algorithm(),
                "raw_cert": base64.b64encode(cert_binary),
            }

            # Add extensions
            extensions = []
            for i in range(x509.get_extension_count()):
                ext = x509.get_extension(i)
                extensions.append(
                    {"name": ext.get_short_name(), "value": str(ext)}
                )
            cert_info["extensions"] = extensions

            return SSLCertificate(cert_info)

    @staticmethod
    def _decode_cert_data(data: Any) -> Any:
        """Helper method to decode bytes in certificate data."""
        if isinstance(data, bytes):
            return data.decode("utf-8")
        elif isinstance(data, dict):
            return {
                (
                    k.decode("utf-8") if isinstance(k, bytes) else k
                ): SSLCertificate._decode_cert_data(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [SSLCertificate._decode_cert_data(item) for item in data]
        return data

    @staticmethod
    def _parse_certificate_time(time_str: str) -> int:
        """Parse certificate time."""
        if time_str.endswith("Z"):
            time_str = time_str[:-1]

        dt = datetime.strptime(time_str, "%Y%m%d%H%M%S")
        return int(dt.timestamp())

    def to_json(self, filepath: Optional[str] = None) -> Optional[str]:
        """
        Export certificate as JSON.

        Args:
            filepath (Optional[str]): Path to save the JSON file (default: None).

        Returns:
            Optional[str]: JSON string if successful, None otherwise.
        """
        json_str = json.dumps(self._cert_info, indent=2, ensure_ascii=False)
        if filepath:
            Path(filepath).write_text(json_str, encoding="utf-8")
            return None
        return json_str

    def to_pem(self, filepath: Optional[str] = None) -> Optional[str]:
        """
        Export certificate as PEM.

        Args:
            filepath (Optional[str]): Path to save the PEM file (default: None).

        Returns:
            Optional[str]: PEM string if successful, None otherwise.
        """
        try:
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_ASN1,
                base64.b64decode(self._cert_info["raw_cert"]),
            )
            pem_data = OpenSSL.crypto.dump_certificate(
                OpenSSL.crypto.FILETYPE_PEM, x509
            ).decode("utf-8")

            if filepath:
                Path(filepath).write_text(pem_data, encoding="utf-8")
                return None
            return pem_data
        except Exception:
            return None

    def to_der(self, filepath: Optional[str] = None) -> Optional[bytes]:
        """
        Export certificate as DER.

        Args:
            filepath (Optional[str]): Path to save the DER file (default: None).

        Returns:
            Optional[bytes]: DER bytes if successful, None otherwise.
        """
        try:
            der_data = base64.b64decode(self._cert_info["raw_cert"])
            if filepath:
                Path(filepath).write_bytes(der_data)
                return None
            return der_data
        except Exception:
            return None

    def to_playwright_format(self) -> Dict[str, Any]:
        """
        Export certificate as Playwright format.
        """
        return {
            "issuer": self.issuer.get("CN"),
            "subject": self.subject.get("CN"),
            "valid_from": self._parse_certificate_time(self.valid_from),
            "valid_until": self._parse_certificate_time(self.valid_until),
        }

    def __str__(self) -> str:
        return self.to_json()

    @property
    def issuer(self) -> Dict[str, str]:
        """Get certificate issuer information."""
        return self._cert_info.get("issuer", {})

    @property
    def subject(self) -> Dict[str, str]:
        """Get certificate subject information."""
        return self._cert_info.get("subject", {})

    @property
    def valid_from(self) -> str:
        """Get certificate validity start date."""
        return self._cert_info.get("not_before", "")

    @property
    def valid_until(self) -> str:
        """Get certificate validity end date."""
        return self._cert_info.get("not_after", "")

    @property
    def fingerprint(self) -> str:
        """Get certificate fingerprint."""
        return self._cert_info.get("fingerprint", "")

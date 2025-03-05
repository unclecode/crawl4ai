"""SSL Certificate class for handling certificate operations."""

import ssl
import socks
import socket
import base64
from datetime import datetime
import json
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import OpenSSL.crypto
from pathlib import Path
from .configs.proxy_config import ProxyConfig


class SSLCertificate:
    """
    A class representing an SSL certificate with methods to export in various formats.

    Attributes:
        cert_info (Dict[str, Any]): The certificate information.

        Methods:
            from_url(url: str, timeout: int = 10) -> Optional['SSLCertificate']: Create SSLCertificate instance from a URL.
            from_file(file_path: str) -> Optional['SSLCertificate']: Create SSLCertificate instance from a file.
            from_binary(binary_data: bytes) -> Optional['SSLCertificate']: Create SSLCertificate instance from binary data.
            export_as_pem() -> str: Export the certificate as PEM format.
            export_as_der() -> bytes: Export the certificate as DER format.
            export_as_json() -> Dict[str, Any]: Export the certificate as JSON format.
            export_as_text() -> str: Export the certificate as text format.
    """

    def __init__(self, cert_info: Dict[str, Any]):
        self._cert_info = self._decode_cert_data(cert_info)

    @staticmethod
    def from_url(
        url: str, timeout: int = 10, proxy_config: Optional[ProxyConfig] = None
    ) -> Optional["SSLCertificate"]:
        """
        Create SSLCertificate instance from a URL.

        Args:
            url (str): URL of the website.
            timeout (int): Timeout for the connection (default: 10).
            proxy_config (Optional[ProxyConfig]]): Proxy configuration (default: None).

        Returns:
            Optional[SSLCertificate]: SSLCertificate instance if successful, None otherwise.
        """
        try:
            hostname = urlparse(url).netloc
            if ":" in hostname:
                hostname = hostname.split(":")[0]

            proxy_host = proxy_port = proxy_username = proxy_password = None
            proxy_schema = "socks"

            # Setup proxy if configuration is provided
            if proxy_config:
                proxy_server = proxy_config.server
                if proxy_server:
                    parsed = urlparse(proxy_server)
                    proxy_host = parsed.hostname
                    proxy_port = parsed.port or 80
                    proxy_schema = parsed.scheme or "http"
                    proxy_username = proxy_config.username
                    proxy_password = proxy_config.password

            # Create socket based on proxy settings
            sock = None
            try:
                if proxy_host and proxy_port:
                    # Create a socks socket if proxy settings are provided
                    sock = socks.socksocket()
                    if "http" in proxy_schema.lower():
                        proxy_type = (
                            socks.HTTPS
                            if "https" in proxy_schema.lower()
                            else socks.HTTP
                        )
                        sock.set_proxy(
                            proxy_type,
                            proxy_host,
                            proxy_port,
                            username=proxy_username,
                            password=proxy_password,
                        )
                    else:
                        proxy_type = socks.SOCKS5
                        sock.set_proxy(
                            proxy_type,
                            proxy_host,
                            proxy_port,
                            username=proxy_username,
                            password=proxy_password,
                        )

                    sock.settimeout(timeout)
                    sock.connect((hostname, 443))
                else:
                    # Use regular socket without proxy
                    sock = socket.create_connection((hostname, 443), timeout=timeout)

                context = ssl.create_default_context()
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    # Transfer ownership of sock to ssock, so we don't need to close sock separately
                    sock = None

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
            finally:
                # Ensure sock is closed if it wasn't transferred to the SSL context
                if sock:
                    try:
                        sock.close()
                    except Exception:
                        pass  # Ignore any errors during closing

        except (socket.gaierror, socket.timeout):
            return None
        except socks.ProxyError:
            return None
        except Exception:
            return None

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

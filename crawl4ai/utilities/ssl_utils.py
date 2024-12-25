"""Utility functions for SSL certificate handling."""

import ssl
import socket
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import OpenSSL.crypto
import datetime
import base64


def get_ssl_certificate(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    Retrieve SSL certificate information from a given URL.
    
    Args:
        url (str): The URL to get SSL certificate from
        timeout (int): Socket timeout in seconds
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary containing certificate information or None if not available
        
    The returned dictionary includes:
        - subject: Certificate subject information
        - issuer: Certificate issuer information
        - version: SSL version
        - serial_number: Certificate serial number
        - not_before: Certificate validity start date
        - not_after: Certificate validity end date
        - fingerprint: Certificate fingerprint
        - raw_cert: Base64 encoded raw certificate data
    """
    try:
        hostname = urlparse(url).netloc
        if ':' in hostname:
            hostname = hostname.split(':')[0]
            
        context = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert_binary = ssock.getpeercert(binary_form=True)
                x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert_binary)
                
                cert_info = {
                    "subject": {
                        key: value.decode() if isinstance(value, bytes) else value
                        for key, value in dict(x509.get_subject().get_components()).items()
                    },
                    "issuer": {
                        key: value.decode() if isinstance(value, bytes) else value
                        for key, value in dict(x509.get_issuer().get_components()).items()
                    },
                    "version": x509.get_version(),
                    "serial_number": hex(x509.get_serial_number()),
                    "not_before": x509.get_notBefore().decode(),
                    "not_after": x509.get_notAfter().decode(),
                    "fingerprint": x509.digest("sha256").hex(),
                    "signature_algorithm": x509.get_signature_algorithm().decode(),
                    "raw_cert": base64.b64encode(cert_binary).decode('utf-8')
                }
                
                # Add extensions
                extensions = []
                for i in range(x509.get_extension_count()):
                    ext = x509.get_extension(i)
                    extensions.append({
                        "name": ext.get_short_name().decode(),
                        "value": str(ext)
                    })
                cert_info["extensions"] = extensions
                
                return cert_info
                
    except (socket.gaierror, socket.timeout, ssl.SSLError, ValueError) as e:
        return {
            "error": str(e),
            "status": "failed"
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "status": "failed"
        }

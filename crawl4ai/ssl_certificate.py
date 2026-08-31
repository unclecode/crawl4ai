"""SSL Certificate class for handling certificate operations."""

import ssl
import socket
import base64
import json
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import OpenSSL.crypto
from pathlib import Path

# === Inherit from dict ===
class SSLCertificate(dict):
    """
    A class representing an SSL certificate, behaving like a dictionary
    for direct JSON serialization. It stores the certificate information internally
    and provides methods for export and property access.

    Inherits from dict, so instances are directly JSON serializable.
    """

    # Use __slots__ for potential memory optimization if desired, though less common when inheriting dict
    # __slots__ = ("_cert_info",) # If using slots, be careful with dict inheritance interaction

    def __init__(self, cert_info: Dict[str, Any]):
        """
        Initializes the SSLCertificate object.

        Args:
            cert_info (Dict[str, Any]): The raw certificate dictionary.
        """
        # 1. Decode the data (handle bytes -> str)
        decoded_info = self._decode_cert_data(cert_info)

        # 2. Store the decoded info internally (optional but good practice)
        # self._cert_info = decoded_info # You can keep this if methods rely on it

        # 3. Initialize the dictionary part of the object with the decoded data
        super().__init__(decoded_info)

    @staticmethod
    def _decode_cert_data(data: Any) -> Any:
        """Helper method to decode bytes in certificate data."""
        if isinstance(data, bytes):
            try:
                # Try UTF-8 first, fallback to latin-1 for arbitrary bytes
                return data.decode("utf-8")
            except UnicodeDecodeError:
                return data.decode("latin-1") # Or handle as needed, maybe hex representation
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
    def from_url(url: str, timeout: int = 10) -> Optional["SSLCertificate"]:
        """
        Create SSLCertificate instance from a URL. Fetches cert info and initializes.
        (Fetching logic remains the same)
        """
        cert_info_raw = None # Variable to hold the fetched dict
        try:
            hostname = urlparse(url).netloc
            if ":" in hostname:
                hostname = hostname.split(":")[0]

            context = ssl.create_default_context()
            # Set check_hostname to False and verify_mode to CERT_NONE temporarily
            # for potentially problematic certificates during fetch, but parse the result regardless.
            # context.check_hostname = False
            # context.verify_mode = ssl.CERT_NONE

            with socket.create_connection((hostname, 443), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_binary = ssock.getpeercert(binary_form=True)
                    if not cert_binary:
                         print(f"Warning: No certificate returned for {hostname}")
                         return None

                    x509 = OpenSSL.crypto.load_certificate(
                        OpenSSL.crypto.FILETYPE_ASN1, cert_binary
                    )

                    # Create the dictionary directly
                    cert_info_raw = {
                        "subject": dict(x509.get_subject().get_components()),
                        "issuer": dict(x509.get_issuer().get_components()),
                        "version": x509.get_version(),
                        "serial_number": hex(x509.get_serial_number()),
                        "not_before": x509.get_notBefore(), # Keep as bytes initially, _decode handles it
                        "not_after": x509.get_notAfter(),   # Keep as bytes initially
                        "fingerprint": x509.digest("sha256").hex(), # hex() is already string
                        "signature_algorithm": x509.get_signature_algorithm(), # Keep as bytes
                        "raw_cert": base64.b64encode(cert_binary), # Base64 is bytes, _decode handles it
                    }

                    # Add extensions
                    extensions = []
                    for i in range(x509.get_extension_count()):
                        ext = x509.get_extension(i)
                        # get_short_name() returns bytes, str(ext) handles value conversion
                        extensions.append(
                            {"name": ext.get_short_name(), "value": str(ext)}
                        )
                    cert_info_raw["extensions"] = extensions

        except ssl.SSLCertVerificationError as e:
             print(f"SSL Verification Error for {url}: {e}")
             # Decide if you want to proceed or return None based on your needs
             # You might try fetching without verification here if needed, but be cautious.
             return None
        except socket.gaierror:
            print(f"Could not resolve hostname: {hostname}")
            return None
        except socket.timeout:
            print(f"Connection timed out for {url}")
            return None
        except Exception as e:
            print(f"Error fetching/processing certificate for {url}: {e}")
            # Log the full error details if needed: logging.exception("Cert fetch error")
            return None

        # If successful, create the SSLCertificate instance from the dictionary
        if cert_info_raw:
             return SSLCertificate(cert_info_raw)
        else:
             return None


    # --- Properties now access the dictionary items directly via self[] ---
    @property
    def issuer(self) -> Dict[str, str]:
        return self.get("issuer", {}) # Use self.get for safety

    @property
    def subject(self) -> Dict[str, str]:
        return self.get("subject", {})

    @property
    def valid_from(self) -> str:
        return self.get("not_before", "")

    @property
    def valid_until(self) -> str:
        return self.get("not_after", "")

    @property
    def fingerprint(self) -> str:
        return self.get("fingerprint", "")

    # --- Export methods can use `self` directly as it is the dict ---
    def to_json(self, filepath: Optional[str] = None) -> Optional[str]:
        """Export certificate as JSON."""
        # `self` is already the dictionary we want to serialize
        json_str = json.dumps(self, indent=2, ensure_ascii=False)
        if filepath:
            Path(filepath).write_text(json_str, encoding="utf-8")
            return None
        return json_str

    def to_pem(self, filepath: Optional[str] = None) -> Optional[str]:
        """Export certificate as PEM."""
        try:
            # Decode the raw_cert (which should be string due to _decode)
            raw_cert_bytes = base64.b64decode(self.get("raw_cert", ""))
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_ASN1, raw_cert_bytes
            )
            pem_data = OpenSSL.crypto.dump_certificate(
                OpenSSL.crypto.FILETYPE_PEM, x509
            ).decode("utf-8")

            if filepath:
                Path(filepath).write_text(pem_data, encoding="utf-8")
                return None
            return pem_data
        except Exception as e:
             print(f"Error converting to PEM: {e}")
             return None

    def to_der(self, filepath: Optional[str] = None) -> Optional[bytes]:
        """Export certificate as DER."""
        try:
            # Decode the raw_cert (which should be string due to _decode)
            der_data = base64.b64decode(self.get("raw_cert", ""))
            if filepath:
                Path(filepath).write_bytes(der_data)
                return None
            return der_data
        except Exception as e:
             print(f"Error converting to DER: {e}")
             return None

    # Optional: Add __repr__ for better debugging
    def __repr__(self) -> str:
        subject_cn = self.subject.get('CN', 'N/A')
        issuer_cn = self.issuer.get('CN', 'N/A')
        return f"<SSLCertificate Subject='{subject_cn}' Issuer='{issuer_cn}'>"
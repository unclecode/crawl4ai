"""Certificate fingerprints must hash DER bytes, not OpenSSL's text digest."""

import hashlib
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from crawl4ai.ssl_certificate import SSLCertificate


@pytest.mark.parametrize("serial", [1, 256])
def test_fingerprint_matches_der_sha256(monkeypatch, serial):
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "example.test")])
    now = datetime.now(timezone.utc)
    der = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(serial)
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=1))
        .sign(key, hashes.SHA256())
        .public_bytes(serialization.Encoding.DER)
    )
    context = MagicMock()
    context.wrap_socket.return_value.__enter__.return_value.getpeercert.return_value = (
        der
    )
    monkeypatch.setattr(
        "crawl4ai.ssl_certificate.ssl.create_default_context", lambda: context
    )
    monkeypatch.setattr(
        "crawl4ai.ssl_certificate.socket.create_connection", MagicMock()
    )

    certificate = SSLCertificate.from_url("https://example.test")

    assert certificate is not None
    expected = hashlib.sha256(der).hexdigest()
    assert certificate.fingerprint == expected
    assert json.loads(certificate.to_json())["fingerprint"] == expected
    assert certificate.to_der() == der
    assert (
        x509.load_pem_x509_certificate(certificate.to_pem().encode()).public_bytes(
            serialization.Encoding.DER
        )
        == der
    )

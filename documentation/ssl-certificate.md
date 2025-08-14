`SSLCertificate` Reference
==========================

The **`SSLCertificate`** class encapsulates an SSL certificate’s data and allows exporting it in various formats (PEM, DER, JSON, or text). It’s used within **Crawl4AI** whenever you set **`fetch_ssl_certificate=True`** in your **`CrawlerRunConfig`**.

1. Overview
-----------

**Location**: `crawl4ai/ssl_certificate.py`

```
class SSLCertificate:
    """
    Represents an SSL certificate with methods to export in various formats.

    Main Methods:
    - from_url(url, timeout=10)
    - from_file(file_path)
    - from_binary(binary_data)
    - to_json(filepath=None)
    - to_pem(filepath=None)
    - to_der(filepath=None)
    ...

    Common Properties:
    - issuer
    - subject
    - valid_from
    - valid_until
    - fingerprint
    """
```

### Typical Use Case

1. You **enable** certificate fetching in your crawl by:

   ```
   CrawlerRunConfig(fetch_ssl_certificate=True, ...)
   ```
2. After `arun()`, if `result.ssl_certificate` is present, it’s an instance of **`SSLCertificate`**.
3. You can **read** basic properties (issuer, subject, validity) or **export** them in multiple formats.

---

2. Construction & Fetching
--------------------------

### 2.1 **`from_url(url, timeout=10)`**

Manually load an SSL certificate from a given URL (port 443). Typically used internally, but you can call it directly if you want:

```
cert = SSLCertificate.from_url("https://example.com")
if cert:
    print("Fingerprint:", cert.fingerprint)
```

### 2.2 **`from_file(file_path)`**

Load from a file containing certificate data in ASN.1 or DER. Rarely needed unless you have local cert files:

```
cert = SSLCertificate.from_file("/path/to/cert.der")
```

### 2.3 **`from_binary(binary_data)`**

Initialize from raw binary. E.g., if you captured it from a socket or another source:

```
cert = SSLCertificate.from_binary(raw_bytes)
```

---
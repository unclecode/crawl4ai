# `SSLCertificate` Reference

The **`SSLCertificate`** class encapsulates an SSL certificate’s data and allows exporting it in various formats (PEM, DER, JSON, or text). It’s used within **Crawl4AI** whenever you set **`fetch_ssl_certificate=True`** in your **`CrawlerRunConfig`**.  

## 1. Overview

**Location**: `crawl4ai/ssl_certificate.py`

```python
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
   ```python
   CrawlerRunConfig(fetch_ssl_certificate=True, ...)
   ```
2. After `arun()`, if `result.ssl_certificate` is present, it’s an instance of **`SSLCertificate`**.  
3. You can **read** basic properties (issuer, subject, validity) or **export** them in multiple formats.

---

## 2. Construction & Fetching

### 2.1 **`from_url(url, timeout=10)`**
Manually load an SSL certificate from a given URL (port 443). Typically used internally, but you can call it directly if you want:

```python
cert = SSLCertificate.from_url("https://example.com")
if cert:
    print("Fingerprint:", cert.fingerprint)
```

### 2.2 **`from_file(file_path)`**
Load from a file containing certificate data in ASN.1 or DER. Rarely needed unless you have local cert files:

```python
cert = SSLCertificate.from_file("/path/to/cert.der")
```

### 2.3 **`from_binary(binary_data)`**
Initialize from raw binary. E.g., if you captured it from a socket or another source:

```python
cert = SSLCertificate.from_binary(raw_bytes)
```

---

## 3. Common Properties

After obtaining a **`SSLCertificate`** instance (e.g. `result.ssl_certificate` from a crawl), you can read:

1. **`issuer`** *(dict)*  
   - E.g. `{"CN": "My Root CA", "O": "..."}`
2. **`subject`** *(dict)*  
   - E.g. `{"CN": "example.com", "O": "ExampleOrg"}`
3. **`valid_from`** *(str)*  
   - NotBefore date/time. Often in ASN.1/UTC format.
4. **`valid_until`** *(str)*  
   - NotAfter date/time.
5. **`fingerprint`** *(str)*  
   - The SHA-256 digest (lowercase hex).  
   - E.g. `"d14d2e..."`

---

## 4. Export Methods

Once you have a **`SSLCertificate`** object, you can **export** or **inspect** it:

### 4.1 **`to_json(filepath=None)` → `Optional[str]`**
- Returns a JSON string containing the parsed certificate fields.  
- If `filepath` is provided, saves it to disk instead, returning `None`.

**Usage**:
```python
json_data = cert.to_json()  # returns JSON string
cert.to_json("certificate.json")  # writes file, returns None
```

### 4.2 **`to_pem(filepath=None)` → `Optional[str]`**
- Returns a PEM-encoded string (common for web servers).  
- If `filepath` is provided, saves it to disk instead.

```python
pem_str = cert.to_pem()              # in-memory PEM string
cert.to_pem("/path/to/cert.pem")     # saved to file
```

### 4.3 **`to_der(filepath=None)` → `Optional[bytes]`**
- Returns the original DER (binary ASN.1) bytes.  
- If `filepath` is specified, writes the bytes there instead.

```python
der_bytes = cert.to_der()
cert.to_der("certificate.der")
```

### 4.4 (Optional) **`export_as_text()`**
- If you see a method like `export_as_text()`, it typically returns an OpenSSL-style textual representation.  
- Not always needed, but can help for debugging or manual inspection.

---

## 5. Example Usage in Crawl4AI

Below is a minimal sample showing how the crawler obtains an SSL cert from a site, then reads or exports it. The code snippet:

```python
import asyncio
import os
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

async def main():
    tmp_dir = "tmp"
    os.makedirs(tmp_dir, exist_ok=True)

    config = CrawlerRunConfig(
        fetch_ssl_certificate=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun("https://example.com", config=config)
        if result.success and result.ssl_certificate:
            cert = result.ssl_certificate
            # 1. Basic Info
            print("Issuer CN:", cert.issuer.get("CN", ""))
            print("Valid until:", cert.valid_until)
            print("Fingerprint:", cert.fingerprint)
            
            # 2. Export
            cert.to_json(os.path.join(tmp_dir, "certificate.json"))
            cert.to_pem(os.path.join(tmp_dir, "certificate.pem"))
            cert.to_der(os.path.join(tmp_dir, "certificate.der"))
    
if __name__ == "__main__":
    asyncio.run(main())
```

---

## 6. Notes & Best Practices

1. **Timeout**: `SSLCertificate.from_url` internally uses a default **10s** socket connect and wraps SSL.  
2. **Binary Form**: The certificate is loaded in ASN.1 (DER) form, then re-parsed by `OpenSSL.crypto`.  
3. **Validation**: This does **not** validate the certificate chain or trust store. It only fetches and parses.  
4. **Integration**: Within Crawl4AI, you typically just set `fetch_ssl_certificate=True` in `CrawlerRunConfig`; the final result’s `ssl_certificate` is automatically built.  
5. **Export**: If you need to store or analyze a cert, the `to_json` and `to_pem` are quite universal.

---

### Summary

- **`SSLCertificate`** is a convenience class for capturing and exporting the **TLS certificate** from your crawled site(s).  
- Common usage is in the **`CrawlResult.ssl_certificate`** field, accessible after setting `fetch_ssl_certificate=True`.  
- Offers quick access to essential certificate details (`issuer`, `subject`, `fingerprint`) and is easy to export (PEM, DER, JSON) for further analysis or server usage.

Use it whenever you need **insight** into a site’s certificate or require some form of cryptographic or compliance check.
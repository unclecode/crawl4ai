[Crawl4AI Documentation (v0.7.x)](https://docs.crawl4ai.com/)
  * [ Home ](https://docs.crawl4ai.com/)
  * [ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/)
  * [ Quick Start ](https://docs.crawl4ai.com/core/quickstart/)
  * [ Code Examples ](https://docs.crawl4ai.com/core/examples/)
  * [ Search ](https://docs.crawl4ai.com/advanced/ssl-certificate/)


[ unclecode/crawl4ai ](https://github.com/unclecode/crawl4ai)
×
  * [Home](https://docs.crawl4ai.com/)
  * [Ask AI](https://docs.crawl4ai.com/core/ask-ai/)
  * [Quick Start](https://docs.crawl4ai.com/core/quickstart/)
  * [Code Examples](https://docs.crawl4ai.com/core/examples/)
  * Apps
    * [Demo Apps](https://docs.crawl4ai.com/apps/)
    * [C4A-Script Editor](https://docs.crawl4ai.com/apps/c4a-script/)
    * [LLM Context Builder](https://docs.crawl4ai.com/apps/llmtxt/)
  * Setup & Installation
    * [Installation](https://docs.crawl4ai.com/core/installation/)
    * [Docker Deployment](https://docs.crawl4ai.com/core/docker-deployment/)
  * Blog & Changelog
    * [Blog Home](https://docs.crawl4ai.com/blog/)
    * [Changelog](https://github.com/unclecode/crawl4ai/blob/main/CHANGELOG.md)
  * Core
    * [Command Line Interface](https://docs.crawl4ai.com/core/cli/)
    * [Simple Crawling](https://docs.crawl4ai.com/core/simple-crawling/)
    * [Deep Crawling](https://docs.crawl4ai.com/core/deep-crawling/)
    * [Adaptive Crawling](https://docs.crawl4ai.com/core/adaptive-crawling/)
    * [URL Seeding](https://docs.crawl4ai.com/core/url-seeding/)
    * [C4A-Script](https://docs.crawl4ai.com/core/c4a-script/)
    * [Crawler Result](https://docs.crawl4ai.com/core/crawler-result/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/core/browser-crawler-config/)
    * [Markdown Generation](https://docs.crawl4ai.com/core/markdown-generation/)
    * [Fit Markdown](https://docs.crawl4ai.com/core/fit-markdown/)
    * [Page Interaction](https://docs.crawl4ai.com/core/page-interaction/)
    * [Content Selection](https://docs.crawl4ai.com/core/content-selection/)
    * [Cache Modes](https://docs.crawl4ai.com/core/cache-modes/)
    * [Local Files & Raw HTML](https://docs.crawl4ai.com/core/local-files/)
    * [Link & Media](https://docs.crawl4ai.com/core/link-media/)
  * Advanced
    * [Overview](https://docs.crawl4ai.com/advanced/advanced-features/)
    * [Adaptive Strategies](https://docs.crawl4ai.com/advanced/adaptive-strategies/)
    * [Virtual Scroll](https://docs.crawl4ai.com/advanced/virtual-scroll/)
    * [File Downloading](https://docs.crawl4ai.com/advanced/file-downloading/)
    * [Lazy Loading](https://docs.crawl4ai.com/advanced/lazy-loading/)
    * [Hooks & Auth](https://docs.crawl4ai.com/advanced/hooks-auth/)
    * [Proxy & Security](https://docs.crawl4ai.com/advanced/proxy-security/)
    * [Undetected Browser](https://docs.crawl4ai.com/advanced/undetected-browser/)
    * [Session Management](https://docs.crawl4ai.com/advanced/session-management/)
    * [Multi-URL Crawling](https://docs.crawl4ai.com/advanced/multi-url-crawling/)
    * [Crawl Dispatcher](https://docs.crawl4ai.com/advanced/crawl-dispatcher/)
    * [Identity Based Crawling](https://docs.crawl4ai.com/advanced/identity-based-crawling/)
    * SSL Certificate
    * [Network & Console Capture](https://docs.crawl4ai.com/advanced/network-console-capture/)
    * [PDF Parsing](https://docs.crawl4ai.com/advanced/pdf-parsing/)
  * Extraction
    * [LLM-Free Strategies](https://docs.crawl4ai.com/extraction/no-llm-strategies/)
    * [LLM Strategies](https://docs.crawl4ai.com/extraction/llm-strategies/)
    * [Clustering Strategies](https://docs.crawl4ai.com/extraction/clustring-strategies/)
    * [Chunking](https://docs.crawl4ai.com/extraction/chunking/)
  * API Reference
    * [AsyncWebCrawler](https://docs.crawl4ai.com/api/async-webcrawler/)
    * [arun()](https://docs.crawl4ai.com/api/arun/)
    * [arun_many()](https://docs.crawl4ai.com/api/arun_many/)
    * [Browser, Crawler & LLM Config](https://docs.crawl4ai.com/api/parameters/)
    * [CrawlResult](https://docs.crawl4ai.com/api/crawl-result/)
    * [Strategies](https://docs.crawl4ai.com/api/strategies/)
    * [C4A-Script Reference](https://docs.crawl4ai.com/api/c4a-script-reference/)


* * *
  * [SSLCertificate Reference](https://docs.crawl4ai.com/advanced/ssl-certificate/#sslcertificate-reference)
  * [1. Overview](https://docs.crawl4ai.com/advanced/ssl-certificate/#1-overview)
  * [2. Construction & Fetching](https://docs.crawl4ai.com/advanced/ssl-certificate/#2-construction-fetching)
  * [3. Common Properties](https://docs.crawl4ai.com/advanced/ssl-certificate/#3-common-properties)
  * [4. Export Methods](https://docs.crawl4ai.com/advanced/ssl-certificate/#4-export-methods)
  * [5. Example Usage in Crawl4AI](https://docs.crawl4ai.com/advanced/ssl-certificate/#5-example-usage-in-crawl4ai)
  * [6. Notes & Best Practices](https://docs.crawl4ai.com/advanced/ssl-certificate/#6-notes-best-practices)


#  `SSLCertificate` Reference
The **`SSLCertificate`**class encapsulates an SSL certificate’s data and allows exporting it in various formats (PEM, DER, JSON, or text). It’s used within**Crawl4AI** whenever you set **`fetch_ssl_certificate=True`**in your**`CrawlerRunConfig`**.
## 1. Overview
**Location** : `crawl4ai/ssl_certificate.py`
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
Copy
```

### Typical Use Case
  1. You **enable** certificate fetching in your crawl by:
```
CrawlerRunConfig(fetch_ssl_certificate=True, ...)
Copy
```

  2. After `arun()`, if `result.ssl_certificate` is present, it’s an instance of **`SSLCertificate`**.
  3. You can **read** basic properties (issuer, subject, validity) or **export** them in multiple formats.


* * *
## 2. Construction & Fetching
### 2.1 **`from_url(url, timeout=10)`**
Manually load an SSL certificate from a given URL (port 443). Typically used internally, but you can call it directly if you want:
```
cert = SSLCertificate.from_url("https://example.com")
if cert:
    print("Fingerprint:", cert.fingerprint)
Copy
```

### 2.2 **`from_file(file_path)`**
Load from a file containing certificate data in ASN.1 or DER. Rarely needed unless you have local cert files:
```
cert = SSLCertificate.from_file("/path/to/cert.der")
Copy
```

### 2.3 **`from_binary(binary_data)`**
Initialize from raw binary. E.g., if you captured it from a socket or another source:
```
cert = SSLCertificate.from_binary(raw_bytes)
Copy
```

* * *
## 3. Common Properties
After obtaining a **`SSLCertificate`**instance (e.g.`result.ssl_certificate` from a crawl), you can read:
1. **`issuer`**_(dict)_
- E.g. `{"CN": "My Root CA", "O": "..."}` 2. **`subject`**_(dict)_
- E.g. `{"CN": "example.com", "O": "ExampleOrg"}` 3. **`valid_from`**_(str)_
- NotBefore date/time. Often in ASN.1/UTC format. 4. **`valid_until`**_(str)_
- NotAfter date/time. 5. **`fingerprint`**_(str)_
- The SHA-256 digest (lowercase hex).
- E.g. `"d14d2e..."`
* * *
## 4. Export Methods
Once you have a **`SSLCertificate`**object, you can**export** or **inspect** it:
### 4.1 **`to_json(filepath=None)`→`Optional[str]`**
  * Returns a JSON string containing the parsed certificate fields.
  * If `filepath` is provided, saves it to disk instead, returning `None`.


**Usage** :
```
json_data = cert.to_json()  # returns JSON string
cert.to_json("certificate.json")  # writes file, returns None
Copy
```

### 4.2 **`to_pem(filepath=None)`→`Optional[str]`**
  * Returns a PEM-encoded string (common for web servers).
  * If `filepath` is provided, saves it to disk instead.


```
pem_str = cert.to_pem()              # in-memory PEM string
cert.to_pem("/path/to/cert.pem")     # saved to file
Copy
```

### 4.3 **`to_der(filepath=None)`→`Optional[bytes]`**
  * Returns the original DER (binary ASN.1) bytes.
  * If `filepath` is specified, writes the bytes there instead.


```
der_bytes = cert.to_der()
cert.to_der("certificate.der")
Copy
```

### 4.4 (Optional) **`export_as_text()`**
  * If you see a method like `export_as_text()`, it typically returns an OpenSSL-style textual representation.
  * Not always needed, but can help for debugging or manual inspection.


* * *
## 5. Example Usage in Crawl4AI
Below is a minimal sample showing how the crawler obtains an SSL cert from a site, then reads or exports it. The code snippet:
```
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
Copy
```

* * *
## 6. Notes & Best Practices
1. **Timeout** : `SSLCertificate.from_url` internally uses a default **10s** socket connect and wraps SSL.
2. **Binary Form** : The certificate is loaded in ASN.1 (DER) form, then re-parsed by `OpenSSL.crypto`.
3. **Validation** : This does **not** validate the certificate chain or trust store. It only fetches and parses.
4. **Integration** : Within Crawl4AI, you typically just set `fetch_ssl_certificate=True` in `CrawlerRunConfig`; the final result’s `ssl_certificate` is automatically built.
5. **Export** : If you need to store or analyze a cert, the `to_json` and `to_pem` are quite universal.
* * *
### Summary
  * **`SSLCertificate`**is a convenience class for capturing and exporting the**TLS certificate** from your crawled site(s).
  * Common usage is in the **`CrawlResult.ssl_certificate`**field, accessible after setting`fetch_ssl_certificate=True`.
  * Offers quick access to essential certificate details (`issuer`, `subject`, `fingerprint`) and is easy to export (PEM, DER, JSON) for further analysis or server usage.


Use it whenever you need **insight** into a site’s certificate or require some form of cryptographic or compliance check.
#### On this page
  * [1. Overview](https://docs.crawl4ai.com/advanced/ssl-certificate/#1-overview)
  * [Typical Use Case](https://docs.crawl4ai.com/advanced/ssl-certificate/#typical-use-case)
  * [2. Construction & Fetching](https://docs.crawl4ai.com/advanced/ssl-certificate/#2-construction-fetching)
  * [2.1 from_url(url, timeout=10)](https://docs.crawl4ai.com/advanced/ssl-certificate/#21-from_urlurl-timeout10)
  * [2.2 from_file(file_path)](https://docs.crawl4ai.com/advanced/ssl-certificate/#22-from_filefile_path)
  * [2.3 from_binary(binary_data)](https://docs.crawl4ai.com/advanced/ssl-certificate/#23-from_binarybinary_data)
  * [3. Common Properties](https://docs.crawl4ai.com/advanced/ssl-certificate/#3-common-properties)
  * [4. Export Methods](https://docs.crawl4ai.com/advanced/ssl-certificate/#4-export-methods)
  * [4.1 to_json(filepath=None) → Optional[str]](https://docs.crawl4ai.com/advanced/ssl-certificate/#41-to_jsonfilepathnone-optionalstr)
  * [4.2 to_pem(filepath=None) → Optional[str]](https://docs.crawl4ai.com/advanced/ssl-certificate/#42-to_pemfilepathnone-optionalstr)
  * [4.3 to_der(filepath=None) → Optional[bytes]](https://docs.crawl4ai.com/advanced/ssl-certificate/#43-to_derfilepathnone-optionalbytes)
  * [4.4 (Optional) export_as_text()](https://docs.crawl4ai.com/advanced/ssl-certificate/#44-optional-export_as_text)
  * [5. Example Usage in Crawl4AI](https://docs.crawl4ai.com/advanced/ssl-certificate/#5-example-usage-in-crawl4ai)
  * [6. Notes & Best Practices](https://docs.crawl4ai.com/advanced/ssl-certificate/#6-notes-best-practices)
  * [Summary](https://docs.crawl4ai.com/advanced/ssl-certificate/#summary)


* * *
> Feedback
##### Search
xClose
Type to start searching
[ Ask AI ](https://docs.crawl4ai.com/core/ask-ai/ "Ask Crawl4AI Assistant")

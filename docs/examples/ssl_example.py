"""Example showing how to work with SSL certificates in Crawl4AI."""

import asyncio
import os
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

# Create tmp directory if it doesn't exist
parent_dir = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
tmp_dir = os.path.join(parent_dir, "tmp")
os.makedirs(tmp_dir, exist_ok=True)


async def main():
    # Configure crawler to fetch SSL certificate
    config = CrawlerRunConfig(
        fetch_ssl_certificate=True,
        cache_mode=CacheMode.BYPASS,  # Bypass cache to always get fresh certificates
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com", config=config)

        if result.success and result.ssl_certificate:
            cert = result.ssl_certificate

            # 1. Access certificate properties directly
            print("\nCertificate Information:")
            print(f"Issuer: {cert.issuer.get('CN', '')}")
            print(f"Valid until: {cert.valid_until}")
            print(f"Fingerprint: {cert.fingerprint}")

            # 2. Export certificate in different formats
            cert.to_json(os.path.join(tmp_dir, "certificate.json"))  # For analysis
            print("\nCertificate exported to:")
            print(f"- JSON: {os.path.join(tmp_dir, 'certificate.json')}")

            pem_data = cert.to_pem(
                os.path.join(tmp_dir, "certificate.pem")
            )  # For web servers
            print(f"- PEM: {os.path.join(tmp_dir, 'certificate.pem')}")

            der_data = cert.to_der(
                os.path.join(tmp_dir, "certificate.der")
            )  # For Java apps
            print(f"- DER: {os.path.join(tmp_dir, 'certificate.der')}")


if __name__ == "__main__":
    asyncio.run(main())

"""Example script showing how to save SSL certificates."""

import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.utilities.cert_exporter import CertificateExporter

# Get location of parent folder, then "tmp" folder if not make it
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(parent_dir, "tmp"), exist_ok=True)
__tmp_dir__ = os.path.join(parent_dir, "tmp")

async def main():
    # Configure crawler to fetch SSL certificate
    crawl_config = CrawlerRunConfig(
        fetch_ssl_certificate=True,
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url='https://example.com',
            config=crawl_config
        )
        
        if result.success and result.ssl_certificate:
            # 1. Save as JSON (most readable format)
            CertificateExporter.to_json(
                result.ssl_certificate,
                filepath=os.path.join(__tmp_dir__, "certificate.json")
            )
            print("Certificate saved in JSON format: certificate.json")
            
            # 2. Save as PEM (standard format for web servers)
            pem_data = CertificateExporter.to_pem(
                result.ssl_certificate,
                filepath=os.path.join(__tmp_dir__, "certificate.pem")
            )
            print("Certificate saved in PEM format: certificate.pem")
            
            # Print basic certificate info
            cert = result.ssl_certificate
            print("\nCertificate Information:")
            print(f"Issuer: {cert['issuer'].get(b'CN', '').decode()}")
            print(f"Valid until: {cert['not_after']}")
            print(f"Fingerprint: {cert['fingerprint']}")

if __name__ == "__main__":
    asyncio.run(main())

"""Example script demonstrating SSL certificate retrieval and export."""

import asyncio
import os
from pathlib import Path
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.utilities.cert_exporter import CertificateExporter

async def main():
    # Configure crawler to fetch SSL certificate
    crawl_config = CrawlerRunConfig(
        fetch_ssl_certificate=True,
        cache_mode=CacheMode.BYPASS
    )

    # Create output directory for certificates
    output_dir = Path("certificates")
    output_dir.mkdir(exist_ok=True)

    async with AsyncWebCrawler() as crawler:
        # Crawl a website
        result = await crawler.arun(
            url='https://example.com',
            config=crawl_config
        )
        
        if result.success and result.ssl_certificate:
            # 1. Export as JSON (human-readable format)
            json_data = CertificateExporter.to_json(
                result.ssl_certificate,
                filepath=str(output_dir / "cert.json")
            )
            
            # 2. Export as PEM (standard text format, used by Apache/Nginx)
            pem_data = CertificateExporter.to_pem(
                result.ssl_certificate,
                filepath=str(output_dir / "cert.pem")
            )
            
            # 3. Export as DER (binary format, used by Java)
            der_data = CertificateExporter.to_der(
                result.ssl_certificate,
                filepath=str(output_dir / "cert.der")
            )
            
            # 4. Export all formats at once
            export_paths = CertificateExporter.export_all(
                result.ssl_certificate,
                str(output_dir),
                "certificate"
            )
            
            print("Certificate exported in multiple formats:")
            for fmt, path in export_paths.items():
                print(f"- {fmt.upper()}: {path}")
            
            # Print some certificate information
            cert = result.ssl_certificate
            print("\nCertificate Information:")
            print(f"Subject: {cert['subject']}")
            print(f"Issuer: {cert['issuer']}")
            print(f"Valid from: {cert['not_before']}")
            print(f"Valid until: {cert['not_after']}")
            print(f"Fingerprint: {cert['fingerprint']}")

if __name__ == "__main__":
    asyncio.run(main())

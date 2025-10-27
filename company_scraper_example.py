"""
Example usage of the Company Website Scraper

This script demonstrates different ways to use the company_website_scraper module.
"""

import asyncio
import os
from company_website_scraper import CompanyWebsiteScraper


async def example_basic_scraping():
    """Example 1: Basic company website scraping"""
    print("="*80)
    print("EXAMPLE 1: Basic Scraping")
    print("="*80)

    # Initialize scraper with default settings
    scraper = CompanyWebsiteScraper(
        llm_provider="openai/gpt-4o",
        llm_api_key=os.getenv('OPENAI_API_KEY'),
        max_depth=2,
        max_pages=10,
        verbose=True
    )

    # Scrape a company website
    # Example: https://www.example-company.com
    url = "https://www.anthropic.com"  # Replace with your target URL

    result = await scraper.scrape_company(url)

    if result.success:
        # Save results
        json_path = scraper.save_results(result)
        md_path = scraper.save_markdown_summary(result)

        # Display summary
        print(f"\nCompany: {result.company_info.company_name}")
        print(f"Description: {result.company_info.description[:200]}...")
        print(f"Products/Services found: {len(result.company_info.products_services)}")
        print(f"Target Industries: {len(result.company_info.target_industries)}")
        print(f"\nFiles saved:")
        print(f"  - JSON: {json_path}")
        print(f"  - Markdown: {md_path}")
    else:
        print(f"Error: {result.error_message}")


async def example_multiple_companies():
    """Example 2: Scraping multiple companies"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Multiple Companies")
    print("="*80)

    scraper = CompanyWebsiteScraper(
        max_depth=2,
        max_pages=15,
        output_dir="./company_data",
        verbose=True
    )

    # List of company URLs to scrape
    companies = [
        "https://www.example1.com",
        "https://www.example2.com",
        "https://www.example3.com"
    ]

    results = []
    for url in companies:
        print(f"\n--- Scraping: {url} ---")
        result = await scraper.scrape_company(url)
        results.append(result)

        if result.success:
            scraper.save_results(result)
            print(f"✓ Successfully scraped {result.company_info.company_name}")
        else:
            print(f"✗ Failed to scrape {url}")

    # Summary
    print(f"\n{'='*80}")
    print(f"Scraped {sum(1 for r in results if r.success)}/{len(results)} companies successfully")
    print(f"{'='*80}")


async def example_custom_configuration():
    """Example 3: Advanced configuration with custom settings"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Custom Configuration")
    print("="*80)

    # Advanced scraper configuration
    scraper = CompanyWebsiteScraper(
        llm_provider="openai/gpt-4o-mini",  # Use cheaper model for testing
        max_depth=4,  # Deeper crawling
        max_pages=30,  # More pages
        use_stealth=True,  # Enable stealth mode
        headless=True,  # Headless browser
        output_dir="./deep_scrape_results",
        verbose=True
    )

    url = "https://www.example-manufacturing.com"  # Manufacturing company example

    result = await scraper.scrape_company(url)

    if result.success:
        company = result.company_info

        print(f"\n{'='*80}")
        print(f"DETAILED COMPANY INFORMATION")
        print(f"{'='*80}")
        print(f"Name: {company.company_name}")
        print(f"Tagline: {company.tagline}")
        print(f"Founded: {company.year_founded}")
        print(f"Size: {company.company_size}")
        print(f"HQ: {company.headquarters}")
        print(f"\nDescription:\n{company.description}")

        print(f"\n--- Products & Services ({len(company.products_services)}) ---")
        for product in company.products_services[:5]:  # First 5
            print(f"  • {product.get('name', 'Unknown')}")
            print(f"    Category: {product.get('category', 'N/A')}")
            print(f"    Target: {product.get('target_market', 'N/A')}")

        print(f"\n--- Target Industries ({len(company.target_industries)}) ---")
        for industry in company.target_industries:
            print(f"  • {industry.get('name', 'Unknown')}")

        if company.production_methods:
            print(f"\n--- Production Methods ---")
            for method in company.production_methods:
                print(f"  • {method}")

        if company.technologies_used:
            print(f"\n--- Technologies Used ---")
            for tech in company.technologies_used:
                print(f"  • {tech}")

        print(f"\n--- Pages Analyzed ({len(company.pages_analyzed)}) ---")
        for page in company.pages_analyzed:
            print(f"  • {page}")

        scraper.save_results(result)


async def example_programmatic_access():
    """Example 4: Programmatic access to scraped data"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Programmatic Data Access")
    print("="*80)

    scraper = CompanyWebsiteScraper(
        max_depth=2,
        max_pages=10,
        verbose=False  # Quiet mode
    )

    url = "https://www.example-software.com"
    result = await scraper.scrape_company(url)

    if result.success:
        company = result.company_info

        # Access data programmatically
        software_products = [
            p for p in company.products_services
            if 'software' in p.get('category', '').lower()
        ]

        print(f"Found {len(software_products)} software products")

        # Export to different formats
        import json

        # 1. Export as JSON
        with open('company_data.json', 'w') as f:
            json.dump(company.model_dump(), f, indent=2)

        # 2. Export products as CSV
        import csv
        with open('products.csv', 'w', newline='') as f:
            if company.products_services:
                writer = csv.DictWriter(f, fieldnames=company.products_services[0].keys())
                writer.writeheader()
                writer.writerows(company.products_services)

        # 3. Create summary report
        summary = {
            'company': company.company_name,
            'url': company.url,
            'product_count': len(company.products_services),
            'industry_count': len(company.target_industries),
            'has_manufacturing': bool(company.production_methods),
            'technologies': company.technologies_used or []
        }

        print("\nSummary Report:")
        print(json.dumps(summary, indent=2))


async def example_with_cookies():
    """Example 5: Handling sites that require cookies/authentication"""
    print("\n" + "="*80)
    print("EXAMPLE 5: Sites with Cookies")
    print("="*80)

    scraper = CompanyWebsiteScraper(
        use_stealth=True,  # Important for sites with bot detection
        max_depth=2,
        max_pages=10,
        verbose=True
    )

    # For sites that set cookies, the scraper will handle them automatically
    # The session_id parameter maintains state across page loads
    url = "https://www.example-protected.com"

    result = await scraper.scrape_company(
        url=url,
        session_id="persistent_session_123"  # Maintains cookies/state
    )

    if result.success:
        print(f"Successfully scraped protected site: {result.company_info.company_name}")
        scraper.save_results(result)


async def run_all_examples():
    """Run all examples"""
    # Run one example at a time
    # Uncomment the example you want to run:

    await example_basic_scraping()
    # await example_multiple_companies()
    # await example_custom_configuration()
    # await example_programmatic_access()
    # await example_with_cookies()


if __name__ == "__main__":
    # Make sure you have OPENAI_API_KEY set in your environment
    if not os.getenv('OPENAI_API_KEY'):
        print("WARNING: OPENAI_API_KEY not found in environment variables")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        print()

    asyncio.run(run_all_examples())

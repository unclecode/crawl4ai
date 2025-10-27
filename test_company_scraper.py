"""
Quick test script for the Company Website Scraper

This script performs a basic test to verify the scraper is working correctly.
"""

import asyncio
import os
import sys
from pathlib import Path


async def test_scraper_import():
    """Test 1: Verify the scraper can be imported"""
    print("Test 1: Testing import...")
    try:
        from company_website_scraper import CompanyWebsiteScraper, CompanyInformation
        print("✓ Successfully imported CompanyWebsiteScraper")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


async def test_scraper_initialization():
    """Test 2: Verify the scraper can be initialized"""
    print("\nTest 2: Testing initialization...")
    try:
        from company_website_scraper import CompanyWebsiteScraper

        scraper = CompanyWebsiteScraper(
            llm_provider="openai/gpt-4o",
            max_depth=2,
            max_pages=5,
            verbose=False
        )
        print("✓ Successfully initialized CompanyWebsiteScraper")
        print(f"  - LLM Provider: {scraper.llm_provider}")
        print(f"  - Max Depth: {scraper.max_depth}")
        print(f"  - Max Pages: {scraper.max_pages}")
        print(f"  - Output Dir: {scraper.output_dir}")
        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False


async def test_configuration():
    """Test 3: Verify configuration objects are created correctly"""
    print("\nTest 3: Testing configuration...")
    try:
        from company_website_scraper import CompanyWebsiteScraper

        scraper = CompanyWebsiteScraper(verbose=False)

        # Test browser config creation
        browser_config = scraper._create_browser_config()
        print("✓ Successfully created browser config")
        print(f"  - Stealth mode: {browser_config.enable_stealth}")
        print(f"  - Headless: {browser_config.headless}")

        # Test deep crawl strategy
        strategy = scraper._create_deep_crawl_strategy()
        print("✓ Successfully created deep crawl strategy")
        print(f"  - Max depth: {strategy.max_depth}")
        print(f"  - Max pages: {strategy.max_pages}")

        # Test extraction strategy (requires API key)
        if os.getenv('OPENAI_API_KEY'):
            extraction = scraper._create_extraction_strategy()
            print("✓ Successfully created extraction strategy")
            print(f"  - LLM Provider: {extraction.llm_config.provider}")
        else:
            print("⚠ Skipping extraction strategy test (no OPENAI_API_KEY)")

        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_live_scrape():
    """Test 4: Perform a minimal live scrape (if API key available)"""
    print("\nTest 4: Testing live scrape...")

    if not os.getenv('OPENAI_API_KEY'):
        print("⚠ Skipping live scrape test (no OPENAI_API_KEY)")
        print("  Set OPENAI_API_KEY environment variable to run this test")
        return True  # Not a failure, just skipped

    try:
        from company_website_scraper import CompanyWebsiteScraper

        print("  Initializing scraper for live test...")
        scraper = CompanyWebsiteScraper(
            max_depth=1,  # Minimal depth
            max_pages=3,  # Only a few pages
            verbose=True,
            output_dir="./test_output"
        )

        # Test with a simple, reliable website
        test_url = "https://www.anthropic.com"
        print(f"  Scraping test URL: {test_url}")

        result = await scraper.scrape_company(test_url)

        if result.success:
            print("✓ Live scrape successful!")
            print(f"  - Company: {result.company_info.company_name}")
            print(f"  - Description length: {len(result.company_info.description)} chars")
            print(f"  - Pages analyzed: {len(result.company_info.pages_analyzed)}")
            print(f"  - Products found: {len(result.company_info.products_services)}")

            # Save results
            output_file = scraper.save_results(result)
            print(f"  - Saved to: {output_file}")

            # Cleanup test output
            print("  Cleaning up test files...")
            if output_file.exists():
                output_file.unlink()
                print("  ✓ Test file removed")

            return True
        else:
            print(f"✗ Live scrape failed: {result.error_message}")
            return False

    except Exception as e:
        print(f"✗ Live scrape test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """Run all tests and provide summary"""
    print("="*80)
    print("COMPANY WEBSITE SCRAPER - TEST SUITE")
    print("="*80)

    tests = [
        ("Import Test", test_scraper_import),
        ("Initialization Test", test_scraper_initialization),
        ("Configuration Test", test_configuration),
        ("Live Scrape Test", test_live_scrape)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! The scraper is ready to use.")
        print("\nNext steps:")
        print("1. Set your OPENAI_API_KEY environment variable")
        print("2. Run: python company_website_scraper.py https://example.com")
        print("3. Check the output in ./scraped_companies/")
    else:
        print("\n⚠ Some tests failed. Please check the errors above.")

    print("="*80)

    return passed == total


if __name__ == "__main__":
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("\n⚠ WARNING: OPENAI_API_KEY environment variable not set")
        print("Some tests will be skipped. To run all tests:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        print()

    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

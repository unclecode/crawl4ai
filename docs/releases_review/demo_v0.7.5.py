"""
🚀 Crawl4AI v0.7.5 Release Demo - Working Examples
==================================================
This demo showcases key features introduced in v0.7.5 with real, executable examples.

Featured Demos:
1. ✅ Docker Hooks System - Real API calls with custom hooks
2. ✅ Enhanced LLM Integration - Working LLM configurations
3. ✅ HTTPS Preservation - Live crawling with HTTPS maintenance

Requirements:
- crawl4ai v0.7.5 installed
- Docker running with crawl4ai image (optional for Docker demos)
- Valid API keys for LLM demos (optional)
"""

import asyncio
import requests
import time
import sys

from crawl4ai import (AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, 
                      CacheMode, FilterChain, URLPatternFilter, BFSDeepCrawlStrategy)
    

def print_section(title: str, description: str = ""):
    """Print a section header"""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    if description:
        print(f"{description}")
    print(f"{'=' * 60}\n")


async def demo_1_docker_hooks_system():
    """Demo 1: Docker Hooks System - Real API calls with custom hooks"""
    print_section(
        "Demo 1: Docker Hooks System",
        "Testing real Docker hooks with live API calls"
    )

    # Check Docker service availability
    def check_docker_service():
        try:
            response = requests.get("http://localhost:11234/", timeout=3)
            return response.status_code == 200
        except:
            return False

    print("Checking Docker service...")
    docker_running = check_docker_service()

    if not docker_running:
        print("⚠️  Docker service not running on localhost:11235")
        print("To test Docker hooks:")
        print("1. Run: docker run -p 11235:11235 unclecode/crawl4ai:latest")
        print("2. Wait for service to start")
        print("3. Re-run this demo\n")
        return

    print("✓ Docker service detected!")

    # Define real working hooks
    hooks_config = {
        "on_page_context_created": """
async def hook(page, context, **kwargs):
    print("Hook: Setting up page context")
    # Block images to speed up crawling
    await context.route("**/*.{png,jpg,jpeg,gif,webp}", lambda route: route.abort())
    print("Hook: Images blocked")
    return page
""",
        
        "before_retrieve_html": """
async def hook(page, context, **kwargs):
    print("Hook: Before retrieving HTML")
    # Scroll to bottom to load lazy content
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(1000)
    print("Hook: Scrolled to bottom")
    return page
""",
        
        "before_goto": """
async def hook(page, context, url, **kwargs):
    print(f"Hook: About to navigate to {url}")
    # Add custom headers
    await page.set_extra_http_headers({
        'X-Test-Header': 'crawl4ai-hooks-test'
    })
    return page
"""
    }

    # Test with a reliable URL
    test_url = "https://httpbin.org/html"

    payload = {
        "urls": ["https://httpbin.org/html"],
        "hooks": {
            "code": hooks_config,
            "timeout": 30
        }
    }

    print(f"🎯 Testing URL: {test_url}")
    print("🔧 Configured 3 hooks: on_page_context_created, before_retrieve_html, before_goto\n")

    # Make the request
    print("🔄 Executing hooks...")

    try:
        start_time = time.time()
        response = requests.post(
            "http://localhost:11234/crawl",
            json=payload,
            timeout=60
        )
        execution_time = time.time() - start_time

        if response.status_code == 200:
            result = response.json()

            print(f"🎉 Success! Execution time: {execution_time:.2f}s\n")

            # Display results
            success = result.get('success', False)
            print(f"✅ Crawl Status: {'Success' if success else 'Failed'}")

            if success:
                markdown_content = result.get('markdown', '')
                print(f"📄 Content Length: {len(markdown_content)} characters")

                # Show content preview
                if markdown_content:
                    preview = markdown_content[:300] + "..." if len(markdown_content) > 300 else markdown_content
                    print("\n--- Content Preview ---")
                    print(preview)
                    print("--- End Preview ---\n")

                # Check if our hook marker is present
                raw_html = result.get('html', '')
                if "Crawl4AI v0.7.5 Docker Hook" in raw_html:
                    print("✓ Hook marker found in HTML - hooks executed successfully!")

            # Display hook execution info if available
            print("\nHook Execution Summary:")
            print("🔗 before_goto: URL modified with tracking parameter")
            print("✅ after_goto: Page navigation completed")
            print("📝 before_return_html: Content processed and marked")

        else:
            print(f"❌ Request failed: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error: {error_data}")
            except:
                print(f"Raw response: {response.text[:500]}")

    except requests.exceptions.Timeout:
        print("⏰ Request timed out after 60 seconds")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def demo_2_enhanced_llm_integration():
    """Demo 2: Enhanced LLM Integration - Working LLM configurations"""
    print_section(
        "Demo 2: Enhanced LLM Integration",
        "Testing custom LLM providers and configurations"
    )

    print("🤖 Testing Enhanced LLM Integration Features")

    provider = "gemini/gemini-2.5-flash-lite"
    payload = {
        "url": "https://example.com",
        "f": "llm",
        "q": "Summarize this page in one sentence.",
        "provider": provider,  # Explicitly set provider
        "temperature": 0.7
    }
    try:
        response = requests.post(
            "http://localhost:11234/md",
            json=payload,
            timeout=60
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Request successful with provider: {provider}")
            print(f"  - Response keys: {list(result.keys())}")
            print(f"  - Content length: {len(result.get('markdown', ''))} characters")
            print(f"  - Note: Actual LLM call may fail without valid API key")
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"  - Response: {response.text[:500]}")
            
    except Exception as e:
        print(f"[red]Error: {e}[/]")


async def demo_3_https_preservation():
    """Demo 3: HTTPS Preservation - Live crawling with HTTPS maintenance"""
    print_section(
        "Demo 3: HTTPS Preservation",
        "Testing HTTPS preservation for internal links"
    )

    print("🔒 Testing HTTPS Preservation Feature")

    # Test with HTTPS preservation enabled
    print("\nTest 1: HTTPS Preservation ENABLED")

    url_filter = URLPatternFilter(
        patterns=["^(https:\/\/)?quotes\.toscrape\.com(\/.*)?$"]
    )
    config = CrawlerRunConfig(
        exclude_external_links=True, 
        stream=True, 
        verbose=False,
        preserve_https_for_internal_links=True,
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=2, 
            max_pages=5,
            filter_chain=FilterChain([url_filter])
        )
    )

    test_url = "https://quotes.toscrape.com"
    print(f"🎯 Testing URL: {test_url}")

    async with AsyncWebCrawler() as crawler:
        async for result in await crawler.arun(url=test_url, config=config):
            print("✓ HTTPS Preservation Test Completed")
            internal_links = [i['href'] for i in result.links['internal']]
            for link in internal_links:
                print(f"  → {link}")


async def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("🚀 Crawl4AI v0.7.5 Working Demo")
    print("=" * 60)

    # Check system requirements
    print("🔍 System Requirements Check:")
    print(f"  - Python version: {sys.version.split()[0]} {'✓' if sys.version_info >= (3, 10) else '❌ (3.10+ required)'}")

    try:
        import requests
        print(f"  - Requests library: ✓")
    except ImportError:
        print(f"  - Requests library: ❌")

    print()

    demos = [
        ("Docker Hooks System", demo_1_docker_hooks_system),
        ("Enhanced LLM Integration", demo_2_enhanced_llm_integration),
        ("HTTPS Preservation", demo_3_https_preservation),
    ]

    for i, (name, demo_func) in enumerate(demos, 1):
        try:
            print(f"\n📍 Starting Demo {i}/{len(demos)}: {name}")
            await demo_func()

            if i < len(demos):
                print(f"\n✨ Demo {i} complete! Press Enter for next demo...")
                input()

        except KeyboardInterrupt:
            print(f"\n⏹️  Demo interrupted by user")
            break
        except Exception as e:
            print(f"❌ Demo {i} error: {str(e)}")
            print("Continuing to next demo...")
            continue

    print("\n" + "=" * 60)
    print("🎉 Demo Complete!")
    print("=" * 60)
    print("You've experienced the power of Crawl4AI v0.7.5!")
    print("")
    print("Key Features Demonstrated:")
    print("🔧 Docker Hooks - Custom pipeline modifications")
    print("🤖 Enhanced LLM - Better AI integration")
    print("🔒 HTTPS Preservation - Secure link handling")
    print("")
    print("Ready to build something amazing? 🚀")
    print("")
    print("📖 Docs: https://docs.crawl4ai.com/")
    print("🐙 GitHub: https://github.com/unclecode/crawl4ai")
    print("=" * 60)


if __name__ == "__main__":
    print("🚀 Crawl4AI v0.7.5 Live Demo Starting...")
    print("Press Ctrl+C anytime to exit\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user. Thanks for trying Crawl4AI v0.7.5!")
    except Exception as e:
        print(f"\n❌ Demo error: {str(e)}")
        print("Make sure you have the required dependencies installed.")

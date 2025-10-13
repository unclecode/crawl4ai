"""
🚀 Crawl4AI v0.7.5 Release Demo - Working Examples
==================================================
This demo showcases key features introduced in v0.7.5 with real, executable examples.

Featured Demos:
1. ✅ Docker Hooks System - Real API calls with custom hooks (string & function-based)
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
                      CacheMode, FilterChain, URLPatternFilter, BFSDeepCrawlStrategy,
                      hooks_to_string)
from crawl4ai.docker_client import Crawl4aiDockerClient
    

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
        "Testing both string-based and function-based hooks (NEW in v0.7.5!)"
    )

    # Check Docker service availability
    def check_docker_service():
        try:
            response = requests.get("http://localhost:11235/", timeout=3)
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

    # ============================================================================
    # PART 1: Traditional String-Based Hooks (Works with REST API)
    # ============================================================================
    print("\n" + "─" * 60)
    print("Part 1: String-Based Hooks (REST API)")
    print("─" * 60)

    hooks_config_string = {
        "on_page_context_created": """
async def hook(page, context, **kwargs):
    print("[String Hook] Setting up page context")
    await context.route("**/*.{png,jpg,jpeg,gif,webp}", lambda route: route.abort())
    return page
""",
        "before_retrieve_html": """
async def hook(page, context, **kwargs):
    print("[String Hook] Before retrieving HTML")
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    await page.wait_for_timeout(1000)
    return page
"""
    }

    payload = {
        "urls": ["https://httpbin.org/html"],
        "hooks": {
            "code": hooks_config_string,
            "timeout": 30
        }
    }

    print("🔧 Using string-based hooks for REST API...")
    try:
        start_time = time.time()
        response = requests.post("http://localhost:11235/crawl", json=payload, timeout=60)
        execution_time = time.time() - start_time

        if response.status_code == 200:
            result = response.json()
            print(f"✅ String-based hooks executed in {execution_time:.2f}s")
            if result.get('results') and result['results'][0].get('success'):
                html_length = len(result['results'][0].get('html', ''))
                print(f"   📄 HTML length: {html_length} characters")
        else:
            print(f"❌ Request failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

    # ============================================================================
    # PART 2: NEW Function-Based Hooks with Docker Client (v0.7.5)
    # ============================================================================
    print("\n" + "─" * 60)
    print("Part 2: Function-Based Hooks with Docker Client (✨ NEW!)")
    print("─" * 60)

    # Define hooks as regular Python functions
    async def on_page_context_created_func(page, context, **kwargs):
        """Block images to speed up crawling"""
        print("[Function Hook] Setting up page context")
        await context.route("**/*.{png,jpg,jpeg,gif,webp}", lambda route: route.abort())
        await page.set_viewport_size({"width": 1920, "height": 1080})
        return page

    async def before_goto_func(page, context, url, **kwargs):
        """Add custom headers before navigation"""
        print(f"[Function Hook] About to navigate to {url}")
        await page.set_extra_http_headers({
            'X-Crawl4AI': 'v0.7.5-function-hooks',
            'X-Test-Header': 'demo'
        })
        return page

    async def before_retrieve_html_func(page, context, **kwargs):
        """Scroll to load lazy content"""
        print("[Function Hook] Scrolling page for lazy-loaded content")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(500)
        await page.evaluate("window.scrollTo(0, 0)")
        return page

    # Use the hooks_to_string utility (can be used standalone)
    print("\n📦 Converting functions to strings with hooks_to_string()...")
    hooks_as_strings = hooks_to_string({
        "on_page_context_created": on_page_context_created_func,
        "before_goto": before_goto_func,
        "before_retrieve_html": before_retrieve_html_func
    })
    print(f"   ✓ Converted {len(hooks_as_strings)} hooks to string format")

    # OR use Docker Client which does conversion automatically!
    print("\n🐳 Using Docker Client with automatic conversion...")
    try:
        client = Crawl4aiDockerClient(base_url="http://localhost:11235")

        # Pass function objects directly - conversion happens automatically!
        results = await client.crawl(
            urls=["https://httpbin.org/html"],
            hooks={
                "on_page_context_created": on_page_context_created_func,
                "before_goto": before_goto_func,
                "before_retrieve_html": before_retrieve_html_func
            },
            hooks_timeout=30
        )

        if results and results.success:
            print(f"✅ Function-based hooks executed successfully!")
            print(f"   📄 HTML length: {len(results.html)} characters")
            print(f"   🎯 URL: {results.url}")
        else:
            print("⚠️ Crawl completed but may have warnings")

    except Exception as e:
        print(f"❌ Docker client error: {str(e)}")

    # Show the benefits
    print("\n" + "=" * 60)
    print("✨ Benefits of Function-Based Hooks:")
    print("=" * 60)
    print("✓ Full IDE support (autocomplete, syntax highlighting)")
    print("✓ Type checking and linting")
    print("✓ Easier to test and debug")
    print("✓ Reusable across projects")
    print("✓ Automatic conversion in Docker client")
    print("=" * 60)


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
            "http://localhost:11235/md",
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
    print("🔧 Docker Hooks - String-based & function-based (NEW!)")
    print("   • hooks_to_string() utility for function conversion")
    print("   • Docker client with automatic conversion")
    print("   • Full IDE support and type checking")
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

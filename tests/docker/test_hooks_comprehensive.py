#!/usr/bin/env python3
"""
Comprehensive test demonstrating all hook types from hooks_example.py
adapted for the Docker API with real URLs
"""

import requests
import json
import time
from typing import Dict, Any

API_BASE_URL = "http://localhost:11234"


def test_all_hooks_demo():
    """Demonstrate all 8 hook types with practical examples"""
    print("=" * 70)
    print("Testing: All Hooks Comprehensive Demo")
    print("=" * 70)
    
    hooks_code = {
        "on_browser_created": """
async def hook(browser, **kwargs):
    # Hook called after browser is created
    print("[HOOK] on_browser_created - Browser is ready!")
    # Browser-level configurations would go here
    return browser
""",
        
        "on_page_context_created": """
async def hook(page, context, **kwargs):
    # Hook called after a new page and context are created
    print("[HOOK] on_page_context_created - New page created!")
    
    # Set viewport size for consistent rendering
    await page.set_viewport_size({"width": 1920, "height": 1080})
    
    # Add cookies for the session (using httpbin.org domain)
    await context.add_cookies([
        {
            "name": "test_session",
            "value": "abc123xyz",
            "domain": ".httpbin.org",
            "path": "/",
            "httpOnly": True,
            "secure": True
        }
    ])
    
    # Block ads and tracking scripts to speed up crawling
    await context.route("**/*.{png,jpg,jpeg,gif,webp,svg}", lambda route: route.abort())
    await context.route("**/analytics/*", lambda route: route.abort())
    await context.route("**/ads/*", lambda route: route.abort())
    
    print("[HOOK] Viewport set, cookies added, and ads blocked")
    return page
""",
        
        "on_user_agent_updated": """
async def hook(page, context, user_agent, **kwargs):
    # Hook called when user agent is updated
    print(f"[HOOK] on_user_agent_updated - User agent: {user_agent[:50]}...")
    return page
""",
        
        "before_goto": """
async def hook(page, context, url, **kwargs):
    # Hook called before navigating to each URL
    print(f"[HOOK] before_goto - About to visit: {url}")
    
    # Add custom headers for the request
    await page.set_extra_http_headers({
        "X-Custom-Header": "crawl4ai-test",
        "Accept-Language": "en-US,en;q=0.9",
        "DNT": "1"
    })
    
    return page
""",
        
        "after_goto": """
async def hook(page, context, url, response, **kwargs):
    # Hook called after navigating to each URL
    print(f"[HOOK] after_goto - Successfully loaded: {url}")
    
    # Wait a moment for dynamic content to load
    await page.wait_for_timeout(1000)
    
    # Check if specific elements exist (with error handling)
    try:
        # For httpbin.org, wait for body element
        await page.wait_for_selector("body", timeout=2000)
        print("[HOOK] Body element found and loaded")
    except:
        print("[HOOK] Timeout waiting for body, continuing anyway")
    
    return page
""",
        
        "on_execution_started": """
async def hook(page, context, **kwargs):
    # Hook called after custom JavaScript execution
    print("[HOOK] on_execution_started - Custom JS executed!")
    
    # You could inject additional JavaScript here if needed
    await page.evaluate("console.log('[INJECTED] Hook JS running');")
    
    return page
""",
        
        "before_retrieve_html": """
async def hook(page, context, **kwargs):
    # Hook called before retrieving the HTML content
    print("[HOOK] before_retrieve_html - Preparing to get HTML")
    
    # Scroll to bottom to trigger lazy loading
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
    await page.wait_for_timeout(500)
    
    # Scroll back to top
    await page.evaluate("window.scrollTo(0, 0);")
    await page.wait_for_timeout(500)
    
    # One more scroll to middle for good measure
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2);")
    
    print("[HOOK] Scrolling completed for lazy-loaded content")
    return page
""",
        
        "before_return_html": """
async def hook(page, context, html, **kwargs):
    # Hook called before returning the HTML content
    print(f"[HOOK] before_return_html - HTML length: {len(html)} characters")
    
    # Log some page metrics
    metrics = await page.evaluate('''() => {
        return {
            images: document.images.length,
            links: document.links.length,
            scripts: document.scripts.length
        }
    }''')
    
    print(f"[HOOK] Page metrics - Images: {metrics['images']}, Links: {metrics['links']}, Scripts: {metrics['scripts']}")
    
    return page
"""
    }
    
    # Create request payload
    payload = {
        "urls": ["https://httpbin.org/html"],
        "hooks": {
            "code": hooks_code,
            "timeout": 30
        },
        "crawler_config": {
            "js_code": "window.scrollTo(0, document.body.scrollHeight);",
            "wait_for": "body",
            "cache_mode": "bypass"
        }
    }
    
    print("\nSending request with all 8 hooks...")
    start_time = time.time()
    
    response = requests.post(f"{API_BASE_URL}/crawl", json=payload)
    
    elapsed_time = time.time() - start_time
    print(f"Request completed in {elapsed_time:.2f} seconds")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ Request successful!")
        
        # Check hooks execution
        if 'hooks' in data:
            hooks_info = data['hooks']
            print("\n📊 Hooks Execution Summary:")
            print(f"  Status: {hooks_info['status']['status']}")
            print(f"  Attached hooks: {len(hooks_info['status']['attached_hooks'])}")
            
            for hook_name in hooks_info['status']['attached_hooks']:
                print(f"    ✓ {hook_name}")
            
            if 'summary' in hooks_info:
                summary = hooks_info['summary']
                print(f"\n📈 Execution Statistics:")
                print(f"  Total executions: {summary['total_executions']}")
                print(f"  Successful: {summary['successful']}")
                print(f"  Failed: {summary['failed']}")
                print(f"  Timed out: {summary['timed_out']}")
                print(f"  Success rate: {summary['success_rate']:.1f}%")
            
            if hooks_info.get('execution_log'):
                print(f"\n📝 Execution Log:")
                for log_entry in hooks_info['execution_log']:
                    status_icon = "✅" if log_entry['status'] == 'success' else "❌"
                    exec_time = log_entry.get('execution_time', 0)
                    print(f"  {status_icon} {log_entry['hook_point']}: {exec_time:.3f}s")
        
        # Check crawl results
        if 'results' in data and len(data['results']) > 0:
            print(f"\n📄 Crawl Results:")
            for result in data['results']:
                print(f"  URL: {result['url']}")
                print(f"  Success: {result.get('success', False)}")
                if result.get('html'):
                    print(f"  HTML length: {len(result['html'])} characters")
    
    else:
        print(f"❌ Error: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error details: {json.dumps(error_data, indent=2)}")
        except:
            print(f"Error text: {response.text[:500]}")


def test_authentication_flow():
    """Test a complete authentication flow with multiple hooks"""
    print("\n" + "=" * 70)
    print("Testing: Authentication Flow with Multiple Hooks")
    print("=" * 70)
    
    hooks_code = {
        "on_page_context_created": """
async def hook(page, context, **kwargs):
    print("[HOOK] Setting up authentication context")
    
    # Add authentication cookies
    await context.add_cookies([
        {
            "name": "auth_token",
            "value": "fake_jwt_token_here",
            "domain": ".httpbin.org",
            "path": "/",
            "httpOnly": True,
            "secure": True
        }
    ])
    
    # Set localStorage items (for SPA authentication)
    await page.evaluate('''
        localStorage.setItem('user_id', '12345');
        localStorage.setItem('auth_time', new Date().toISOString());
    ''')
    
    return page
""",
        
        "before_goto": """
async def hook(page, context, url, **kwargs):
    print(f"[HOOK] Adding auth headers for {url}")
    
    # Add Authorization header
    import base64
    credentials = base64.b64encode(b"user:passwd").decode('ascii')
    
    await page.set_extra_http_headers({
        'Authorization': f'Basic {credentials}',
        'X-API-Key': 'test-api-key-123'
    })
    
    return page
"""
    }
    
    payload = {
        "urls": [
            "https://httpbin.org/basic-auth/user/passwd"
        ],
        "hooks": {
            "code": hooks_code,
            "timeout": 15
        }
    }
    
    print("\nTesting authentication with httpbin endpoints...")
    response = requests.post(f"{API_BASE_URL}/crawl", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Authentication test completed")
        
        if 'results' in data:
            for i, result in enumerate(data['results']):
                print(f"\n  URL {i+1}: {result['url']}")
                if result.get('success'):
                    # Check for authentication success indicators
                    html_content = result.get('html', '')
                    if '"authenticated"' in html_content and 'true' in html_content:
                        print("    ✅ Authentication successful! Basic auth worked.")
                    else:
                        print("    ⚠️ Page loaded but auth status unclear")
                else:
                    print(f"    ❌ Failed: {result.get('error_message', 'Unknown error')}")
    else:
        print(f"❌ Error: {response.status_code}")


def test_performance_optimization_hooks():
    """Test hooks for performance optimization"""
    print("\n" + "=" * 70)
    print("Testing: Performance Optimization Hooks")
    print("=" * 70)
    
    hooks_code = {
        "on_page_context_created": """
async def hook(page, context, **kwargs):
    print("[HOOK] Optimizing page for performance")
    
    # Block resource-heavy content
    await context.route("**/*.{png,jpg,jpeg,gif,webp,svg,ico}", lambda route: route.abort())
    await context.route("**/*.{woff,woff2,ttf,otf}", lambda route: route.abort())
    await context.route("**/*.{mp4,webm,ogg,mp3,wav}", lambda route: route.abort())
    await context.route("**/googletagmanager.com/*", lambda route: route.abort())
    await context.route("**/google-analytics.com/*", lambda route: route.abort())
    await context.route("**/doubleclick.net/*", lambda route: route.abort())
    await context.route("**/facebook.com/*", lambda route: route.abort())
    
    # Disable animations and transitions
    await page.add_style_tag(content='''
        *, *::before, *::after {
            animation-duration: 0s !important;
            animation-delay: 0s !important;
            transition-duration: 0s !important;
            transition-delay: 0s !important;
        }
    ''')
    
    print("[HOOK] Performance optimizations applied")
    return page
""",
        
        "before_retrieve_html": """
async def hook(page, context, **kwargs):
    print("[HOOK] Removing unnecessary elements before extraction")
    
    # Remove ads, popups, and other unnecessary elements
    await page.evaluate('''() => {
        // Remove common ad containers
        const adSelectors = [
            '.ad', '.ads', '.advertisement', '[id*="ad-"]', '[class*="ad-"]',
            '.popup', '.modal', '.overlay', '.cookie-banner', '.newsletter-signup'
        ];
        
        adSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(el => el.remove());
        });
        
        // Remove script tags to clean up HTML
        document.querySelectorAll('script').forEach(el => el.remove());
        
        // Remove style tags we don't need
        document.querySelectorAll('style').forEach(el => el.remove());
    }''')
    
    return page
"""
    }
    
    payload = {
        "urls": ["https://httpbin.org/html"],
        "hooks": {
            "code": hooks_code,
            "timeout": 10
        }
    }
    
    print("\nTesting performance optimization hooks...")
    start_time = time.time()
    
    response = requests.post(f"{API_BASE_URL}/crawl", json=payload)
    
    elapsed_time = time.time() - start_time
    print(f"Request completed in {elapsed_time:.2f} seconds")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Performance optimization test completed")
        
        if 'results' in data and len(data['results']) > 0:
            result = data['results'][0]
            if result.get('html'):
                print(f"  HTML size: {len(result['html'])} characters")
                print("  Resources blocked, ads removed, animations disabled")
    else:
        print(f"❌ Error: {response.status_code}")


def test_content_extraction_hooks():
    """Test hooks for intelligent content extraction"""
    print("\n" + "=" * 70)
    print("Testing: Content Extraction Hooks")
    print("=" * 70)
    
    hooks_code = {
        "after_goto": """
async def hook(page, context, url, response, **kwargs):
    print(f"[HOOK] Waiting for dynamic content on {url}")
    
    # Wait for any lazy-loaded content
    await page.wait_for_timeout(2000)
    
    # Trigger any "Load More" buttons
    try:
        load_more = await page.query_selector('[class*="load-more"], [class*="show-more"], button:has-text("Load More")')
        if load_more:
            await load_more.click()
            await page.wait_for_timeout(1000)
            print("[HOOK] Clicked 'Load More' button")
    except:
        pass
    
    return page
""",
        
        "before_retrieve_html": """
async def hook(page, context, **kwargs):
    print("[HOOK] Extracting structured data")
    
    # Extract metadata
    metadata = await page.evaluate('''() => {
        const getMeta = (name) => {
            const element = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
            return element ? element.getAttribute('content') : null;
        };
        
        return {
            title: document.title,
            description: getMeta('description') || getMeta('og:description'),
            author: getMeta('author'),
            keywords: getMeta('keywords'),
            ogTitle: getMeta('og:title'),
            ogImage: getMeta('og:image'),
            canonical: document.querySelector('link[rel="canonical"]')?.href,
            jsonLd: Array.from(document.querySelectorAll('script[type="application/ld+json"]'))
                .map(el => el.textContent).filter(Boolean)
        };
    }''')
    
    print(f"[HOOK] Extracted metadata: {json.dumps(metadata, indent=2)}")
    
    # Infinite scroll handling
    for i in range(3):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await page.wait_for_timeout(1000)
        print(f"[HOOK] Scroll iteration {i+1}/3")
    
    return page
"""
    }
    
    payload = {
        "urls": ["https://httpbin.org/html", "https://httpbin.org/json"],
        "hooks": {
            "code": hooks_code,
            "timeout": 20
        }
    }
    
    print("\nTesting content extraction hooks...")
    response = requests.post(f"{API_BASE_URL}/crawl", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Content extraction test completed")
        
        if 'hooks' in data and 'summary' in data['hooks']:
            summary = data['hooks']['summary']
            print(f"  Hooks executed: {summary['successful']}/{summary['total_executions']}")
        
        if 'results' in data:
            for result in data['results']:
                print(f"\n  URL: {result['url']}")
                print(f"  Success: {result.get('success', False)}")
    else:
        print(f"❌ Error: {response.status_code}")


def main():
    """Run comprehensive hook tests"""
    print("🔧 Crawl4AI Docker API - Comprehensive Hooks Testing")
    print("Based on docs/examples/hooks_example.py")
    print("=" * 70)
    
    tests = [
        ("All Hooks Demo", test_all_hooks_demo),
        ("Authentication Flow", test_authentication_flow),
        ("Performance Optimization", test_performance_optimization_hooks),
        ("Content Extraction", test_content_extraction_hooks),
    ]
    
    for i, (name, test_func) in enumerate(tests, 1):
        print(f"\n📌 Test {i}/{len(tests)}: {name}")
        try:
            test_func()
            print(f"✅ {name} completed")
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("🎉 All comprehensive hook tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
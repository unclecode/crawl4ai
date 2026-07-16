"""
Stealth Mode Example with Crawl4AI

This example demonstrates how to use the stealth mode feature to bypass basic bot detection.
The stealth mode uses playwright-stealth to modify browser fingerprints and behaviors
that are commonly used to detect automated browsers.

Key features demonstrated:
1. Comparing crawling with and without stealth mode
2. Testing against bot detection sites
3. Accessing sites that block automated browsers
4. Best practices for stealth crawling
"""

import asyncio
import json
from typing import Dict, Any
from colorama import Fore, Style, init

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.async_logger import AsyncLogger

# Initialize colorama for colored output
init()

# Create a logger for better output
logger = AsyncLogger(verbose=True)


async def test_bot_detection(use_stealth: bool = False) -> Dict[str, Any]:
    """Test against a bot detection service"""
    
    logger.info(
        f"Testing bot detection with stealth={'ON' if use_stealth else 'OFF'}",
        tag="STEALTH"
    )
    
    # Configure browser with or without stealth
    browser_config = BrowserConfig(
        headless=False,  # Use False to see the browser in action
        enable_stealth=use_stealth,
        viewport_width=1280,
        viewport_height=800
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # JavaScript to extract bot detection results
        detection_script = """
        // Comprehensive bot detection checks
        (() => {
        const detectionResults = {
            // Basic WebDriver detection
            webdriver: navigator.webdriver,
            
            // Chrome specific
            chrome: !!window.chrome,
            chromeRuntime: !!window.chrome?.runtime,
            
            // Automation indicators
            automationControlled: navigator.webdriver,
            
            // Permissions API
            permissionsPresent: !!navigator.permissions?.query,
            
            // Plugins
            pluginsLength: navigator.plugins.length,
            pluginsArray: Array.from(navigator.plugins).map(p => p.name),
            
            // Languages
            languages: navigator.languages,
            language: navigator.language,
            
            // User agent
            userAgent: navigator.userAgent,
            
            // Screen and window properties
            screen: {
                width: screen.width,
                height: screen.height,
                availWidth: screen.availWidth,
                availHeight: screen.availHeight,
                colorDepth: screen.colorDepth,
                pixelDepth: screen.pixelDepth
            },
            
            // WebGL vendor
            webglVendor: (() => {
                try {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    const ext = gl.getExtension('WEBGL_debug_renderer_info');
                    return gl.getParameter(ext.UNMASKED_VENDOR_WEBGL);
                } catch (e) {
                    return 'Error';
                }
            })(),
            
            // Platform
            platform: navigator.platform,
            
            // Hardware concurrency
            hardwareConcurrency: navigator.hardwareConcurrency,
            
            // Device memory
            deviceMemory: navigator.deviceMemory,
            
            // Connection
            connection: navigator.connection?.effectiveType
        };
        
        // Log results for console capture
        console.log('DETECTION_RESULTS:', JSON.stringify(detectionResults, null, 2));
        
        // Return results
        return detectionResults;
        })();
        """
        
        # Crawl bot detection test page
        config = CrawlerRunConfig(
            js_code=detection_script,
            capture_console_messages=True,
            wait_until="networkidle",
            delay_before_return_html=2.0  # Give time for all checks to complete
        )
        
        result = await crawler.arun(
            url="https://bot.sannysoft.com",
            config=config
        )
        
        if result.success:
            # Extract detection results from console
            detection_data = None
            for msg in result.console_messages or []:
                if "DETECTION_RESULTS:" in msg.get("text", ""):
                    try:
                        json_str = msg["text"].replace("DETECTION_RESULTS:", "").strip()
                        detection_data = json.loads(json_str)
                    except:
                        pass
            
            # Also try to get from JavaScript execution result
            if not detection_data and result.js_execution_result:
                detection_data = result.js_execution_result
            
            return {
                "success": True,
                "url": result.url,
                "detection_data": detection_data,
                "page_title": result.metadata.get("title", ""),
                "stealth_enabled": use_stealth
            }
        else:
            return {
                "success": False,
                "error": result.error_message,
                "stealth_enabled": use_stealth
            }


async def test_cloudflare_site(use_stealth: bool = False) -> Dict[str, Any]:
    """Test accessing a Cloudflare-protected site"""
    
    logger.info(
        f"Testing Cloudflare site with stealth={'ON' if use_stealth else 'OFF'}",
        tag="STEALTH"
    )
    
    browser_config = BrowserConfig(
        headless=True,  # Cloudflare detection works better in headless mode with stealth
        enable_stealth=use_stealth,
        viewport_width=1920,
        viewport_height=1080
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        config = CrawlerRunConfig(
            wait_until="networkidle",
            page_timeout=30000,  # 30 seconds
            delay_before_return_html=3.0
        )
        
        # Test on a site that often shows Cloudflare challenges
        result = await crawler.arun(
            url="https://nowsecure.nl",
            config=config
        )
        
        # Check if we hit Cloudflare challenge
        cloudflare_detected = False
        if result.html:
            cloudflare_indicators = [
                "Checking your browser",
                "Just a moment",
                "cf-browser-verification",
                "cf-challenge",
                "ray ID"
            ]
            cloudflare_detected = any(indicator in result.html for indicator in cloudflare_indicators)
        
        return {
            "success": result.success,
            "url": result.url,
            "cloudflare_challenge": cloudflare_detected,
            "status_code": result.status_code,
            "page_title": result.metadata.get("title", "") if result.metadata else "",
            "stealth_enabled": use_stealth,
            "html_snippet": result.html[:500] if result.html else ""
        }


async def test_anti_bot_site(use_stealth: bool = False) -> Dict[str, Any]:
    """Test against sites with anti-bot measures"""
    
    logger.info(
        f"Testing anti-bot site with stealth={'ON' if use_stealth else 'OFF'}",
        tag="STEALTH"
    )
    
    browser_config = BrowserConfig(
        headless=False,
        enable_stealth=use_stealth,
        # Additional browser arguments that help with stealth
        extra_args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-features=site-per-process"
        ] if not use_stealth else []  # These are automatically applied with stealth
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Some sites check for specific behaviors
        behavior_script = """
        (async () => {
            // Simulate human-like behavior
            const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
            
            // Random mouse movement
            const moveX = Math.random() * 100;
            const moveY = Math.random() * 100;
            
            // Simulate reading time
            await sleep(1000 + Math.random() * 2000);
            
            // Scroll slightly
            window.scrollBy(0, 100 + Math.random() * 200);
            
            console.log('Human behavior simulation complete');
            return true;
        })()
        """
        
        config = CrawlerRunConfig(
            js_code=behavior_script,
            wait_until="networkidle",
            delay_before_return_html=5.0,  # Longer delay to appear more human
            capture_console_messages=True
        )
        
        # Test on a site that implements anti-bot measures
        result = await crawler.arun(
            url="https://www.g2.com/",
            config=config
        )
        
        # Check for common anti-bot blocks
        blocked_indicators = [
            "Access Denied",
            "403 Forbidden", 
            "Security Check",
            "Verify you are human",
            "captcha",
            "challenge"
        ]
        
        blocked = False
        if result.html:
            blocked = any(indicator.lower() in result.html.lower() for indicator in blocked_indicators)
        
        return {
            "success": result.success and not blocked,
            "url": result.url,
            "blocked": blocked,
            "status_code": result.status_code,
            "page_title": result.metadata.get("title", "") if result.metadata else "",
            "stealth_enabled": use_stealth
        }


async def compare_results():
    """Run all tests with and without stealth mode and compare results"""
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Crawl4AI Stealth Mode Comparison{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    # Test 1: Bot Detection
    print(f"{Fore.YELLOW}1. Bot Detection Test (bot.sannysoft.com){Style.RESET_ALL}")
    print("-" * 40)
    
    # Without stealth
    regular_detection = await test_bot_detection(use_stealth=False)
    if regular_detection["success"] and regular_detection["detection_data"]:
        print(f"{Fore.RED}Without Stealth:{Style.RESET_ALL}")
        data = regular_detection["detection_data"]
        print(f"  • WebDriver detected: {data.get('webdriver', 'Unknown')}")
        print(f"  • Chrome: {data.get('chrome', 'Unknown')}")
        print(f"  • Languages: {data.get('languages', 'Unknown')}")
        print(f"  • Plugins: {data.get('pluginsLength', 'Unknown')}")
        print(f"  • User Agent: {data.get('userAgent', 'Unknown')[:60]}...")
    
    # With stealth
    stealth_detection = await test_bot_detection(use_stealth=True)
    if stealth_detection["success"] and stealth_detection["detection_data"]:
        print(f"\n{Fore.GREEN}With Stealth:{Style.RESET_ALL}")
        data = stealth_detection["detection_data"]
        print(f"  • WebDriver detected: {data.get('webdriver', 'Unknown')}")
        print(f"  • Chrome: {data.get('chrome', 'Unknown')}")
        print(f"  • Languages: {data.get('languages', 'Unknown')}")
        print(f"  • Plugins: {data.get('pluginsLength', 'Unknown')}")
        print(f"  • User Agent: {data.get('userAgent', 'Unknown')[:60]}...")
    
    # Test 2: Cloudflare Site
    print(f"\n\n{Fore.YELLOW}2. Cloudflare Protected Site Test{Style.RESET_ALL}")
    print("-" * 40)
    
    # Without stealth
    regular_cf = await test_cloudflare_site(use_stealth=False)
    print(f"{Fore.RED}Without Stealth:{Style.RESET_ALL}")
    print(f"  • Success: {regular_cf['success']}")
    print(f"  • Cloudflare Challenge: {regular_cf['cloudflare_challenge']}")
    print(f"  • Status Code: {regular_cf['status_code']}")
    print(f"  • Page Title: {regular_cf['page_title']}")
    
    # With stealth
    stealth_cf = await test_cloudflare_site(use_stealth=True)
    print(f"\n{Fore.GREEN}With Stealth:{Style.RESET_ALL}")
    print(f"  • Success: {stealth_cf['success']}")
    print(f"  • Cloudflare Challenge: {stealth_cf['cloudflare_challenge']}")
    print(f"  • Status Code: {stealth_cf['status_code']}")
    print(f"  • Page Title: {stealth_cf['page_title']}")
    
    # Test 3: Anti-bot Site
    print(f"\n\n{Fore.YELLOW}3. Anti-Bot Site Test{Style.RESET_ALL}")
    print("-" * 40)
    
    # Without stealth
    regular_antibot = await test_anti_bot_site(use_stealth=False)
    print(f"{Fore.RED}Without Stealth:{Style.RESET_ALL}")
    print(f"  • Success: {regular_antibot['success']}")
    print(f"  • Blocked: {regular_antibot['blocked']}")
    print(f"  • Status Code: {regular_antibot['status_code']}")
    print(f"  • Page Title: {regular_antibot['page_title']}")
    
    # With stealth
    stealth_antibot = await test_anti_bot_site(use_stealth=True)
    print(f"\n{Fore.GREEN}With Stealth:{Style.RESET_ALL}")
    print(f"  • Success: {stealth_antibot['success']}")
    print(f"  • Blocked: {stealth_antibot['blocked']}")
    print(f"  • Status Code: {stealth_antibot['status_code']}")
    print(f"  • Page Title: {stealth_antibot['page_title']}")
    
    # Summary
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Summary:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"\nStealth mode helps bypass basic bot detection by:")
    print(f"  • Hiding webdriver property")
    print(f"  • Modifying browser fingerprints")
    print(f"  • Adjusting navigator properties")
    print(f"  • Emulating real browser plugin behavior")
    print(f"\n{Fore.YELLOW}Note:{Style.RESET_ALL} Stealth mode is not a silver bullet.")
    print(f"Advanced anti-bot systems may still detect automation.")
    print(f"Always respect robots.txt and website terms of service.")


async def stealth_best_practices():
    """Demonstrate best practices for using stealth mode"""
    
    print(f"\n\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Stealth Mode Best Practices{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    # Best Practice 1: Combine with realistic behavior
    print(f"{Fore.YELLOW}1. Combine with Realistic Behavior:{Style.RESET_ALL}")
    
    browser_config = BrowserConfig(
        headless=False,
        enable_stealth=True,
        viewport_width=1920,
        viewport_height=1080
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Simulate human-like behavior
        human_behavior_script = """
        (async () => {
            // Wait random time between actions
            const randomWait = () => Math.random() * 2000 + 1000;
            
            // Simulate reading
            await new Promise(resolve => setTimeout(resolve, randomWait()));
            
            // Smooth scroll
            const smoothScroll = async () => {
                const totalHeight = document.body.scrollHeight;
                const viewHeight = window.innerHeight;
                let currentPosition = 0;
                
                while (currentPosition < totalHeight - viewHeight) {
                    const scrollAmount = Math.random() * 300 + 100;
                    window.scrollBy({
                        top: scrollAmount,
                        behavior: 'smooth'
                    });
                    currentPosition += scrollAmount;
                    await new Promise(resolve => setTimeout(resolve, randomWait()));
                }
            };
            
            await smoothScroll();
            console.log('Human-like behavior simulation completed');
            return true;
        })()
        """
        
        config = CrawlerRunConfig(
            js_code=human_behavior_script,
            wait_until="networkidle",
            delay_before_return_html=3.0,
            capture_console_messages=True
        )
        
        result = await crawler.arun(
            url="https://example.com",
            config=config
        )
        
        print(f"  ✓ Simulated human-like scrolling and reading patterns")
        print(f"  ✓ Added random delays between actions")
        print(f"  ✓ Result: {result.success}")
    
    # Best Practice 2: Use appropriate viewport and user agent
    print(f"\n{Fore.YELLOW}2. Use Realistic Viewport and User Agent:{Style.RESET_ALL}")
    
    # Get a realistic user agent
    from crawl4ai.user_agent_generator import UserAgentGenerator
    ua_generator = UserAgentGenerator()
    
    browser_config = BrowserConfig(
        headless=True,
        enable_stealth=True,
        viewport_width=1920,
        viewport_height=1080,
        user_agent=ua_generator.generate(device_type="desktop", browser_type="chrome")
    )
    
    print(f"  ✓ Using realistic viewport: 1920x1080")
    print(f"  ✓ Using current Chrome user agent")
    print(f"  ✓ Stealth mode will ensure consistency")
    
    # Best Practice 3: Manage request rate
    print(f"\n{Fore.YELLOW}3. Manage Request Rate:{Style.RESET_ALL}")
    print(f"  ✓ Add delays between requests")
    print(f"  ✓ Randomize timing patterns")
    print(f"  ✓ Respect robots.txt")
    
    # Best Practice 4: Session management
    print(f"\n{Fore.YELLOW}4. Use Session Management:{Style.RESET_ALL}")
    
    browser_config = BrowserConfig(
        headless=False,
        enable_stealth=True
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Create a session for multiple requests
        session_id = "stealth_session_1"
        
        config = CrawlerRunConfig(
            session_id=session_id,
            wait_until="domcontentloaded"
        )
        
        # First request
        result1 = await crawler.arun(
            url="https://example.com",
            config=config
        )
        
        # Subsequent request reuses the same browser context
        result2 = await crawler.arun(
            url="https://example.com/about",
            config=config
        )
        
        print(f"  ✓ Reused browser session for multiple requests")
        print(f"  ✓ Maintains cookies and state between requests")
        print(f"  ✓ More efficient and realistic browsing pattern")
    
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")


async def main():
    """Run all examples"""
    
    # Run comparison tests
    await compare_results()
    
    # Show best practices
    await stealth_best_practices()
    
    print(f"\n{Fore.GREEN}Examples completed!{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}Remember:{Style.RESET_ALL}")
    print(f"• Stealth mode helps with basic bot detection")
    print(f"• Always respect website terms of service")
    print(f"• Consider rate limiting and ethical scraping practices")
    print(f"• For advanced protection, consider additional measures")


if __name__ == "__main__":
    asyncio.run(main())
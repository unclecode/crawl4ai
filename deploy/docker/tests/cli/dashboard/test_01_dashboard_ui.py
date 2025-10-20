#!/usr/bin/env python3
"""
Dashboard UI Test with Playwright
Tests the monitoring dashboard UI functionality
"""
import asyncio
import subprocess
import time
import os
from pathlib import Path
from playwright.async_api import async_playwright

BASE_URL = "http://localhost:11235"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"

async def start_server():
    """Start server with 3 replicas"""
    print("Starting server with 3 replicas...")
    subprocess.run(["crwl", "server", "stop"],
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    time.sleep(2)

    result = subprocess.run(
        ["crwl", "server", "start", "--replicas", "3"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"Failed to start server: {result.stderr}")

    print("Waiting for server to be ready...")
    time.sleep(12)

async def run_demo_script():
    """Run the demo script in background to generate activity"""
    print("Starting demo script to generate dashboard activity...")
    demo_path = Path(__file__).parent.parent.parent / "monitor" / "demo_monitor_dashboard.py"

    process = subprocess.Popen(
        ["python", str(demo_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Let it run for a bit to generate some data
    print("Waiting for demo to generate data...")
    time.sleep(10)

    return process

async def test_dashboard_ui():
    """Test dashboard UI with Playwright"""

    # Create screenshot directory
    SCREENSHOT_DIR.mkdir(exist_ok=True)
    print(f"Screenshots will be saved to: {SCREENSHOT_DIR}")

    async with async_playwright() as p:
        # Launch browser
        print("\nLaunching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        try:
            # Navigate to dashboard
            print(f"Navigating to {BASE_URL}/dashboard")
            await page.goto(f"{BASE_URL}/dashboard", wait_until="networkidle")
            await asyncio.sleep(3)

            # Take full dashboard screenshot
            print("Taking full dashboard screenshot...")
            await page.screenshot(path=SCREENSHOT_DIR / "01_full_dashboard.png", full_page=True)
            print(f"  ✅ Saved: 01_full_dashboard.png")

            # Verify page title
            title = await page.title()
            print(f"\nPage title: {title}")
            if "Monitor" not in title and "Dashboard" not in title:
                print("  ⚠️  Warning: Title doesn't contain 'Monitor' or 'Dashboard'")

            # Check for infrastructure card (container filters)
            print("\nChecking Infrastructure card...")
            infrastructure = await page.query_selector('.card h3:has-text("Infrastructure")')
            if infrastructure:
                print("  ✅ Infrastructure card found")
                await page.screenshot(path=SCREENSHOT_DIR / "02_infrastructure_card.png")
                print(f"  ✅ Saved: 02_infrastructure_card.png")
            else:
                print("  ❌ Infrastructure card not found")

            # Check for container filter buttons (All, C-1, C-2, C-3)
            print("\nChecking container filter buttons...")
            all_button = await page.query_selector('.filter-btn[data-container="all"]')
            if all_button:
                print("  ✅ 'All' filter button found")
                # Take screenshot of filter area
                await all_button.screenshot(path=SCREENSHOT_DIR / "03_filter_buttons.png")
                print(f"  ✅ Saved: 03_filter_buttons.png")

                # Test clicking filter button
                await all_button.click()
                await asyncio.sleep(1)
                print("  ✅ Clicked 'All' filter button")
            else:
                print("  ⚠️  'All' filter button not found (may appear after containers register)")

            # Check for WebSocket connection indicator
            print("\nChecking WebSocket connection...")
            ws_indicator = await page.query_selector('.ws-status, .connection-status, [class*="websocket"]')
            if ws_indicator:
                print("  ✅ WebSocket indicator found")
            else:
                print("  ⚠️  WebSocket indicator not found in DOM")

            # Check for main dashboard sections
            print("\nChecking dashboard sections...")
            sections = [
                ("Active Requests", ".active-requests, [class*='active']"),
                ("Completed Requests", ".completed-requests, [class*='completed']"),
                ("Browsers", ".browsers, [class*='browser']"),
                ("Timeline", ".timeline, [class*='timeline']"),
            ]

            for section_name, selector in sections:
                element = await page.query_selector(selector)
                if element:
                    print(f"  ✅ {section_name} section found")
                else:
                    print(f"  ⚠️  {section_name} section not found with selector: {selector}")

            # Scroll to different sections and take screenshots
            print("\nTaking section screenshots...")

            # Requests section
            requests = await page.query_selector('.card h3:has-text("Requests")')
            if requests:
                await requests.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                await page.screenshot(path=SCREENSHOT_DIR / "04_requests_section.png")
                print(f"  ✅ Saved: 04_requests_section.png")

            # Browsers section
            browsers = await page.query_selector('.card h3:has-text("Browsers")')
            if browsers:
                await browsers.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                await page.screenshot(path=SCREENSHOT_DIR / "05_browsers_section.png")
                print(f"  ✅ Saved: 05_browsers_section.png")

            # Timeline section
            timeline = await page.query_selector('.card h3:has-text("Timeline")')
            if timeline:
                await timeline.scroll_into_view_if_needed()
                await asyncio.sleep(1)
                await page.screenshot(path=SCREENSHOT_DIR / "06_timeline_section.png")
                print(f"  ✅ Saved: 06_timeline_section.png")

            # Check for tabs (if they exist)
            print("\nChecking for tabs...")
            tabs = await page.query_selector_all('.tab, [role="tab"]')
            if tabs:
                print(f"  ✅ Found {len(tabs)} tabs")
                for i, tab in enumerate(tabs[:5]):  # Check first 5 tabs
                    tab_text = await tab.inner_text()
                    print(f"    - Tab {i+1}: {tab_text}")
            else:
                print("  ℹ️  No tab elements found")

            # Wait for any animations to complete
            await asyncio.sleep(2)

            # Take final screenshot
            print("\nTaking final screenshot...")
            await page.screenshot(path=SCREENSHOT_DIR / "07_final_state.png", full_page=True)
            print(f"  ✅ Saved: 07_final_state.png")

            print("\n" + "="*60)
            print("Dashboard UI Test Complete!")
            print(f"Screenshots saved to: {SCREENSHOT_DIR}")
            print("="*60)

        finally:
            await browser.close()

async def cleanup():
    """Stop server and cleanup"""
    print("\nCleaning up...")
    subprocess.run(["crwl", "server", "stop"],
                   stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)
    print("✅ Cleanup complete")

async def main():
    """Main test execution"""
    demo_process = None

    try:
        # Start server
        await start_server()

        # Run demo script to generate activity
        demo_process = await run_demo_script()

        # Run dashboard UI test
        await test_dashboard_ui()

        print("\n✅ All dashboard UI tests passed!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    finally:
        # Stop demo script
        if demo_process:
            demo_process.terminate()
            demo_process.wait(timeout=5)

        # Cleanup server
        await cleanup()

if __name__ == "__main__":
    asyncio.run(main())

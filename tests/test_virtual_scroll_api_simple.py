#!/usr/bin/env python3
"""
Test VirtualScrollConfig with the /crawl API using existing test assets
"""

import requests
import json
import os
import http.server
import socketserver
import threading
import time
from pathlib import Path

def test_virtual_scroll_api():
    """Test the /crawl endpoint with VirtualScrollConfig using test assets"""

    # Use the existing test assets
    assets_dir = Path(__file__).parent / "docs" / "examples" / "assets"
    if not assets_dir.exists():
        print(f"❌ Assets directory not found: {assets_dir}")
        return

    # Start local server for assets
    os.chdir(assets_dir)
    port = 8081

    class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Suppress log messages

    try:
        with socketserver.TCPServer(("", port), QuietHTTPRequestHandler) as httpd:
            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()

            time.sleep(0.5)  # Give server time to start

            # Test with Twitter-like virtual scroll
            url = f"http://docs.crawl4ai.com/examples/assets/virtual_scroll_twitter_like.html"

            payload = {
                "urls": [url],
                "browser_config": {
                    "type": "BrowserConfig",
                    "params": {
                        "headless": True,
                        "viewport_width": 1280,
                        "viewport_height": 800
                    }
                },
                "crawler_config": {
                    "type": "CrawlerRunConfig",
                    "params": {
                        "virtual_scroll_config": {
                            "type": "VirtualScrollConfig",
                            "params": {
                                "container_selector": "#timeline",
                                "scroll_count": 10,
                                "scroll_by": "container_height",
                                "wait_after_scroll": 0.3
                            }
                        },
                        "cache_mode": "bypass",
                        "extraction_strategy": {
                            "type": "NoExtractionStrategy",
                            "params": {}
                        }
                    }
                }
            }

            print("Testing VirtualScrollConfig with /crawl endpoint...")
            print(f"Test URL: {url}")
            print("Payload:")
            print(json.dumps(payload, indent=2))

            response = requests.post(
                "http://localhost:11234/crawl",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60  # Longer timeout for virtual scroll
            )

            print(f"\nResponse Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("✅ Success! VirtualScrollConfig is working with the API.")
                print(f"Content length: {len(result[0]['content']['raw_content'])} characters")

                # Check if we captured multiple posts (indicating virtual scroll worked)
                content = result[0]['content']['raw_content']
                post_count = content.count("Post #")
                print(f"Found {post_count} posts in the content")

                if post_count > 5:  # Should capture more than just the initial posts
                    print("✅ Virtual scroll successfully captured additional content!")
                else:
                    print("⚠️  Virtual scroll may not have captured much additional content")

                # Print a snippet of the content
                content_preview = content[:1000] + "..." if len(content) > 1000 else content
                print(f"\nContent preview:\n{content_preview}")

            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")

    except requests.exceptions.Timeout:
        print("❌ Request timed out - virtual scroll may be taking too long")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_virtual_scroll_api()
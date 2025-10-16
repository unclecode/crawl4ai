#!/usr/bin/env python3
"""
Test script for VirtualScrollConfig with the /crawl API endpoint
"""

import requests
import json

def test_virtual_scroll_api():
    """Test the /crawl endpoint with VirtualScrollConfig"""

    # Create a simple HTML page with virtual scroll for testing
    test_html = '''
    <html>
    <head>
        <style>
            #container {
                height: 300px;
                overflow-y: auto;
                border: 1px solid #ccc;
            }
            .item {
                height: 30px;
                padding: 5px;
                border-bottom: 1px solid #eee;
            }
        </style>
    </head>
    <body>
        <h1>Virtual Scroll Test</h1>
        <div id="container">
            <div class="item">Item 1</div>
            <div class="item">Item 2</div>
            <div class="item">Item 3</div>
            <div class="item">Item 4</div>
            <div class="item">Item 5</div>
        </div>
        <script>
            // Simple script to simulate virtual scroll
            const container = document.getElementById('container');
            let itemCount = 5;

            // Add more items when scrolling
            container.addEventListener('scroll', function() {
                if (container.scrollTop + container.clientHeight >= container.scrollHeight - 10) {
                    for (let i = 0; i < 5; i++) {
                        itemCount++;
                        const newItem = document.createElement('div');
                        newItem.className = 'item';
                        newItem.textContent = `Item ${itemCount}`;
                        container.appendChild(newItem);
                    }
                }
            });

            // Initial scroll to trigger loading
            setTimeout(() => {
                container.scrollTop = container.scrollHeight;
            }, 100);
        </script>
    </body>
    </html>
    '''

    # Save the HTML to a temporary file and serve it
    import tempfile
    import os
    import http.server
    import socketserver
    import threading
    import time

    # Create temporary HTML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(test_html)
        temp_file = f.name

    # Start local server
    os.chdir(os.path.dirname(temp_file))
    port = 8080

    class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            pass  # Suppress log messages

    try:
        with socketserver.TCPServer(("", port), QuietHTTPRequestHandler) as httpd:
            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()

            time.sleep(0.5)  # Give server time to start

            # Now test the API
            url = f"http://crawl4ai.com/examples/assets/virtual_scroll_twitter_like.html"

            payload = {
                "urls": [url],
                "browser_config": {
                    "type": "BrowserConfig",
                    "params": {
                        "headless": True,
                        "viewport_width": 1920,
                        "viewport_height": 1080
                    }
                },
                "crawler_config": {
                    "type": "CrawlerRunConfig",
                    "params": {
                        "virtual_scroll_config": {
                            "type": "VirtualScrollConfig",
                            "params": {
                                "container_selector": "#container",
                                "scroll_count": 3,
                                "scroll_by": "container_height",
                                "wait_after_scroll": 0.5
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
                headers={"Content-Type": "application/json"}
            )

            print(f"\nResponse Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("✅ Success! VirtualScrollConfig is working.")
                print(f"Content length: {len(result[0]['content']['raw_content'])} characters")

                # Check if virtual scroll captured more content
                if "Item 10" in result[0]['content']['raw_content']:
                    print("✅ Virtual scroll successfully captured additional content!")
                else:
                    print("⚠️  Virtual scroll may not have worked as expected")

                # Print a snippet of the content
                content_preview = result[0]['content']['raw_content'][:500] + "..."
                print(f"\nContent preview:\n{content_preview}")

            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
    finally:
        # Cleanup
        try:
            os.unlink(temp_file)
        except:
            pass

if __name__ == "__main__":
    test_virtual_scroll_api()
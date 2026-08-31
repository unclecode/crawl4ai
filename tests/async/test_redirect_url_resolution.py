"""Test delayed redirect WITH wait_for - does link resolution use correct URL?"""
import asyncio
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

class RedirectTestHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/page-a":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            content = """
            <!DOCTYPE html>
            <html>
            <head><title>Page A</title></head>
            <body>
                <h1>Page A - Will redirect after 200ms</h1>
                <script>
                    setTimeout(function() {
                        window.location.href = '/redirect-target/';
                    }, 200);
                </script>
            </body>
            </html>
            """
            self.wfile.write(content.encode())
        elif self.path.startswith("/redirect-target"):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            content = """
            <!DOCTYPE html>
            <html>
            <head><title>Redirect Target</title></head>
            <body>
                <h1>Redirect Target</h1>
                <nav id="target-nav">
                    <a href="subpage-1">Subpage 1</a>
                    <a href="subpage-2">Subpage 2</a>
                </nav>
            </body>
            </html>
            """
            self.wfile.write(content.encode())
        else:
            self.send_response(404)
            self.end_headers()

async def main():
    import socket
    class ReuseAddrHTTPServer(HTTPServer):
        allow_reuse_address = True
    
    server = ReuseAddrHTTPServer(("localhost", 8769), RedirectTestHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    try:
        import sys
        sys.path.insert(0, '/Users/nasrin/vscode/c4ai-uc/develop')
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
        
        print("=" * 60)
        print("TEST: Delayed JS redirect WITH wait_for='css:#target-nav'")
        print("This waits for the redirect to complete")
        print("=" * 60)
        
        browser_config = BrowserConfig(headless=True, verbose=False)
        crawl_config = CrawlerRunConfig(
            cache_mode="bypass",
            wait_for="css:#target-nav"  # Wait for element on redirect target
        )
        
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url="http://localhost:8769/page-a",
                config=crawl_config
            )
            
            print(f"Original URL: http://localhost:8769/page-a")
            print(f"Redirected URL returned: {result.redirected_url}")
            print(f"HTML contains 'Redirect Target': {'Redirect Target' in result.html}")
            print()
            
            if "/redirect-target" in (result.redirected_url or ""):
                print("✓ redirected_url is CORRECT")
            else:
                print("✗ BUG #1: redirected_url is WRONG - still shows original URL!")
                
            # Check links
            all_links = []
            if isinstance(result.links, dict):
                all_links = result.links.get("internal", []) + result.links.get("external", [])
            
            print(f"\nLinks found ({len(all_links)} total):")
            bug_found = False
            for link in all_links:
                href = link.get("href", "") if isinstance(link, dict) else getattr(link, 'href', "")
                if "subpage" in href:
                    print(f"  {href}")
                    if "/page-a/" in href:
                        print("    ^^^ BUG #2: Link resolved with WRONG base URL!")
                        bug_found = True
                    elif "/redirect-target/" in href:
                        print("    ^^^ CORRECT")
            
            if not bug_found and all_links:
                print("\n✓ Link resolution is CORRECT")
                        
    finally:
        server.shutdown()

if __name__ == "__main__":
    asyncio.run(main())

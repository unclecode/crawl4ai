"""
Test virtual scroll implementation according to the design:
- Create a page with virtual scroll that replaces content
- Verify all 1000 items are captured
"""

import asyncio
import os
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, VirtualScrollConfig, CacheMode, BrowserConfig

async def test_virtual_scroll():
    """Test virtual scroll with content replacement (true virtual scroll)"""
    
    # Create test HTML with true virtual scroll that replaces content
    test_html = '''
    <html>
    <head>
        <style>
            #container {
                height: 500px;
                overflow-y: auto;
                border: 1px solid #ccc;
            }
            .item {
                height: 50px;
                padding: 10px;
                border-bottom: 1px solid #eee;
            }
        </style>
    </head>
    <body>
        <h1>Virtual Scroll Test - 1000 Items</h1>
        <div id="container"></div>
        <script>
            // True virtual scroll that REPLACES content
            const container = document.getElementById('container');
            const totalItems = 1000;
            const itemsPerPage = 10; // Only show 10 items at a time
            let currentStartIndex = 0;
            
            // All our data
            const allData = [];
            for (let i = 0; i < totalItems; i++) {
                allData.push({
                    id: i,
                    text: `Item ${i + 1} of ${totalItems} - Unique ID: ${i}`
                });
            }
            
            // Function to render current page
            function renderPage(startIndex) {
                const items = [];
                const endIndex = Math.min(startIndex + itemsPerPage, totalItems);
                
                for (let i = startIndex; i < endIndex; i++) {
                    const item = allData[i];
                    items.push(`<div class="item" data-index="${item.id}">${item.text}</div>`);
                }
                
                // REPLACE container content (virtual scroll)
                container.innerHTML = items.join('');
                currentStartIndex = startIndex;
            }
            
            // Initial render
            renderPage(0);
            
            // Handle scroll
            container.addEventListener('scroll', () => {
                const scrollTop = container.scrollTop;
                const scrollHeight = container.scrollHeight;
                const clientHeight = container.clientHeight;
                
                // Calculate which page we should show based on scroll position
                // This creates a virtual scroll effect
                if (scrollTop + clientHeight >= scrollHeight - 50) {
                    // Load next page
                    const nextIndex = currentStartIndex + itemsPerPage;
                    if (nextIndex < totalItems) {
                        renderPage(nextIndex);
                        // Reset scroll to top to continue scrolling
                        container.scrollTop = 10;
                    }
                }
            });
        </script>
    </body>
    </html>
    '''
    
    # Save test HTML to a file
    import tempfile
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(test_html)
        test_file_path = f.name
    
    httpd = None
    old_cwd = os.getcwd()
    
    try:
        # Start a simple HTTP server
        import http.server
        import socketserver
        import threading
        import random
        
        # Find available port
        for _ in range(10):
            PORT = random.randint(8000, 9999)
            try:
                Handler = http.server.SimpleHTTPRequestHandler
                os.chdir(os.path.dirname(test_file_path))
                httpd = socketserver.TCPServer(("", PORT), Handler)
                break
            except OSError:
                continue
        
        if httpd is None:
            raise RuntimeError("Could not find available port")
            
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        # Give server time to start
        await asyncio.sleep(0.5)
        
        # Configure virtual scroll
        # With 10 items per page and 1000 total, we need 100 pages
        # Let's do 120 scrolls to ensure we get everything
        virtual_config = VirtualScrollConfig(
            container_selector="#container",
            scroll_count=120,
            scroll_by="container_height",  # Scroll by container height
            wait_after_scroll=0.1  # Quick wait for test
        )
        
        config = CrawlerRunConfig(
            virtual_scroll_config=virtual_config,
            cache_mode=CacheMode.BYPASS,
            verbose=True
        )
        
        browserConfig = BrowserConfig(
            headless= False
        )
        
        async with AsyncWebCrawler(verbose=True, config=browserConfig) as crawler:
            result = await crawler.arun(
                url=f"http://localhost:{PORT}/{os.path.basename(test_file_path)}",
                config=config
            )
            
            # Count all items in the result
            import re
            items = re.findall(r'data-index="(\d+)"', result.html)
            unique_indices = sorted(set(int(idx) for idx in items))
            
            print(f"\n{'='*60}")
            print(f"TEST RESULTS:")
            print(f"HTML Length: {len(result.html)}")
            print(f"Total items found: {len(items)}")
            print(f"Unique items: {len(unique_indices)}")
            
            if unique_indices:
                print(f"Item indices: {min(unique_indices)} to {max(unique_indices)}")
                print(f"Expected: 0 to 999")
                
                # Check for gaps
                expected = set(range(1000))
                actual = set(unique_indices)
                missing = expected - actual
                
                if missing:
                    print(f"\n❌ FAILED! Missing {len(missing)} items")
                    print(f"Missing indices: {sorted(missing)[:10]}{'...' if len(missing) > 10 else ''}")
                else:
                    print(f"\n✅ SUCCESS! All 1000 items captured!")
                    
                # Show some sample items
                print(f"\nSample items from result:")
                sample_items = re.findall(r'<div class="item"[^>]*>([^<]+)</div>', result.html)[:5]
                for item in sample_items:
                    print(f"  - {item}")
            
            print(f"{'='*60}\n")
                
    finally:
        # Clean up
        if httpd:
            httpd.shutdown()
        os.chdir(old_cwd)
        os.unlink(test_file_path)

if __name__ == "__main__":
    asyncio.run(test_virtual_scroll())
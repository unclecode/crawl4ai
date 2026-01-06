
import pytest

import asyncio
import http.server
import os
import random
import re
import socketserver
import tempfile
import threading
from typing import Final

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
    VirtualScrollConfig,
)

"""
Test virtual scroll implementation:
- Create a page with virtual scroll that replaces content
- Verify all 400 items are captured
"""

NUM_ITEMS: Final = 400
NUM_ITEMS_PER_PAGE: Final = 10

@pytest.mark.asyncio
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
        <h1>Virtual Scroll Test - 400 Items</h1>
        <div id="container"></div>
        <script>
            // True virtual scroll that REPLACES content
            const container = document.getElementById('container');
            const totalItems = 400;
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
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(test_html)
        test_file_path = f.name
    
    httpd = None
    old_cwd = os.getcwd()
    
    try:
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
        virtual_config = VirtualScrollConfig(
            container_selector="#container",
            scroll_count=NUM_ITEMS // NUM_ITEMS_PER_PAGE,
            scroll_by="container_height",  # Scroll by container height
            wait_after_scroll=0.1  # Quick wait for test
        )
        
        config = CrawlerRunConfig(
            virtual_scroll_config=virtual_config,
            cache_mode=CacheMode.BYPASS,
        )
        
        browserConfig = BrowserConfig(
            headless=True
        )
        
        async with AsyncWebCrawler(config=browserConfig) as crawler:
            result = await crawler.arun(
                url=f"http://localhost:{PORT}/{os.path.basename(test_file_path)}",
                config=config
            )
            
            # Count all items in the result
            items = re.findall(r'data-index="(\d+)"', result.html)
            unique_indices = sorted(set(int(idx) for idx in items))
            
            expected = set(range(NUM_ITEMS))
            actual = set(unique_indices)
            assert expected == actual, f"Missing {len(expected - actual)} items"
                
    finally:
        # Clean up
        if httpd:
            httpd.shutdown()
        os.chdir(old_cwd)
        os.unlink(test_file_path)

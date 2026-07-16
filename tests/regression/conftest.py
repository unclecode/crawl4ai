"""
Crawl4AI Regression Test Suite - Shared Fixtures

Provides a local HTTP test server with crafted pages for deterministic testing,
plus markers for network-dependent tests against real URLs.

Usage:
    pytest tests/regression/ -v                    # all tests
    pytest tests/regression/ -v -m "not network"   # skip real URL tests
    pytest tests/regression/ -v -k "core"          # only core tests
"""

import pytest
import socket
import threading
import asyncio
import time
from aiohttp import web


# ---------------------------------------------------------------------------
# Pytest configuration
# ---------------------------------------------------------------------------

def pytest_configure(config):
    config.addinivalue_line("markers", "network: tests requiring real network access")


# ---------------------------------------------------------------------------
# Test HTML Pages
# ---------------------------------------------------------------------------

HOME_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Crawl4AI Test Home</title>
    <meta name="description" content="Regression test page for Crawl4AI">
    <meta name="keywords" content="crawl4ai, testing, regression">
    <meta property="og:title" content="Test OG Title">
    <meta property="og:description" content="Test OG description for social sharing">
    <meta property="og:image" content="/images/og-image.jpg">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Test Twitter Title">
</head>
<body>
    <nav>
        <a href="/">Home</a>
        <a href="/products">Products</a>
        <a href="/links-page">Links</a>
        <a href="/tables">Tables</a>
    </nav>
    <main>
        <h1>Welcome to the Crawl4AI Test Site</h1>
        <p>This is a comprehensive test page designed for regression testing of the
        Crawl4AI web crawling library. It contains various HTML elements to verify
        content extraction, markdown generation, and link discovery work correctly.</p>

        <h2>Features Overview</h2>
        <p>The test suite covers multiple aspects of web crawling including content
        extraction, JavaScript execution, screenshot capture, and deep crawling
        capabilities. Each feature is tested both with local pages and real URLs.</p>

        <ul>
            <li>Content extraction and markdown generation</li>
            <li>Link discovery and classification</li>
            <li>Image extraction and scoring</li>
            <li>Table extraction and validation</li>
        </ul>

        <h2>Code Example</h2>
        <pre><code>from crawl4ai import AsyncWebCrawler

async with AsyncWebCrawler() as crawler:
    result = await crawler.arun("https://example.com")
    print(result.markdown)</code></pre>

        <p>Contact us at <a href="mailto:test@example.com">test@example.com</a> for more info.</p>

        <h3>Internal Links</h3>
        <a href="/page-alpha">Alpha Page</a>
        <a href="/page-beta">Beta Page</a>

        <h3>External Links</h3>
        <a href="https://example.com">Example.com</a>
        <a href="https://github.com/unclecode/crawl4ai">Crawl4AI GitHub</a>

        <img src="/images/hero.jpg" alt="Hero image for testing" width="800" height="400">
        <img src="/images/icon.png" alt="" width="16" height="16">
    </main>
    <footer>
        <p>Footer content - should be excluded with excluded_tags</p>
    </footer>
</body>
</html>"""

PRODUCTS_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Product Listing</title>
    <meta name="description" content="Test product listing page">
</head>
<body>
    <h1>Products</h1>
    <div class="product-list">
        <div class="product" data-id="1">
            <h2 class="name">Wireless Mouse</h2>
            <span class="price">$29.99</span>
            <div class="rating" data-stars="4.5">4.5 stars</div>
            <p class="description">Ergonomic wireless mouse with precision tracking</p>
            <span class="category">Electronics</span>
            <a href="/product/1" class="details-link">View Details</a>
        </div>
        <div class="product" data-id="2">
            <h2 class="name">Mechanical Keyboard</h2>
            <span class="price">$89.99</span>
            <div class="rating" data-stars="4.8">4.8 stars</div>
            <p class="description">Cherry MX switches with RGB backlighting</p>
            <span class="category">Electronics</span>
            <a href="/product/2" class="details-link">View Details</a>
        </div>
        <div class="product" data-id="3">
            <h2 class="name">USB-C Hub</h2>
            <span class="price">$45.50</span>
            <div class="rating" data-stars="4.2">4.2 stars</div>
            <p class="description">7-in-1 hub with HDMI, USB-A, SD card reader</p>
            <span class="category">Accessories</span>
            <a href="/product/3" class="details-link">View Details</a>
        </div>
        <div class="product" data-id="4">
            <h2 class="name">Monitor Stand</h2>
            <span class="price">$34.99</span>
            <div class="rating" data-stars="3.9">3.9 stars</div>
            <p class="description">Adjustable aluminum monitor riser with storage</p>
            <span class="category">Furniture</span>
            <a href="/product/4" class="details-link">View Details</a>
        </div>
        <div class="product" data-id="5">
            <h2 class="name">Webcam HD</h2>
            <span class="price">$59.00</span>
            <div class="rating" data-stars="4.6">4.6 stars</div>
            <p class="description">1080p webcam with built-in microphone and privacy cover</p>
            <span class="category">Electronics</span>
            <a href="/product/5" class="details-link">View Details</a>
        </div>
    </div>
</body>
</html>"""

TABLES_HTML = """\
<!DOCTYPE html>
<html>
<head><title>Tables Test</title></head>
<body>
    <h1>Data Tables</h1>

    <h2>Sales Report</h2>
    <table id="sales-table">
        <thead>
            <tr><th>Quarter</th><th>Revenue</th><th>Growth</th></tr>
        </thead>
        <tbody>
            <tr><td>Q1 2025</td><td>$1,234,567</td><td>12.5%</td></tr>
            <tr><td>Q2 2025</td><td>$1,456,789</td><td>18.0%</td></tr>
            <tr><td>Q3 2025</td><td>$1,678,901</td><td>15.2%</td></tr>
            <tr><td>Q4 2025</td><td>$1,890,123</td><td>12.6%</td></tr>
        </tbody>
    </table>

    <h2>Layout Table (should be filtered)</h2>
    <table id="layout-table">
        <tr><td>Left column</td><td>Right column</td></tr>
    </table>

    <h2>Employee Directory</h2>
    <table id="employee-table">
        <thead>
            <tr><th>Name</th><th>Email</th><th>Department</th><th>Phone</th></tr>
        </thead>
        <tbody>
            <tr><td>Alice Johnson</td><td>alice@example.com</td><td>Engineering</td><td>+1-555-0101</td></tr>
            <tr><td>Bob Smith</td><td>bob@example.com</td><td>Marketing</td><td>+1-555-0102</td></tr>
            <tr><td>Carol White</td><td>carol@example.com</td><td>Sales</td><td>+1-555-0103</td></tr>
        </tbody>
    </table>
</body>
</html>"""

JS_DYNAMIC_HTML = """\
<!DOCTYPE html>
<html>
<head><title>JS Dynamic Content</title></head>
<body>
    <div id="static-content">
        <h1>Static Section</h1>
        <p>This content is immediately available in the HTML.</p>
    </div>
    <div id="dynamic-content"></div>
    <div id="counter">0</div>
    <script>
        setTimeout(function() {
            document.getElementById('dynamic-content').innerHTML =
                '<p class="js-loaded">Dynamic content successfully loaded via JavaScript</p>' +
                '<ul><li>Item A</li><li>Item B</li><li>Item C</li></ul>';
        }, 300);
        setTimeout(function() {
            document.getElementById('counter').textContent = '42';
        }, 200);
    </script>
</body>
</html>"""

LINKS_HTML = """\
<!DOCTYPE html>
<html>
<head><title>Links Collection</title></head>
<body>
    <h1>Link Collection Page</h1>
    <nav>
        <h2>Internal Navigation</h2>
        <a href="/">Home</a>
        <a href="/products">Products</a>
        <a href="/tables">Tables</a>
        <a href="/about">About Us</a>
        <a href="/contact">Contact</a>
        <a href="/blog/post-1">Blog Post 1</a>
        <a href="/blog/post-2">Blog Post 2</a>
        <a href="/docs/api">API Docs</a>
        <a href="/docs/guide">User Guide</a>
    </nav>
    <section>
        <h2>External Resources</h2>
        <a href="https://example.com">Example Domain</a>
        <a href="https://github.com">GitHub</a>
        <a href="https://python.org">Python</a>
        <a href="https://docs.python.org/3/">Python Docs</a>
    </section>
    <section>
        <h2>Social Media</h2>
        <a href="https://twitter.com/example">Twitter</a>
        <a href="https://facebook.com/example">Facebook</a>
        <a href="https://linkedin.com/company/example">LinkedIn</a>
    </section>
    <section>
        <h2>Duplicate Links</h2>
        <a href="/">Home Again</a>
        <a href="https://example.com">Example Again</a>
    </section>
</body>
</html>"""

IMAGES_HTML = """\
<!DOCTYPE html>
<html>
<head><title>Images Gallery</title></head>
<body>
    <h1>Image Gallery</h1>

    <!-- High-quality image: should score high (large, has alt, common format) -->
    <div class="hero">
        <img src="/images/landscape.jpg" alt="Beautiful mountain landscape at sunset"
             width="1200" height="800">
        <p>A stunning landscape photograph showcasing the beauty of mountain scenery
        at golden hour. This image demonstrates proper extraction of high-quality
        photographs with descriptive alt text and surrounding context.</p>
    </div>

    <!-- Medium quality: decent size, has alt -->
    <img src="/images/product-photo.png" alt="Product photograph" width="400" height="300">

    <!-- Low quality: small icon, no alt -->
    <img src="/images/icon-search.svg" alt="" width="24" height="24">

    <!-- Lazy-loaded image -->
    <img data-src="/images/lazy-photo.webp" alt="Lazy loaded image" width="600" height="400"
         class="lazyload" src="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==">

    <!-- Image with srcset -->
    <img src="/images/responsive-sm.jpg"
         srcset="/images/responsive-sm.jpg 480w, /images/responsive-md.jpg 800w, /images/responsive-lg.jpg 1200w"
         alt="Responsive image with srcset" width="800" height="600">

    <!-- Button icon (should be filtered) -->
    <button><img src="/images/btn-submit.png" alt="submit" width="100" height="30"></button>

    <!-- Logo (should be filtered by pattern) -->
    <img src="/images/company-logo.png" alt="Company Logo" width="200" height="50">
</body>
</html>"""

STRUCTURED_DATA_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <title>Article with Structured Data</title>
    <meta name="description" content="An article about web crawling techniques">
    <meta property="og:title" content="Web Crawling Best Practices">
    <meta property="og:description" content="Learn about modern web crawling">
    <meta property="og:image" content="/images/article-cover.jpg">
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="2025-06-15T10:00:00Z">
    <meta property="article:modified_time" content="2025-07-20T14:30:00Z">
    <meta name="twitter:card" content="summary_large_image">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "Web Crawling Best Practices",
        "author": {"@type": "Person", "name": "Test Author"},
        "datePublished": "2025-06-15",
        "description": "A comprehensive guide to web crawling"
    }
    </script>
</head>
<body>
    <article>
        <h1>Web Crawling Best Practices</h1>
        <p class="byline">By Test Author | Published June 15, 2025</p>
        <p>Web crawling is the process of systematically browsing the web to extract
        information. Modern crawlers like Crawl4AI provide sophisticated tools for
        content extraction, including markdown generation, structured data extraction,
        and intelligent link following.</p>
        <h2>Key Techniques</h2>
        <p>Understanding how to properly configure a web crawler is essential for
        efficient data collection. This includes setting appropriate delays, respecting
        robots.txt, and using proper user agents.</p>
    </article>
</body>
</html>"""

EMPTY_HTML = """\
<!DOCTYPE html>
<html><head><title>Empty Page</title></head>
<body></body>
</html>"""

MALFORMED_HTML = """\
<html>
<head><title>Malformed Page</head>
<body>
<div>
<p>Unclosed paragraph
<p>Another paragraph without closing
<img src="/test.jpg" alt="no closing bracket"
<a href="/broken>Broken link</a>
<div><span>Nested but unclosed
<table><tr><td>Cell without closing tags
</body>
</html>"""

REGEX_TEST_HTML = """\
<!DOCTYPE html>
<html>
<head><title>Regex Test Content</title></head>
<body>
    <h1>Contact Information</h1>
    <p>Email us at support@crawl4ai.com or sales@example.org for inquiries.</p>
    <p>Call us: +1-555-123-4567 or (800) 555-0199</p>
    <p>Visit https://crawl4ai.com or https://docs.crawl4ai.com/api/v2</p>
    <p>Server IP: 192.168.1.100</p>
    <p>Request ID: 550e8400-e29b-41d4-a716-446655440000</p>
    <p>Price: $199.99 or EUR 175.50</p>
    <p>Completion rate: 95.7%</p>
    <p>Published: 2025-03-15</p>
    <p>Updated: 03/15/2025</p>
    <p>Meeting at 14:30 or 09:00</p>
    <p>Zip code: 94105 or 94105-1234</p>
    <p>Follow @crawl4ai on social media</p>
    <p>Tags: #WebCrawling #DataExtraction #Python</p>
    <p>Color theme: #FF5733</p>
</body>
</html>"""


def _generate_large_html(num_sections=50):
    """Generate a large HTML page with many sections."""
    sections = []
    for i in range(num_sections):
        sections.append(f"""
        <section id="section-{i}">
            <h2>Section {i}: Important Topic Number {i}</h2>
            <p>This is paragraph one of section {i}. It contains enough text to be
            meaningful for content extraction and markdown generation testing purposes.
            The crawler should properly handle large pages with many sections.</p>
            <p>This is paragraph two of section {i}. It provides additional context
            and detail about topic {i}, ensuring that the content extraction pipeline
            can handle substantial amounts of text without issues.</p>
            <a href="/section/{i}">Read more about topic {i}</a>
        </section>""")
    return f"""\
<!DOCTYPE html>
<html>
<head><title>Large Page with Many Sections</title></head>
<body>
    <h1>Comprehensive Document</h1>
    {"".join(sections)}
</body>
</html>"""

LARGE_HTML = _generate_large_html(50)


# Deep crawl pages: hub -> sub1,sub2,sub3 -> leaf pages
DEEP_HUB_HTML = """\
<!DOCTYPE html>
<html>
<head><title>Deep Crawl Hub</title></head>
<body>
    <h1>Hub Page</h1>
    <p>This is the starting point for deep crawl testing.</p>
    <nav>
        <a href="/deep/sub1">Sub Page 1 - Technology</a>
        <a href="/deep/sub2">Sub Page 2 - Science</a>
        <a href="/deep/sub3">Sub Page 3 - Arts</a>
    </nav>
</body>
</html>"""

DEEP_SUB_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head><title>Deep Crawl - {title}</title></head>
<body>
    <h1>{title}</h1>
    <p>Content about {title}. This sub-page contains links to deeper content.</p>
    <a href="/deep/{prefix}/leaf-a">Leaf A under {title}</a>
    <a href="/deep/{prefix}/leaf-b">Leaf B under {title}</a>
    <a href="/deep/hub">Back to Hub</a>
</body>
</html>"""

DEEP_LEAF_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head><title>Deep Crawl - {title}</title></head>
<body>
    <h1>{title}</h1>
    <p>This is a leaf page in the deep crawl hierarchy. It contains substantial
    content about {title} to ensure proper extraction at all crawl depths.
    The adaptive crawler should find and process this content correctly.</p>
    <a href="/deep/hub">Back to Hub</a>
</body>
</html>"""

IFRAME_HTML = """\
<!DOCTYPE html>
<html>
<head><title>Page with Iframes</title></head>
<body>
    <h1>Main Page Content</h1>
    <p>This page contains embedded iframes for testing iframe processing.</p>
    <iframe id="frame1" srcdoc="<html><body><p>Iframe 1 content: embedded text</p></body></html>"
            width="400" height="200"></iframe>
    <iframe id="frame2" srcdoc="<html><body><h2>Iframe 2 heading</h2><p>More embedded content here</p></body></html>"
            width="400" height="200"></iframe>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Server Handlers
# ---------------------------------------------------------------------------

async def _serve_html(html, content_type="text/html"):
    return web.Response(text=html, content_type=content_type)


async def _home_handler(request):
    return await _serve_html(HOME_HTML)

async def _products_handler(request):
    return await _serve_html(PRODUCTS_HTML)

async def _tables_handler(request):
    return await _serve_html(TABLES_HTML)

async def _js_dynamic_handler(request):
    return await _serve_html(JS_DYNAMIC_HTML)

async def _links_handler(request):
    return await _serve_html(LINKS_HTML)

async def _images_handler(request):
    return await _serve_html(IMAGES_HTML)

async def _structured_handler(request):
    return await _serve_html(STRUCTURED_DATA_HTML)

async def _empty_handler(request):
    return await _serve_html(EMPTY_HTML)

async def _malformed_handler(request):
    return await _serve_html(MALFORMED_HTML)

async def _regex_test_handler(request):
    return await _serve_html(REGEX_TEST_HTML)

async def _large_handler(request):
    return await _serve_html(LARGE_HTML)

async def _iframe_handler(request):
    return await _serve_html(IFRAME_HTML)

async def _redirect_handler(request):
    raise web.HTTPFound("/")

async def _not_found_handler(request):
    return web.Response(
        text="<html><head><title>404 Not Found</title></head>"
             "<body><h1>Page Not Found</h1><p>The requested page does not exist.</p></body></html>",
        status=404, content_type="text/html",
    )

async def _slow_handler(request):
    await asyncio.sleep(2)
    return await _serve_html(
        "<html><head><title>Slow Page</title></head>"
        "<body><h1>Slow Response</h1><p>This page had a 2-second delay.</p></body></html>"
    )

async def _deep_hub_handler(request):
    return await _serve_html(DEEP_HUB_HTML)

async def _deep_sub_handler(request):
    sub_id = request.match_info["sub_id"]
    titles = {"sub1": "Technology", "sub2": "Science", "sub3": "Arts"}
    title = titles.get(sub_id, f"Sub {sub_id}")
    html = DEEP_SUB_TEMPLATE.format(title=title, prefix=sub_id)
    return await _serve_html(html)

async def _deep_leaf_handler(request):
    sub_id = request.match_info["sub_id"]
    leaf_id = request.match_info["leaf_id"]
    title = f"Leaf {leaf_id} under {sub_id}"
    html = DEEP_LEAF_TEMPLATE.format(title=title)
    return await _serve_html(html)

async def _catch_all_handler(request):
    """Serve a simple page for any unmatched path (useful for link targets)."""
    path = request.path
    return await _serve_html(
        f"<html><head><title>Page: {path}</title></head>"
        f"<body><h1>Page at {path}</h1>"
        f"<p>Auto-generated page for path: {path}</p>"
        f'<a href="/">Back to Home</a></body></html>'
    )


# ---------------------------------------------------------------------------
# Server Setup
# ---------------------------------------------------------------------------

def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _create_app():
    app = web.Application()
    app.router.add_get("/", _home_handler)
    app.router.add_get("/products", _products_handler)
    app.router.add_get("/tables", _tables_handler)
    app.router.add_get("/js-dynamic", _js_dynamic_handler)
    app.router.add_get("/links-page", _links_handler)
    app.router.add_get("/images-page", _images_handler)
    app.router.add_get("/structured-data", _structured_handler)
    app.router.add_get("/empty", _empty_handler)
    app.router.add_get("/malformed", _malformed_handler)
    app.router.add_get("/regex-test", _regex_test_handler)
    app.router.add_get("/large", _large_handler)
    app.router.add_get("/iframe-page", _iframe_handler)
    app.router.add_get("/redirect", _redirect_handler)
    app.router.add_get("/not-found", _not_found_handler)
    app.router.add_get("/slow", _slow_handler)
    app.router.add_get("/deep/hub", _deep_hub_handler)
    app.router.add_get("/deep/{sub_id}", _deep_sub_handler)
    app.router.add_get("/deep/{sub_id}/{leaf_id}", _deep_leaf_handler)
    # Catch-all for auto-generated pages (internal link targets, etc.)
    app.router.add_get("/{path:.*}", _catch_all_handler)
    return app


def _run_server(app, host, port, ready_event):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    runner = web.AppRunner(app)
    loop.run_until_complete(runner.setup())
    site = web.TCPSite(runner, host, port)
    loop.run_until_complete(site.start())
    ready_event.set()
    try:
        loop.run_forever()
    finally:
        loop.run_until_complete(runner.cleanup())
        loop.close()


@pytest.fixture(scope="session")
def local_server():
    """Start a local HTTP test server. Returns base URL like 'http://localhost:PORT'."""
    port = _find_free_port()
    app = _create_app()
    ready = threading.Event()
    thread = threading.Thread(
        target=_run_server,
        args=(app, "localhost", port, ready),
        daemon=True,
    )
    thread.start()
    assert ready.wait(timeout=10), "Test server failed to start within 10 seconds"
    # Small delay to ensure server is fully ready
    time.sleep(0.2)
    yield f"http://localhost:{port}"
    # Daemon thread cleans up automatically


# ---------------------------------------------------------------------------
# Common test constants
# ---------------------------------------------------------------------------

# Stable real URLs for network tests
REAL_URL_SIMPLE = "https://example.com"
REAL_URL_QUOTES = "https://quotes.toscrape.com"
REAL_URL_BOOKS = "https://books.toscrape.com"

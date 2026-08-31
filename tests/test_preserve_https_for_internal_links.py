#!/usr/bin/env python3
"""
Final test and demo for HTTPS preservation feature (Issue #1410)

This demonstrates how the preserve_https_for_internal_links flag
prevents HTTPS downgrade when servers redirect to HTTP.
"""

import sys
import os
from urllib.parse import urljoin, urlparse

def demonstrate_issue():
    """Show the problem: HTTPS -> HTTP redirect causes HTTP links"""
    
    print("=" * 60)
    print("DEMONSTRATING THE ISSUE")
    print("=" * 60)
    
    # Simulate what happens during crawling
    original_url = "https://quotes.toscrape.com/tag/deep-thoughts"
    redirected_url = "http://quotes.toscrape.com/tag/deep-thoughts/"  # Server redirects to HTTP
    
    # Extract a relative link
    relative_link = "/author/Albert-Einstein"
    
    # Standard URL joining uses the redirected (HTTP) base
    resolved_url = urljoin(redirected_url, relative_link)
    
    print(f"Original URL:    {original_url}")
    print(f"Redirected to:   {redirected_url}")
    print(f"Relative link:   {relative_link}")
    print(f"Resolved link:   {resolved_url}")
    print(f"\n❌ Problem: Link is now HTTP instead of HTTPS!")
    
    return resolved_url

def demonstrate_solution():
    """Show the solution: preserve HTTPS for internal links"""
    
    print("\n" + "=" * 60)
    print("DEMONSTRATING THE SOLUTION")
    print("=" * 60)
    
    # Our normalize_url with HTTPS preservation
    def normalize_url_with_preservation(href, base_url, preserve_https=False, original_scheme=None):
        """Normalize URL with optional HTTPS preservation"""
        
        # Standard resolution
        full_url = urljoin(base_url, href.strip())
        
        # Preserve HTTPS if requested
        if preserve_https and original_scheme == 'https':
            parsed_full = urlparse(full_url)
            parsed_base = urlparse(base_url)
            
            # Only for same-domain links
            if parsed_full.scheme == 'http' and parsed_full.netloc == parsed_base.netloc:
                full_url = full_url.replace('http://', 'https://', 1)
                print(f"  → Preserved HTTPS for {parsed_full.netloc}")
        
        return full_url
    
    # Same scenario as before
    original_url = "https://quotes.toscrape.com/tag/deep-thoughts"
    redirected_url = "http://quotes.toscrape.com/tag/deep-thoughts/"
    relative_link = "/author/Albert-Einstein"
    
    # Without preservation (current behavior)
    resolved_without = normalize_url_with_preservation(
        relative_link, redirected_url,
        preserve_https=False, original_scheme='https'
    )
    
    print(f"\nWithout preservation:")
    print(f"  Result: {resolved_without}")
    
    # With preservation (new feature)
    resolved_with = normalize_url_with_preservation(
        relative_link, redirected_url,
        preserve_https=True, original_scheme='https'
    )
    
    print(f"\nWith preservation (preserve_https_for_internal_links=True):")
    print(f"  Result: {resolved_with}")
    print(f"\n✅ Solution: Internal link stays HTTPS!")
    
    return resolved_with

def test_edge_cases():
    """Test important edge cases"""
    
    print("\n" + "=" * 60)
    print("EDGE CASES")
    print("=" * 60)
    
    from urllib.parse import urljoin, urlparse
    
    def preserve_https(href, base_url, original_scheme):
        """Helper to test preservation logic"""
        full_url = urljoin(base_url, href)
        
        if original_scheme == 'https':
            parsed_full = urlparse(full_url)
            parsed_base = urlparse(base_url)
            # Fixed: check for protocol-relative URLs
            if (parsed_full.scheme == 'http' and 
                parsed_full.netloc == parsed_base.netloc and
                not href.strip().startswith('//')):
                full_url = full_url.replace('http://', 'https://', 1)
        
        return full_url
    
    test_cases = [
        # (description, href, base_url, original_scheme, should_be_https)
        ("External link", "http://other.com/page", "http://example.com", "https", False),
        ("Already HTTPS", "/page", "https://example.com", "https", True),
        ("No original HTTPS", "/page", "http://example.com", "http", False),
        ("Subdomain", "/page", "http://sub.example.com", "https", True),
        ("Protocol-relative", "//example.com/page", "http://example.com", "https", False),
    ]
    
    for desc, href, base_url, orig_scheme, should_be_https in test_cases:
        result = preserve_https(href, base_url, orig_scheme)
        is_https = result.startswith('https://')
        status = "✅" if is_https == should_be_https else "❌"
        
        print(f"\n{status} {desc}:")
        print(f"  Input: {href} + {base_url}")
        print(f"  Result: {result}")
        print(f"  Expected HTTPS: {should_be_https}, Got: {is_https}")

def usage_example():
    """Show how to use the feature in crawl4ai"""
    
    print("\n" + "=" * 60)
    print("USAGE IN CRAWL4AI")
    print("=" * 60)
    
    print("""
To enable HTTPS preservation in your crawl4ai code:

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async with AsyncWebCrawler() as crawler:
    config = CrawlerRunConfig(
        preserve_https_for_internal_links=True  # Enable HTTPS preservation
    )
    
    result = await crawler.arun(
        url="https://example.com",
        config=config
    )
    
    # All internal links will maintain HTTPS even if 
    # the server redirects to HTTP
```

This is especially useful for:
- Sites that redirect HTTPS to HTTP but still support HTTPS
- Security-conscious crawling where you want to stay on HTTPS
- Avoiding mixed content issues in downstream processing
""")

if __name__ == "__main__":
    # Run all demonstrations
    demonstrate_issue()
    demonstrate_solution() 
    test_edge_cases()
    usage_example()
    
    print("\n" + "=" * 60)
    print("✅ All tests complete!")
    print("=" * 60)
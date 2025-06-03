"""
Test cases for CallbackURLFilter
"""

import asyncio
from urllib.parse import urlparse, parse_qs
from crawl4ai.deep_crawling.filters import CallbackURLFilter


async def test_callback_filter():
    """Test CallbackURLFilter with various callback functions."""
    
    # Test Case 1: Simple path-based filter
    def path_filter(url: str) -> bool:
        """Only allow URLs containing '/docs/' in the path."""
        try:
            parsed = urlparse(url)
            return '/docs/' in parsed.path
        except:
            return False
    
    path_test_cases = {
        "https://example.com/docs/guide": True,
        "https://example.com/docs/api/reference": True,
        "https://example.com/blog/post": False,
        "https://example.com/about": False,
        "https://docs.example.com/": False,  # 'docs' in domain, not path
    }
    
    print("\nTest Case 1: Path-based Filter")
    print("-" * 50)
    
    path_callback_filter = CallbackURLFilter(callback=path_filter, name="PathFilter")
    all_passed = True
    
    for url, expected in path_test_cases.items():
        result = await path_callback_filter.apply(url)
        if result != expected:
            print(f"❌ Failed: URL '{url}'")
            print(f"   Expected: {expected}, Got: {result}")
            all_passed = False
        else:
            print(f"✅ Passed: URL '{url}'")
    
    # Test Case 2: Query parameter filter
    def query_filter(url: str) -> bool:
        """Filter based on query parameters."""
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            # Exclude URLs with 'print' or 'download' parameters
            if 'print' in params or 'download' in params:
                return False
            
            # Only include URLs with version=v2 or version=v3
            if 'version' in params:
                version = params['version'][0]
                return version in ['v2', 'v3']
            
            return True
        except:
            return False
    
    query_test_cases = {
        "https://api.example.com/users?version=v2": True,
        "https://api.example.com/users?version=v3": True,
        "https://api.example.com/users?version=v1": False,
        "https://example.com/doc?print=true": False,
        "https://example.com/file?download=pdf": False,
        "https://example.com/page": True,
    }
    
    print("\n\nTest Case 2: Query Parameter Filter")
    print("-" * 50)
    
    query_callback_filter = CallbackURLFilter(callback=query_filter, name="QueryFilter")
    
    for url, expected in query_test_cases.items():
        result = await query_callback_filter.apply(url)
        if result != expected:
            print(f"❌ Failed: URL '{url}'")
            print(f"   Expected: {expected}, Got: {result}")
            all_passed = False
        else:
            print(f"✅ Passed: URL '{url}'")
    
    # Test Case 3: Complex multi-condition filter
    def complex_filter(url: str) -> bool:
        """Complex filter with multiple conditions."""
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
            
            # Exclude archive/deprecated content
            if any(pattern in path for pattern in ['/archive/', '/deprecated/', '/old/']):
                return False
            
            # Exclude non-HTML file types
            if path.endswith(('.pdf', '.zip', '.exe', '.jpg', '.png')):
                return False
            
            # Exclude very long URLs
            if len(url) > 150:
                return False
            
            # Must be HTTPS
            if parsed.scheme != 'https':
                return False
            
            return True
        except:
            return False
    
    complex_test_cases = {
        "https://example.com/docs/guide": True,
        "https://example.com/archive/old-docs": False,
        "https://example.com/files/document.pdf": False,
        "http://example.com/page": False,  # Not HTTPS
        "https://example.com/" + "x" * 200: False,  # Too long
        "https://example.com/deprecated/api": False,
    }
    
    print("\n\nTest Case 3: Complex Multi-condition Filter")
    print("-" * 50)
    
    complex_callback_filter = CallbackURLFilter(callback=complex_filter, name="ComplexFilter")
    
    for url, expected in complex_test_cases.items():
        display_url = url if len(url) <= 80 else url[:77] + "..."
        result = await complex_callback_filter.apply(url)
        if result != expected:
            print(f"❌ Failed: URL '{display_url}'")
            print(f"   Expected: {expected}, Got: {result}")
            all_passed = False
        else:
            print(f"✅ Passed: URL '{display_url}'")
    
    # Test Case 4: Async callback filter
    async def async_filter(url: str) -> bool:
        """Async filter that simulates async operations."""
        # Simulate async operation
        await asyncio.sleep(0.001)
        
        try:
            parsed = urlparse(url)
            # Only allow specific domains asynchronously
            allowed_domains = ['example.com', 'test.com', 'docs.example.com']
            return parsed.netloc in allowed_domains
        except:
            return False
    
    async_test_cases = {
        "https://example.com/page": True,
        "https://test.com/api": True,
        "https://docs.example.com/guide": True,
        "https://malicious.com/hack": False,
        "https://other.com/page": False,
    }
    
    print("\n\nTest Case 4: Async Callback Filter")
    print("-" * 50)
    
    async_callback_filter = CallbackURLFilter(callback=async_filter, name="AsyncFilter")
    
    for url, expected in async_test_cases.items():
        result = await async_callback_filter.apply(url)
        if result != expected:
            print(f"❌ Failed: URL '{url}'")
            print(f"   Expected: {expected}, Got: {result}")
            all_passed = False
        else:
            print(f"✅ Passed: URL '{url}'")
    
    # Test Case 5: Path scope filter (similar to user's use case)
    def create_path_scope_filter(start_url: str):
        """Create a filter that only allows URLs under the starting path."""
        parsed_start = urlparse(start_url)
        start_domain = parsed_start.netloc
        start_path = parsed_start.path.rstrip('/')
        
        def filter_func(url: str) -> bool:
            try:
                parsed = urlparse(url)
                if parsed.netloc != start_domain:
                    return False
                
                url_path = parsed.path.rstrip('/')
                return url_path.startswith(start_path + '/') or url_path == start_path
            except:
                return False
        
        return filter_func
    
    print("\n\nTest Case 5: Path Scope Filter (User's Use Case)")
    print("-" * 50)
    
    start_url = "https://docs.github.com/en/github-models"
    path_scope_filter = create_path_scope_filter(start_url)
    scope_callback_filter = CallbackURLFilter(callback=path_scope_filter, name="PathScopeFilter")
    
    scope_test_cases = {
        "https://docs.github.com/en/github-models": True,
        "https://docs.github.com/en/github-models/overview": True,
        "https://docs.github.com/en/github-models/api/reference": True,
        "https://docs.github.com/en/actions": False,
        "https://docs.github.com/en": False,
        "https://github.com/docs": False,
    }
    
    for url, expected in scope_test_cases.items():
        result = await scope_callback_filter.apply(url)
        if result != expected:
            print(f"❌ Failed: URL '{url}'")
            print(f"   Expected: {expected}, Got: {result}")
            all_passed = False
        else:
            print(f"✅ Passed: URL '{url}'")
    
    # Display filter statistics
    print("\nFilter Statistics:")
    print("-"*50)
    print(f"Path Filter: Total={path_callback_filter.stats.total_urls}, Passed={path_callback_filter.stats.passed_urls}, Rejected={path_callback_filter.stats.rejected_urls}")
    print(f"Query Filter: Total={query_callback_filter.stats.total_urls}, Passed={query_callback_filter.stats.passed_urls}, Rejected={query_callback_filter.stats.rejected_urls}")
    print(f"Complex Filter: Total={complex_callback_filter.stats.total_urls}, Passed={complex_callback_filter.stats.passed_urls}, Rejected={complex_callback_filter.stats.rejected_urls}")
    print(f"Async Filter: Total={async_callback_filter.stats.total_urls}, Passed={async_callback_filter.stats.passed_urls}, Rejected={async_callback_filter.stats.rejected_urls}")
    print(f"Path Scope Filter: Total={scope_callback_filter.stats.total_urls}, Passed={scope_callback_filter.stats.passed_urls}, Rejected={scope_callback_filter.stats.rejected_urls}")
    
    if all_passed:
        print("\n✨ All callback filter tests passed!")
    else:
        print("\n❌ Some callback filter tests failed!")
    
    return all_passed


async def test_callback_filter_error_handling():
    """Test error handling in CallbackURLFilter."""
    
    print("\n\nTest Case: Error Handling")
    print("-" * 50)
    
    # Create a filter that raises exceptions
    def error_filter(url: str) -> bool:
        if "error" in url:
            raise ValueError("Simulated error")
        return True
    
    error_callback_filter = CallbackURLFilter(callback=error_filter, name="ErrorFilter")
    
    test_cases = {
        "https://example.com/page": True,  # Should pass
        "https://example.com/error": False,  # Should fail due to exception
        "https://example.com/another": True,  # Should pass
    }
    
    all_passed = True
    for url, expected in test_cases.items():
        result = await error_callback_filter.apply(url)
        if result != expected:
            print(f"❌ Failed: URL '{url}'")
            print(f"   Expected: {expected}, Got: {result}")
            all_passed = False
        else:
            print(f"✅ Passed: URL '{url}' (handled error correctly)")
    
    if all_passed:
        print("\n✨ Error handling test passed!")
    else:
        print("\n❌ Error handling test failed!")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(test_callback_filter())
    asyncio.run(test_callback_filter_error_handling()) 
from crawl4ai.deep_crawling.filters import ContentRelevanceFilter, URLPatternFilter, DomainFilter, ContentTypeFilter, SEOFilter
async def test_pattern_filter():
    # Test cases as list of tuples instead of dict for multiple patterns
    test_cases = [
        # Simple suffix patterns (*.html)
        ("*.html", {
            "https://example.com/page.html": True,
            "https://example.com/path/doc.html": True,
            "https://example.com/page.htm": False,
            "https://example.com/page.html?param=1": True,
        }),
        
        # Path prefix patterns (/foo/*)
        ("*/article/*", {
            "https://example.com/article/123": True,
            "https://example.com/blog/article/456": True,
            "https://example.com/articles/789": False,
            "https://example.com/article": False,
        }),
        
        # Complex patterns
        ("blog-*-[0-9]", {
            "https://example.com/blog-post-1": True,
            "https://example.com/blog-test-9": True,
            "https://example.com/blog-post": False,
            "https://example.com/blog-post-x": False,
        }),
        
        # Multiple patterns case
        (["*.pdf", "*/download/*"], {
            "https://example.com/doc.pdf": True,
            "https://example.com/download/file.txt": True,
            "https://example.com/path/download/doc": True,
            "https://example.com/uploads/file.txt": False,
        }),
        
        # Edge cases
        ("*", {
            "https://example.com": True,
            "": True,
            "http://test.com/path": True,
        }),
        
        # Complex regex
        (r"^https?://.*\.example\.com/\d+", {
            "https://sub.example.com/123": True,
            "http://test.example.com/456": True,
            "https://example.com/789": False,
            "https://sub.example.com/abc": False,
        })
    ]

    def run_accuracy_test():
        print("\nAccuracy Tests:")
        print("-" * 50)
        
        all_passed = True
        for patterns, test_urls in test_cases:
            filter_obj = URLPatternFilter(patterns)
            
            for url, expected in test_urls.items():
                result = filter_obj.apply(url)
                if result != expected:
                    print(f"❌ Failed: Pattern '{patterns}' with URL '{url}'")
                    print(f"   Expected: {expected}, Got: {result}")
                    all_passed = False
                else:
                    print(f"✅ Passed: Pattern '{patterns}' with URL '{url}'")
        
        return all_passed

    # Run tests
    print("Running Pattern Filter Tests...")
    accuracy_passed = run_accuracy_test()
    
    if accuracy_passed:
        print("\n✨ All accuracy tests passed!")
        
    else:
        print("\n❌ Some accuracy tests failed!")

async def test_domain_filter():
    from itertools import chain

    # Test cases
    test_cases = [
        # Allowed domains
        ({"allowed": "example.com"}, {
            "https://example.com/page": True,
            "http://example.com": True,
            "https://sub.example.com": False,
            "https://other.com": False,
        }),

        ({"allowed": ["example.com", "test.com"]}, {
            "https://example.com/page": True,
            "https://test.com/home": True,
            "https://other.com": False,
        }),

        # Blocked domains
        ({"blocked": "malicious.com"}, {
            "https://malicious.com": False,
            "https://safe.com": True,
            "http://malicious.com/login": False,
        }),

        ({"blocked": ["spam.com", "ads.com"]}, {
            "https://spam.com": False,
            "https://ads.com/banner": False,
            "https://example.com": True,
        }),

        # Allowed and Blocked combination
        ({"allowed": "example.com", "blocked": "sub.example.com"}, {
            "https://example.com": True,
            "https://sub.example.com": False,
            "https://other.com": False,
        }),
    ]

    def run_accuracy_test():
        print("\nAccuracy Tests:")
        print("-" * 50)
        
        all_passed = True
        for params, test_urls in test_cases:
            filter_obj = DomainFilter(
                allowed_domains=params.get("allowed"),
                blocked_domains=params.get("blocked"),
            )
            
            for url, expected in test_urls.items():
                result = filter_obj.apply(url)
                if result != expected:
                    print(f"\u274C Failed: Params {params} with URL '{url}'")
                    print(f"   Expected: {expected}, Got: {result}")
                    all_passed = False
                else:
                    print(f"\u2705 Passed: Params {params} with URL '{url}'")
        
        return all_passed

    # Run tests
    print("Running Domain Filter Tests...")
    accuracy_passed = run_accuracy_test()
    
    if accuracy_passed:
        print("\n\u2728 All accuracy tests passed!")
    else:
        print("\n\u274C Some accuracy tests failed!")

async def test_content_relevance_filter():
    relevance_filter = ContentRelevanceFilter(
        query="What was the cause of american civil war?", 
        threshold=1
    )

    test_cases = {
        "https://en.wikipedia.org/wiki/Cricket": False,
        "https://en.wikipedia.org/wiki/American_Civil_War": True,
    }

    print("\nRunning Content Relevance Filter Tests...")
    print("-" * 50)
    
    all_passed = True
    for url, expected in test_cases.items():
        result = await relevance_filter.apply(url)
        if result != expected:
            print(f"\u274C Failed: URL '{url}'")
            print(f"   Expected: {expected}, Got: {result}")
            all_passed = False
        else:
            print(f"\u2705 Passed: URL '{url}'")
    
    if all_passed:
        print("\n\u2728 All content relevance tests passed!")
    else:
        print("\n\u274C Some content relevance tests failed!")

async def test_content_type_filter():
    from itertools import chain

    # Test cases
    test_cases = [
        # Allowed single type
        ({"allowed": "image/png"}, {
            "https://example.com/image.png": True,
            "https://example.com/photo.jpg": False,
            "https://example.com/document.pdf": False,
        }),

        # Multiple allowed types
        ({"allowed": ["image/jpeg", "application/pdf"]}, {
            "https://example.com/photo.jpg": True,
            "https://example.com/document.pdf": True,
            "https://example.com/script.js": False,
        }),

        # No extension should be allowed
        ({"allowed": "application/json"}, {
            "https://example.com/api/data": True,
            "https://example.com/data.json": True,
            "https://example.com/page.html": False,
        }),

        # Unknown extensions should not be allowed
        ({"allowed": "application/octet-stream"}, {
            "https://example.com/file.unknown": True,
            "https://example.com/archive.zip": False,
            "https://example.com/software.exe": False,
        }),
    ]

    def run_accuracy_test():
        print("\nAccuracy Tests:")
        print("-" * 50)
        
        all_passed = True
        for params, test_urls in test_cases:
            filter_obj = ContentTypeFilter(
                allowed_types=params.get("allowed"),
            )
            
            for url, expected in test_urls.items():
                result = filter_obj.apply(url)
                if result != expected:
                    print(f"\u274C Failed: Params {params} with URL '{url}'")
                    print(f"   Expected: {expected}, Got: {result}")
                    all_passed = False
                else:
                    print(f"\u2705 Passed: Params {params} with URL '{url}'")
        
        return all_passed

    # Run tests
    print("Running Content Type Filter Tests...")
    accuracy_passed = run_accuracy_test()
    
    if accuracy_passed:
        print("\n\u2728 All accuracy tests passed!")
    else:
        print("\n\u274C Some accuracy tests failed!")

async def test_seo_filter():
    seo_filter = SEOFilter(threshold=0.5, keywords=["SEO", "search engines", "Optimization"])

    test_cases = {
        "https://en.wikipedia.org/wiki/Search_engine_optimization": True,
        "https://en.wikipedia.org/wiki/Randomness": False,
    }

    print("\nRunning SEO Filter Tests...")
    print("-" * 50)
    
    all_passed = True
    for url, expected in test_cases.items():
        result = await seo_filter.apply(url)
        if result != expected:
            print(f"\u274C Failed: URL '{url}'")
            print(f"   Expected: {expected}, Got: {result}")
            all_passed = False
        else:
            print(f"\u2705 Passed: URL '{url}'")
    
    if all_passed:
        print("\n\u2728 All SEO filter tests passed!")
    else:
        print("\n\u274C Some SEO filter tests failed!")

import asyncio

if __name__ == "__main__":
    asyncio.run(test_pattern_filter())
    asyncio.run(test_domain_filter())
    asyncio.run(test_content_type_filter())
    asyncio.run(test_content_relevance_filter())
    asyncio.run(test_seo_filter())
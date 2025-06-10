import sys
import os

# Get the grandparent directory
grandparent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(grandparent_dir)
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

import asyncio
from crawl4ai.deep_crawling.filters import URLPatternFilter


def test_prefix_boundary_matching():
    """Test that prefix patterns respect path boundaries"""
    print("=== Testing URLPatternFilter Prefix Boundary Fix ===")
    
    filter_obj = URLPatternFilter(patterns=['https://langchain-ai.github.io/langgraph/*'])
    
    test_cases = [
        ('https://langchain-ai.github.io/langgraph/', True),
        ('https://langchain-ai.github.io/langgraph/concepts/', True),
        ('https://langchain-ai.github.io/langgraph/tutorials/', True),
        ('https://langchain-ai.github.io/langgraph?param=1', True),
        ('https://langchain-ai.github.io/langgraph#section', True),
        ('https://langchain-ai.github.io/langgraphjs/', False),
        ('https://langchain-ai.github.io/langgraphjs/concepts/', False),
        ('https://other-site.com/langgraph/', False),
    ]
    
    all_passed = True
    for url, expected in test_cases:
        result = filter_obj.apply(url)
        status = "PASS" if result == expected else "FAIL"
        if result != expected:
            all_passed = False
        print(f"{status:4} | Expected: {expected:5} | Got: {result:5} | {url}")
    
    return all_passed


def test_edge_cases():
    """Test edge cases for path boundary matching"""
    print("\n=== Testing Edge Cases ===")
    
    test_patterns = [
        ('/api/*', [
            ('/api/', True),
            ('/api/v1', True),
            ('/api?param=1', True),
            ('/apiv2/', False),
            ('/api_old/', False),
        ]),
        
        ('*/docs/*', [
            ('example.com/docs/', True),
            ('example.com/docs/guide', True),
            ('example.com/documentation/', False),
            ('example.com/docs_old/', False),
        ]),
    ]
    
    all_passed = True
    for pattern, test_cases in test_patterns:
        print(f"\nPattern: {pattern}")
        filter_obj = URLPatternFilter(patterns=[pattern])
        
        for url, expected in test_cases:
            result = filter_obj.apply(url)
            status = "PASS" if result == expected else "FAIL"
            if result != expected:
                all_passed = False
            print(f"  {status:4} | Expected: {expected:5} | Got: {result:5} | {url}")
    
    return all_passed

if __name__ == "__main__":
    test1_passed = test_prefix_boundary_matching()
    test2_passed = test_edge_cases()
    
    if test1_passed and test2_passed:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

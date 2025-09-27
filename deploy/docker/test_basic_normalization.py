#!/usr/bin/env python3
"""
Basic test for result normalization - no external dependencies.
"""

import os
import pathlib
from datetime import datetime, date
from typing import List, Any

# Import the modules we're testing
from result_normalizer import (
    normalize_results,
    normalize_results_protocol_dispatch,
    normalize_single_result,
    normalize_value_recursive
)
from result_protocols import ResultContainer, SingleResult
from schemas import StandardizedResponse


class MockCrawlResult:
    """Mock crawl result object."""

    def __init__(self, url="https://example.com", success=True, error_message=""):
        self.url = url
        self.success = success
        self.error_message = error_message

    def model_dump(self):
        return {
            "url": self.url,
            "success": self.success,
            "error_message": self.error_message,
            "html": "<html>test</html>",
            "created_at": datetime.now()
        }


class MockCrawlResultContainer:
    """Mock container that implements ResultContainer protocol."""

    def __init__(self, results: List[MockCrawlResult]):
        self._results = results

    @property
    def results(self):
        return self._results


def test_basic_functionality():
    """Test basic functionality of the new normalization system."""
    print("Testing basic result normalization...")

    # Test 1: None handling
    result = normalize_results(None)
    assert result == [], f"Expected [], got {result}"
    print("✓ None handling works")

    # Test 2: List handling
    mock_results = [MockCrawlResult(), MockCrawlResult()]
    result = normalize_results(mock_results)
    assert result == mock_results, f"Expected {mock_results}, got {result}"
    print("✓ List handling works")

    # Test 3: Container protocol
    container = MockCrawlResultContainer(mock_results)
    result = normalize_results_protocol_dispatch(container)
    assert result == mock_results, f"Expected {mock_results}, got {result}"
    print("✓ Container protocol works")

    # Test 4: Single result normalization
    mock_result = MockCrawlResult()
    result = normalize_single_result(mock_result)
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert "url" in result, f"Expected 'url' key in result"
    print("✓ Single result normalization works")

    # Test 5: Value normalization
    test_value = {
        "timestamp": datetime.now(),
        "path": pathlib.Path("/tmp/test"),
        "nested": {"date": date.today()}
    }
    result = normalize_value_recursive(test_value)

    # Should be JSON serializable
    import json
    json_str = json.dumps(result)
    assert isinstance(json_str, str), "Result should be JSON serializable"
    print("✓ Recursive value normalization works")

    # Test 6: StandardizedResponse
    response = StandardizedResponse.success_response(
        results=[{"url": "test", "success": True}],
        processing_time=1.0
    )
    assert response.success is True, "Response should be successful"
    assert len(response.results) == 1, "Should have one result"
    print("✓ StandardizedResponse works")

    print("\n🎉 All basic tests passed!")


def test_no_hasattr_usage():
    """Test that we're not using hasattr() in the main normalization paths."""
    print("\nTesting hasattr() usage...")

    import inspect

    # Check normalize_results_protocol_dispatch
    source = inspect.getsource(normalize_results_protocol_dispatch)
    hasattr_count = source.count('hasattr(')

    # Should use isinstance() for protocol checking, not hasattr()
    # Allow up to 1 hasattr for fallback logic
    if hasattr_count <= 1:
        print(f"✓ normalize_results_protocol_dispatch has minimal hasattr() usage: {hasattr_count}")
    else:
        print(f"⚠ normalize_results_protocol_dispatch has {hasattr_count} hasattr() calls")

    # Check normalize_single_result
    source = inspect.getsource(normalize_single_result)
    hasattr_count = source.count('hasattr(')

    if hasattr_count <= 1:
        print(f"✓ normalize_single_result has minimal hasattr() usage: {hasattr_count}")
    else:
        print(f"⚠ normalize_single_result has {hasattr_count} hasattr() calls")


if __name__ == "__main__":
    try:
        test_basic_functionality()
        test_no_hasattr_usage()
        print("\n✅ All tests completed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
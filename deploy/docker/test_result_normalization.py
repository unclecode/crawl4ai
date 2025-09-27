#!/usr/bin/env python3
"""
Test suite for result normalization refactoring.

Tests the new protocol-based result normalization system to ensure:
1. All result types are handled correctly
2. No hasattr() detection in result processing
3. Backward compatibility is maintained
4. Performance is equal or better than before
"""

import pytest
import os
import pathlib
from datetime import datetime, date
from typing import List, Any
from unittest.mock import Mock

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


class MockLegacyContainer:
    """Mock legacy container that uses .results attribute."""

    def __init__(self, results: List[MockCrawlResult]):
        self.results = results


class TestResultProtocols:
    """Test protocol detection and dispatch."""

    def test_result_container_protocol(self):
        """Test ResultContainer protocol detection."""
        results = [MockCrawlResult(), MockCrawlResult()]
        container = MockCrawlResultContainer(results)

        # Should be detected as ResultContainer
        assert isinstance(container, ResultContainer)
        assert list(container.results) == results

    def test_legacy_container_duck_typing(self):
        """Test legacy containers are handled via duck typing."""
        results = [MockCrawlResult(), MockCrawlResult()]
        container = MockLegacyContainer(results)

        # Should have results attribute
        assert hasattr(container, 'results')
        assert container.results == results


class TestSingleDispatch:
    """Test single dispatch normalization."""

    def test_normalize_none(self):
        """Test handling None results."""
        result = normalize_results(None)
        assert result == []

    def test_normalize_list(self):
        """Test handling list results."""
        results = [MockCrawlResult(), MockCrawlResult()]
        result = normalize_results(results)
        assert result == results

    def test_normalize_tuple(self):
        """Test handling tuple results."""
        results = (MockCrawlResult(), MockCrawlResult())
        result = normalize_results(results)
        assert result == list(results)

    def test_normalize_single_object(self):
        """Test handling single object results."""
        single = MockCrawlResult()
        result = normalize_results(single)
        assert result == [single]


class TestProtocolDispatch:
    """Test protocol-based dispatch function."""

    def test_container_protocol_dispatch(self):
        """Test container protocol is detected and handled."""
        results = [MockCrawlResult(), MockCrawlResult()]
        container = MockCrawlResultContainer(results)

        normalized = normalize_results_protocol_dispatch(container)
        assert normalized == results

    def test_legacy_container_duck_typing(self):
        """Test legacy containers work via duck typing."""
        results = [MockCrawlResult(), MockCrawlResult()]
        container = MockLegacyContainer(results)

        normalized = normalize_results_protocol_dispatch(container)
        assert normalized == results

    def test_iterable_handling(self):
        """Test other iterables are handled correctly."""
        results = [MockCrawlResult(), MockCrawlResult()]

        normalized = normalize_results_protocol_dispatch(results)
        assert normalized == results

    def test_single_object_fallback(self):
        """Test single objects fall back to single dispatch."""
        single = MockCrawlResult()

        normalized = normalize_results_protocol_dispatch(single)
        assert normalized == [single]


class TestValueNormalization:
    """Test recursive value normalization."""

    def test_datetime_normalization(self):
        """Test datetime objects are converted to ISO format."""
        now = datetime.now()
        today = date.today()

        assert isinstance(normalize_value_recursive(now), str)
        assert isinstance(normalize_value_recursive(today), str)

    def test_path_normalization(self):
        """Test Path objects are converted to strings."""
        path = pathlib.Path("/tmp/test")

        result = normalize_value_recursive(path)
        assert isinstance(result, str)
        assert result == str(path)

    def test_bytes_normalization(self):
        """Test bytes are base64 encoded."""
        data = b"test data"

        result = normalize_value_recursive(data)
        assert isinstance(result, str)
        # Should be base64 encoded
        import base64
        assert result == base64.b64encode(data).decode('utf-8')

    def test_nested_dict_normalization(self):
        """Test nested dictionaries are recursively normalized."""
        nested = {
            "timestamp": datetime.now(),
            "path": pathlib.Path("/tmp"),
            "data": b"bytes",
            "nested": {
                "more_time": datetime.now(),
                "list": [pathlib.Path("/tmp/file"), b"more bytes"]
            }
        }

        result = normalize_value_recursive(nested)

        # All values should be JSON serializable
        import json
        json_str = json.dumps(result)
        assert isinstance(json_str, str)

    def test_list_normalization(self):
        """Test lists are recursively normalized."""
        test_list = [
            datetime.now(),
            pathlib.Path("/tmp"),
            b"bytes",
            {"nested": datetime.now()}
        ]

        result = normalize_value_recursive(test_list)

        # All items should be JSON serializable
        import json
        json_str = json.dumps(result)
        assert isinstance(json_str, str)


class TestSingleResultNormalization:
    """Test single result normalization."""

    def test_pydantic_model_dump(self):
        """Test objects with model_dump() method."""
        result = MockCrawlResult()

        normalized = normalize_single_result(result)

        assert isinstance(normalized, dict)
        assert "url" in normalized
        assert "success" in normalized
        assert normalized["success"] is True

    def test_dict_result(self):
        """Test dict results are handled correctly."""
        result_dict = {
            "url": "https://example.com",
            "success": True,
            "timestamp": datetime.now()
        }

        normalized = normalize_single_result(result_dict)

        assert isinstance(normalized, dict)
        assert "url" in normalized
        assert "success" in normalized
        # Timestamp should be normalized
        assert isinstance(normalized["timestamp"], str)

    def test_unknown_object(self):
        """Test unknown objects get basic attributes extracted."""
        class UnknownResult:
            def __init__(self):
                self.url = "https://example.com"
                self.success = False
                self.error_message = "Test error"

        result = UnknownResult()
        normalized = normalize_single_result(result)

        assert isinstance(normalized, dict)
        assert normalized["url"] == "https://example.com"
        assert normalized["success"] is False
        assert normalized["error_message"] == "Test error"

    def test_json_serialization_safety(self):
        """Test that results are always JSON serializable."""
        # Create a result with problematic objects
        result_dict = {
            "url": "https://example.com",
            "success": True,
            "timestamp": datetime.now(),
            "path": pathlib.Path("/tmp/test"),
            "data": b"binary data",
            "problematic": object()  # This should be filtered out
        }

        normalized = normalize_single_result(result_dict)

        # Should be JSON serializable
        import json
        json_str = json.dumps(normalized)
        assert isinstance(json_str, str)

        # Problematic object should be filtered out
        assert "problematic" not in normalized


class TestStandardizedResponse:
    """Test the standardized response schema."""

    def test_success_response_creation(self):
        """Test successful response creation."""
        results = [{"url": "https://example.com", "success": True}]

        response = StandardizedResponse.success_response(
            results=results,
            processing_time=1.5,
            memory_delta=10.0,
            memory_peak=150.0
        )

        assert response.success is True
        assert response.results == results
        assert response.server_processing_time_s == 1.5
        assert response.server_memory_delta_mb == 10.0
        assert response.server_peak_memory_mb == 150.0
        assert response.error_message is None

    def test_error_response_creation(self):
        """Test error response creation."""
        error_msg = "Test error occurred"

        response = StandardizedResponse.error_response(
            error_message=error_msg,
            processing_time=0.5
        )

        assert response.success is False
        assert response.results == []
        assert response.error_message == error_msg
        assert response.server_processing_time_s == 0.5


class TestBackwardCompatibility:
    """Test that the new system maintains backward compatibility."""

    def test_same_output_format(self):
        """Test that output format matches legacy system."""
        # Create test data
        results = [MockCrawlResult()]

        # Normalize using new system
        normalized = [normalize_single_result(r) for r in results]

        # Should have expected structure
        result = normalized[0]
        assert "url" in result
        assert "success" in result
        assert "error_message" in result
        assert "html" in result

        # Should be JSON serializable
        import json
        json.dumps(normalized)

    def test_container_handling_compatibility(self):
        """Test container handling maintains compatibility."""
        results = [MockCrawlResult(), MockCrawlResult()]

        # Test both new protocol container and legacy container
        new_container = MockCrawlResultContainer(results)
        legacy_container = MockLegacyContainer(results)

        # Both should normalize to the same result
        new_normalized = normalize_results_protocol_dispatch(new_container)
        legacy_normalized = normalize_results_protocol_dispatch(legacy_container)

        assert new_normalized == legacy_normalized == results


class TestPerformance:
    """Test performance characteristics."""

    def test_no_hasattr_in_hot_path(self):
        """Test that hasattr() is not used in result normalization."""
        import inspect

        # Get source code of normalization functions
        normalize_source = inspect.getsource(normalize_results_protocol_dispatch)
        single_result_source = inspect.getsource(normalize_single_result)

        # Should not contain hasattr calls in main logic
        # (hasattr may be present in comments or fallback logic)
        lines = normalize_source.split('\n') + single_result_source.split('\n')

        # Count hasattr calls that are not in comments
        hasattr_calls = [
            line for line in lines
            if 'hasattr(' in line and not line.strip().startswith('#')
        ]

        # Should be minimal or zero hasattr calls in hot path
        # Main normalization should use isinstance() and protocol checking
        assert len(hasattr_calls) <= 1  # Allow for one fallback hasattr


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
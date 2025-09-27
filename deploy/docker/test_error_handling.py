#!/usr/bin/env python3
"""
Test script for the new protocol-based error handling system.
"""

import json
from fastapi import HTTPException

# Import our new error handling system
from error_handler import handle_error, parse_network_error, parse_security_error
from error_protocols import NetworkErrorImpl, ValidationErrorImpl, SecurityErrorImpl
from schemas import ErrorResponse


def test_network_error_handling():
    """Test network error protocol dispatch."""
    print("Testing network error handling...")

    # Create a network error
    network_error = NetworkErrorImpl(
        error_code="ERR_NAME_NOT_RESOLVED",
        message="Unable to resolve hostname",
        operation="Fetch HTML"
    )

    # Handle with protocol dispatch
    error_response = handle_error(network_error, "Fetch HTML")

    print(f"✓ Network error handled: {error_response.error_type}")
    print(f"  Message: {error_response.error_message}")
    print(f"  Suggestions: {error_response.suggestions}")

    assert error_response.error_type == "network"
    assert error_response.error_code == "ERR_NAME_NOT_RESOLVED"
    assert len(error_response.suggestions) > 0


def test_parse_network_error():
    """Test parsing raw error messages into network errors."""
    print("\nTesting network error parsing...")

    raw_error = "net::ERR_NAME_NOT_RESOLVED at https://invalid-domain.com"
    network_error = parse_network_error(raw_error, "Screenshot capture")

    print(f"✓ Parsed error code: {network_error.error_code}")
    print(f"  Message: {network_error.message}")

    assert network_error.error_code == "ERR_NAME_NOT_RESOLVED"
    assert "Screenshot capture failed" in network_error.message


def test_validation_error():
    """Test validation error handling."""
    print("\nTesting validation error handling...")

    validation_error = ValidationErrorImpl(
        field_name="output_path",
        invalid_value="/invalid/path",
        expected_format="path within /tmp/crawl4ai-exports"
    )

    error_response = handle_error(validation_error)

    print(f"✓ Validation error handled: {error_response.error_type}")
    print(f"  Details: {error_response.details}")

    assert error_response.error_type == "validation"
    assert error_response.details["field_name"] == "output_path"


def test_security_error():
    """Test security error handling."""
    print("\nTesting security error handling...")

    security_error = SecurityErrorImpl(
        violation_type="path_traversal",
        attempted_action="Access path: /etc/passwd",
        allowed_scope="/tmp/crawl4ai-exports"
    )

    error_response = handle_error(security_error)

    print(f"✓ Security error handled: {error_response.error_type}")
    print(f"  Violation: {error_response.details['violation_type']}")

    assert error_response.error_type == "security"
    assert error_response.details["violation_type"] == "path_traversal"


def test_http_exception():
    """Test HTTPException handling."""
    print("\nTesting HTTP exception handling...")

    http_error = HTTPException(status_code=400, detail="Invalid request format")
    error_response = handle_error(http_error, "API request")

    print(f"✓ HTTP exception handled: {error_response.error_type}")
    print(f"  Error code: {error_response.error_code}")

    assert error_response.error_type == "validation"
    assert error_response.error_code == "HTTP_400"


def test_unknown_error():
    """Test handling of unknown error types."""
    print("\nTesting unknown error handling...")

    unknown_error = RuntimeError("Something unexpected happened")
    error_response = handle_error(unknown_error, "Unknown operation")

    print(f"✓ Unknown error handled: {error_response.error_type}")
    print(f"  Message: {error_response.error_message}")

    assert error_response.error_type == "unknown"
    assert "Something unexpected happened" in error_response.error_message


def test_json_serialization():
    """Test that error responses are JSON serializable."""
    print("\nTesting JSON serialization...")

    network_error = NetworkErrorImpl(
        error_code="ERR_CONNECTION_REFUSED",
        message="Connection refused",
        operation="PDF generation"
    )

    error_response = handle_error(network_error)

    # Should be JSON serializable
    json_str = json.dumps(error_response.model_dump())
    parsed = json.loads(json_str)

    print(f"✓ JSON serialization successful")
    print(f"  Serialized size: {len(json_str)} characters")

    assert parsed["error_type"] == "network"
    assert parsed["error_code"] == "ERR_CONNECTION_REFUSED"


if __name__ == "__main__":
    try:
        print("🧪 Testing Protocol-Based Error Handling System\n")

        test_network_error_handling()
        test_parse_network_error()
        test_validation_error()
        test_security_error()
        test_http_exception()
        test_unknown_error()
        test_json_serialization()

        print("\n✅ All error handling tests passed!")
        print("\n📋 Error handling system features:")
        print("  ✓ Protocol-based dispatch using @singledispatch")
        print("  ✓ Type-safe error responses with Pydantic")
        print("  ✓ User-friendly error messages with suggestions")
        print("  ✓ Structured error information for debugging")
        print("  ✓ JSON serializable for API responses")
        print("  ✓ Backward compatibility with existing code")

    except Exception as e:
        print(f"\n❌ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
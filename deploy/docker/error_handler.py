# deploy/docker/error_handler.py

from __future__ import annotations

import re
from functools import singledispatch
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException

from error_protocols import (
    NetworkError, ValidationError, SecurityError,
    ConfigurationError, ProcessingError,
    NetworkErrorImpl, ValidationErrorImpl, SecurityErrorImpl,
    ConfigurationErrorImpl, ProcessingErrorImpl
)
from schemas import ErrorResponse


@singledispatch
def handle_error(error: Exception, operation: str = "operation") -> ErrorResponse:
    """
    Default handler for unknown error types.

    Uses protocol checking before falling back to generic handling.

    Args:
        error: Exception to handle
        operation: Operation that failed

    Returns:
        ErrorResponse with appropriate error information
    """
    # Check protocols explicitly since singledispatch doesn't handle protocols
    if isinstance(error, NetworkError):
        return ErrorResponse.network_error(
            error_code=error.error_code,
            message=error.message,
            operation=operation,
            suggestions=_get_network_error_suggestions(error.error_code)
        )
    elif isinstance(error, ValidationError):
        return ErrorResponse.validation_error(
            field_name=error.field_name,
            invalid_value=error.invalid_value,
            expected_format=error.expected_format,
            suggestions=[
                f"Provide a valid {error.expected_format} for {error.field_name}",
                "Check the API documentation for valid input formats"
            ]
        )
    elif isinstance(error, SecurityError):
        return ErrorResponse.security_error(
            violation_type=error.violation_type,
            attempted_action=error.attempted_action,
            allowed_scope=error.allowed_scope,
            suggestions=[
                f"Ensure your action is within the allowed scope: {error.allowed_scope}",
                "Check the security restrictions in the API documentation"
            ]
        )
    elif isinstance(error, ConfigurationError):
        return ErrorResponse.configuration_error(
            config_key=error.config_key,
            config_value=error.config_value,
            suggestion=error.suggestion
        )
    elif isinstance(error, ProcessingError):
        return ErrorResponse.processing_error(
            processing_stage=error.processing_stage,
            data_type=error.data_type,
            recovery_suggestion=error.recovery_suggestion,
            operation=operation
        )

    # Fallback to generic error handling
    return ErrorResponse(
        error_type="unknown",
        error_message=f"{operation} failed: {str(error)}",
        operation=operation,
        suggestions=["Please check your input and try again"]
    )




@handle_error.register
def _(error: HTTPException, operation: str = "operation") -> ErrorResponse:
    """Handle FastAPI HTTP exceptions."""
    if error.status_code == 400:
        return ErrorResponse(
            error_type="validation",
            error_message=str(error.detail),
            error_code="HTTP_400",
            operation=operation,
            suggestions=["Check your request parameters and format"]
        )
    elif error.status_code == 404:
        return ErrorResponse(
            error_type="not_found",
            error_message=str(error.detail),
            error_code="HTTP_404",
            operation=operation,
            suggestions=["Check that the requested resource exists"]
        )
    elif error.status_code == 413:
        return ErrorResponse(
            error_type="size_limit",
            error_message=str(error.detail),
            error_code="HTTP_413",
            operation=operation,
            suggestions=[
                "Use output_path parameter to save large results to file",
                "Reduce the size of your request"
            ]
        )
    elif error.status_code == 500:
        return ErrorResponse(
            error_type="server_error",
            error_message=str(error.detail),
            error_code="HTTP_500",
            operation=operation,
            suggestions=["Try again later", "Contact support if the issue persists"]
        )
    else:
        return ErrorResponse(
            error_type="http_error",
            error_message=str(error.detail),
            error_code=f"HTTP_{error.status_code}",
            operation=operation
        )


@handle_error.register
def _(error: ValueError, operation: str = "operation") -> ErrorResponse:
    """Handle value errors, often from invalid configurations or inputs."""
    error_msg = str(error)

    # Detect if it's a configuration error
    if any(keyword in error_msg.lower() for keyword in ["config", "browser", "crawler"]):
        return ErrorResponse.configuration_error(
            config_key="unknown",
            config_value=error_msg,
            suggestion="Check your configuration syntax and allowed values"
        )

    # Otherwise treat as validation error
    return ErrorResponse.validation_error(
        field_name="input",
        invalid_value=error_msg,
        expected_format="valid input format",
        suggestions=["Check your input values and formats"]
    )


@handle_error.register
def _(error: TypeError, operation: str = "operation") -> ErrorResponse:
    """Handle type errors, often from incorrect parameter types."""
    return ErrorResponse.validation_error(
        field_name="parameter_type",
        invalid_value=str(error),
        expected_format="correct parameter type",
        suggestions=[
            "Check that all parameters are the correct type",
            "Refer to the API documentation for parameter types"
        ]
    )


def parse_network_error(error_msg: str, operation: str = "operation") -> NetworkErrorImpl:
    """
    Parse a raw error message and create a NetworkError.

    This replaces the old _extract_user_friendly_error function.
    """
    error_code = "UNKNOWN"
    friendly_message = error_msg

    if "ERR_NAME_NOT_RESOLVED" in error_msg:
        error_code = "ERR_NAME_NOT_RESOLVED"
        friendly_message = f"{operation} failed: Unable to resolve hostname. Please check the URL is valid and accessible."
    elif "ERR_CONNECTION_REFUSED" in error_msg:
        error_code = "ERR_CONNECTION_REFUSED"
        friendly_message = f"{operation} failed: Connection refused. The server may be down or unreachable."
    elif "ERR_CONNECTION_TIMED_OUT" in error_msg or "Timeout" in error_msg:
        error_code = "ERR_CONNECTION_TIMED_OUT"
        friendly_message = f"{operation} failed: Connection timed out. The server took too long to respond."
    elif "ERR_CONNECTION_CLOSED" in error_msg:
        error_code = "ERR_CONNECTION_CLOSED"
        friendly_message = f"{operation} failed: Connection closed unexpectedly. The server may have terminated the connection."
    elif "ERR_SSL_PROTOCOL_ERROR" in error_msg or "SSL" in error_msg:
        error_code = "ERR_SSL_PROTOCOL_ERROR"
        friendly_message = f"{operation} failed: SSL/TLS error. The server's certificate may be invalid or expired."
    elif "ERR_CERT" in error_msg:
        error_code = "ERR_CERT"
        friendly_message = f"{operation} failed: Certificate error. The server's SSL certificate is invalid."
    elif "ERR_TOO_MANY_REDIRECTS" in error_msg:
        error_code = "ERR_TOO_MANY_REDIRECTS"
        friendly_message = f"{operation} failed: Too many redirects. The URL may be misconfigured."
    elif "net::" in error_msg:
        match = re.search(r'net::(ERR_[A-Z_]+)', error_msg)
        if match:
            error_code = match.group(1)
            friendly_message = f"{operation} failed: Network error ({error_code}). Please check the URL and network connectivity."

    return NetworkErrorImpl(error_code, friendly_message, operation)


def parse_security_error(error_msg: str, attempted_path: str = "", allowed_dir: str = "") -> SecurityErrorImpl:
    """Parse security-related errors, particularly path validation errors."""
    if "must be within" in error_msg and "outside the allowed directory" in error_msg:
        return SecurityErrorImpl(
            violation_type="path_traversal",
            attempted_action=f"Access path: {attempted_path}",
            allowed_scope=allowed_dir,
            message=error_msg
        )

    return SecurityErrorImpl(
        violation_type="access_denied",
        attempted_action="unknown action",
        allowed_scope="allowed operations only",
        message=error_msg
    )


def _get_network_error_suggestions(error_code: str) -> List[str]:
    """Get specific suggestions based on network error code."""
    suggestions_map = {
        "ERR_NAME_NOT_RESOLVED": [
            "Check that the URL is spelled correctly",
            "Verify the domain exists and is accessible",
            "Check your internet connection"
        ],
        "ERR_CONNECTION_REFUSED": [
            "Verify the server is running and accessible",
            "Check if the port number is correct",
            "Ensure the service is not blocked by firewall"
        ],
        "ERR_CONNECTION_TIMED_OUT": [
            "Try again later as the server may be temporarily overloaded",
            "Check your internet connection stability",
            "Verify the server is responding"
        ],
        "ERR_SSL_PROTOCOL_ERROR": [
            "Check if the website has a valid SSL certificate",
            "Try using http:// instead of https:// if appropriate",
            "Contact the website administrator about certificate issues"
        ],
        "ERR_CERT": [
            "The website's SSL certificate may be expired or invalid",
            "Try accessing the site in a web browser to see certificate details",
            "Contact the website administrator"
        ],
        "ERR_TOO_MANY_REDIRECTS": [
            "Check if the URL is correct and not causing a redirect loop",
            "Try accessing the final destination URL directly",
            "Contact the website administrator about the redirect configuration"
        ]
    }

    return suggestions_map.get(error_code, [
        "Check the URL and network connectivity",
        "Try again later",
        "Contact support if the issue persists"
    ])


def create_http_exception_from_error(error_response: ErrorResponse, status_code: int = 500) -> HTTPException:
    """Convert an ErrorResponse to an HTTPException for FastAPI."""
    return HTTPException(
        status_code=status_code,
        detail=error_response.model_dump()
    )
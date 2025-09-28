# deploy/docker/error_context.py

from __future__ import annotations

import logging
import re
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from app.schemas import ErrorResponse


_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

logger = logging.getLogger(__name__)


def get_correlation_id() -> str:
    """Get current correlation ID from context."""
    cid = _correlation_id.get()
    if not cid:
        cid = str(uuid.uuid4())
        _correlation_id.set(cid)
    return cid


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in context."""
    _correlation_id.set(correlation_id)


@dataclass
class ErrorContext:
    """
    Unified error context for structured error handling.

    Replaces multiple protocol implementations with a single, flexible context.
    """

    error_type: str
    message: str
    operation: str = "operation"
    correlation_id: str = field(default_factory=get_correlation_id)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    error_code: Optional[str] = None
    field_name: Optional[str] = None
    invalid_value: Optional[Any] = None
    expected_format: Optional[str] = None
    violation_type: Optional[str] = None
    attempted_action: Optional[str] = None
    allowed_scope: Optional[str] = None
    config_key: Optional[str] = None
    config_value: Optional[Any] = None
    processing_stage: Optional[str] = None
    data_type: Optional[str] = None

    suggestions: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def network_error(
        cls,
        error_code: str,
        message: str,
        operation: str = "operation",
        suggestions: Optional[List[str]] = None,
    ) -> ErrorContext:
        """Create network error context."""
        return cls(
            error_type="network",
            error_code=error_code,
            message=message,
            operation=operation,
            suggestions=suggestions or _get_network_error_suggestions(error_code),
        )

    @classmethod
    def validation_error(
        cls,
        field_name: str,
        invalid_value: Any,
        expected_format: str,
        suggestions: Optional[List[str]] = None,
    ) -> ErrorContext:
        """Create validation error context."""
        return cls(
            error_type="validation",
            field_name=field_name,
            invalid_value=invalid_value,
            expected_format=expected_format,
            message=f"Invalid value for {field_name}",
            suggestions=suggestions or [
                f"Provide a valid {expected_format} for {field_name}",
                "Check the API documentation for valid input formats"
            ],
        )

    @classmethod
    def security_error(
        cls,
        violation_type: str,
        attempted_action: str,
        allowed_scope: str,
        message: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
    ) -> ErrorContext:
        """Create security error context."""
        return cls(
            error_type="security",
            violation_type=violation_type,
            attempted_action=attempted_action,
            allowed_scope=allowed_scope,
            message=message or f"Security violation: {violation_type}",
            suggestions=suggestions or [
                f"Ensure your action is within the allowed scope: {allowed_scope}",
                "Check the security restrictions in the API documentation"
            ],
        )

    @classmethod
    def configuration_error(
        cls,
        config_key: str,
        config_value: Any,
        suggestion: str,
        message: Optional[str] = None,
    ) -> ErrorContext:
        """Create configuration error context."""
        return cls(
            error_type="configuration",
            config_key=config_key,
            config_value=config_value,
            message=message or f"Invalid configuration for {config_key}",
            suggestions=[suggestion],
        )

    @classmethod
    def processing_error(
        cls,
        processing_stage: str,
        data_type: str,
        recovery_suggestion: str,
        operation: str = "operation",
        message: Optional[str] = None,
    ) -> ErrorContext:
        """Create processing error context."""
        return cls(
            error_type="processing",
            processing_stage=processing_stage,
            data_type=data_type,
            message=message or f"Processing failed at {processing_stage}",
            operation=operation,
            suggestions=[recovery_suggestion],
        )

    @classmethod
    def from_exception(cls, error: Exception, operation: str = "operation") -> ErrorContext:
        """
        Create error context from any exception.

        This method replaces the old handle_error singledispatch approach.
        """
        correlation_id = get_correlation_id()

        if isinstance(error, HTTPException):
            return cls._from_http_exception(error, operation, correlation_id)

        if isinstance(error, ValueError):
            return cls._from_value_error(error, operation, correlation_id)

        if isinstance(error, TypeError):
            return cls._from_type_error(error, operation, correlation_id)

        return cls(
            error_type="unknown",
            message=f"{operation} failed: {str(error)}",
            operation=operation,
            correlation_id=correlation_id,
            suggestions=["Please check your input and try again"],
        )

    @classmethod
    def _from_http_exception(cls, error: HTTPException, operation: str, correlation_id: str) -> ErrorContext:
        """Handle FastAPI HTTP exceptions."""
        status_map = {
            400: ("validation", "Check your request parameters and format"),
            404: ("not_found", "Check that the requested resource exists"),
            413: ("size_limit", "Use output_path parameter to save large results to file"),
            500: ("server_error", "Try again later"),
        }

        error_type, suggestion = status_map.get(error.status_code, ("http_error", "Check your request"))

        suggestions = [suggestion]
        if error.status_code == 413:
            suggestions.append("Reduce the size of your request")
        elif error.status_code == 500:
            suggestions.append("Contact support if the issue persists")

        return cls(
            error_type=error_type,
            error_code=f"HTTP_{error.status_code}",
            message=str(error.detail),
            operation=operation,
            correlation_id=correlation_id,
            suggestions=suggestions,
        )

    @classmethod
    def _from_value_error(cls, error: ValueError, operation: str, correlation_id: str) -> ErrorContext:
        """Handle value errors."""
        error_msg = str(error)

        if any(keyword in error_msg.lower() for keyword in ["config", "browser", "crawler"]):
            return cls(
                error_type="configuration",
                config_key="unknown",
                config_value=error_msg,
                message=error_msg,
                operation=operation,
                correlation_id=correlation_id,
                suggestions=["Check your configuration syntax and allowed values"],
            )

        return cls(
            error_type="validation",
            field_name="input",
            invalid_value=error_msg,
            expected_format="valid input format",
            message=error_msg,
            operation=operation,
            correlation_id=correlation_id,
            suggestions=["Check your input values and formats"],
        )

    @classmethod
    def _from_type_error(cls, error: TypeError, operation: str, correlation_id: str) -> ErrorContext:
        """Handle type errors."""
        return cls(
            error_type="validation",
            field_name="parameter_type",
            invalid_value=str(error),
            expected_format="correct parameter type",
            message=str(error),
            operation=operation,
            correlation_id=correlation_id,
            suggestions=[
                "Check that all parameters are the correct type",
                "Refer to the API documentation for parameter types"
            ],
        )

    def to_error_response(self) -> ErrorResponse:
        """Convert to ErrorResponse schema."""
        kwargs = {
            "error_type": self.error_type,
            "error_message": self.message,
            "operation": self.operation,
            "suggestions": self.suggestions or None,
        }

        if self.error_code:
            kwargs["error_code"] = self.error_code

        if self.field_name:
            kwargs["field_name"] = self.field_name
        if self.invalid_value is not None:
            kwargs["invalid_value"] = self.invalid_value
        if self.expected_format:
            kwargs["expected_format"] = self.expected_format

        if self.violation_type:
            kwargs["violation_type"] = self.violation_type
        if self.attempted_action:
            kwargs["attempted_action"] = self.attempted_action
        if self.allowed_scope:
            kwargs["allowed_scope"] = self.allowed_scope

        if self.config_key:
            kwargs["config_key"] = self.config_key
        if self.config_value is not None:
            kwargs["config_value"] = self.config_value

        if self.processing_stage:
            kwargs["processing_stage"] = self.processing_stage
        if self.data_type:
            kwargs["data_type"] = self.data_type

        return ErrorResponse(**kwargs)

    def to_http_exception(self, status_code: int = 500) -> HTTPException:
        """Convert to HTTPException for FastAPI."""
        logger.error(
            "Error occurred [%s]: %s",
            self.correlation_id,
            self.message,
            extra={
                "correlation_id": self.correlation_id,
                "error_type": self.error_type,
                "operation": self.operation,
                "context": self.context,
            },
        )

        return HTTPException(
            status_code=status_code,
            detail=self.to_error_response().model_dump()
        )

    def log(self, level: int = logging.ERROR) -> None:
        """Log error with structured context."""
        logger.log(
            level,
            "Error [%s]: %s",
            self.correlation_id,
            self.message,
            extra={
                "correlation_id": self.correlation_id,
                "error_type": self.error_type,
                "error_code": self.error_code,
                "operation": self.operation,
                "field_name": self.field_name,
                "violation_type": self.violation_type,
                "config_key": self.config_key,
                "processing_stage": self.processing_stage,
                "context": self.context,
                "timestamp": self.timestamp.isoformat(),
            },
        )


def parse_network_error(error_msg: str, operation: str = "operation") -> ErrorContext:
    """
    Parse a raw error message and create network error context.

    This replaces the old parse_network_error function.
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

    return ErrorContext.network_error(error_code, friendly_message, operation)


def parse_security_error(error_msg: str, attempted_path: str = "", allowed_dir: str = "") -> ErrorContext:
    """Parse security-related errors, particularly path validation errors."""
    if "must be within" in error_msg and "outside the allowed directory" in error_msg:
        return ErrorContext.security_error(
            violation_type="path_traversal",
            attempted_action=f"Access path: {attempted_path}",
            allowed_scope=allowed_dir,
            message=error_msg,
        )

    return ErrorContext.security_error(
        violation_type="access_denied",
        attempted_action="unknown action",
        allowed_scope="allowed operations only",
        message=error_msg,
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
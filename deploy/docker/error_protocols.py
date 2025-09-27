# deploy/docker/error_protocols.py

from __future__ import annotations

from typing import Protocol, runtime_checkable, Optional, Dict, Any
from abc import abstractmethod


@runtime_checkable
class NetworkError(Protocol):
    """Protocol for network-related errors."""

    @property
    @abstractmethod
    def error_code(self) -> str:
        """Network error code (e.g., ERR_NAME_NOT_RESOLVED)."""
        ...

    @property
    @abstractmethod
    def message(self) -> str:
        """Original error message."""
        ...

    @property
    @abstractmethod
    def operation(self) -> str:
        """Operation that failed (e.g., 'Fetch HTML', 'Screenshot capture')."""
        ...


@runtime_checkable
class ValidationError(Protocol):
    """Protocol for input validation errors."""

    @property
    @abstractmethod
    def field_name(self) -> str:
        """Name of the field that failed validation."""
        ...

    @property
    @abstractmethod
    def invalid_value(self) -> Any:
        """The invalid value that was provided."""
        ...

    @property
    @abstractmethod
    def expected_format(self) -> str:
        """Description of the expected format."""
        ...


@runtime_checkable
class SecurityError(Protocol):
    """Protocol for security-related errors."""

    @property
    @abstractmethod
    def violation_type(self) -> str:
        """Type of security violation (e.g., 'path_traversal', 'access_denied')."""
        ...

    @property
    @abstractmethod
    def attempted_action(self) -> str:
        """What action was attempted."""
        ...

    @property
    @abstractmethod
    def allowed_scope(self) -> str:
        """Description of allowed scope/boundaries."""
        ...


@runtime_checkable
class ConfigurationError(Protocol):
    """Protocol for configuration-related errors."""

    @property
    @abstractmethod
    def config_key(self) -> str:
        """Configuration key that caused the error."""
        ...

    @property
    @abstractmethod
    def config_value(self) -> Any:
        """Configuration value that was invalid."""
        ...

    @property
    @abstractmethod
    def suggestion(self) -> str:
        """Suggested fix for the configuration issue."""
        ...


@runtime_checkable
class ProcessingError(Protocol):
    """Protocol for data processing errors."""

    @property
    @abstractmethod
    def processing_stage(self) -> str:
        """Stage where processing failed (e.g., 'normalization', 'serialization')."""
        ...

    @property
    @abstractmethod
    def data_type(self) -> str:
        """Type of data being processed."""
        ...

    @property
    @abstractmethod
    def recovery_suggestion(self) -> str:
        """Suggestion for how to recover from this error."""
        ...


class CrawlError:
    """Base implementation for crawl-related errors."""

    def __init__(self, message: str, operation: str = "operation", context: Optional[Dict[str, Any]] = None):
        self._message = message
        self._operation = operation
        self.context = context or {}

    @property
    def message(self) -> str:
        return self._message

    @property
    def operation(self) -> str:
        return self._operation


class NetworkErrorImpl(CrawlError):
    """Implementation of NetworkError protocol."""

    def __init__(self, error_code: str, message: str, operation: str = "operation"):
        super().__init__(message, operation)
        self._error_code = error_code

    @property
    def error_code(self) -> str:
        return self._error_code



class ValidationErrorImpl(CrawlError):
    """Implementation of ValidationError protocol."""

    def __init__(self, field_name: str, invalid_value: Any, expected_format: str, message: str = ""):
        super().__init__(message or f"Invalid value for {field_name}")
        self._field_name = field_name
        self._invalid_value = invalid_value
        self._expected_format = expected_format

    @property
    def field_name(self) -> str:
        return self._field_name

    @property
    def invalid_value(self) -> Any:
        return self._invalid_value

    @property
    def expected_format(self) -> str:
        return self._expected_format


class SecurityErrorImpl(CrawlError):
    """Implementation of SecurityError protocol."""

    def __init__(self, violation_type: str, attempted_action: str, allowed_scope: str, message: str = ""):
        super().__init__(message or f"Security violation: {violation_type}")
        self._violation_type = violation_type
        self._attempted_action = attempted_action
        self._allowed_scope = allowed_scope

    @property
    def violation_type(self) -> str:
        return self._violation_type

    @property
    def attempted_action(self) -> str:
        return self._attempted_action

    @property
    def allowed_scope(self) -> str:
        return self._allowed_scope


class ConfigurationErrorImpl(CrawlError):
    """Implementation of ConfigurationError protocol."""

    def __init__(self, config_key: str, config_value: Any, suggestion: str, message: str = ""):
        super().__init__(message or f"Invalid configuration for {config_key}")
        self._config_key = config_key
        self._config_value = config_value
        self._suggestion = suggestion

    @property
    def config_key(self) -> str:
        return self._config_key

    @property
    def config_value(self) -> Any:
        return self._config_value

    @property
    def suggestion(self) -> str:
        return self._suggestion


class ProcessingErrorImpl(CrawlError):
    """Implementation of ProcessingError protocol."""

    def __init__(self, processing_stage: str, data_type: str, recovery_suggestion: str, message: str = ""):
        super().__init__(message or f"Processing failed at {processing_stage}")
        self._processing_stage = processing_stage
        self._data_type = data_type
        self._recovery_suggestion = recovery_suggestion

    @property
    def processing_stage(self) -> str:
        return self._processing_stage

    @property
    def data_type(self) -> str:
        return self._data_type

    @property
    def recovery_suggestion(self) -> str:
        return self._recovery_suggestion
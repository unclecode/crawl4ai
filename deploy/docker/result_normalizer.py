# deploy/docker/result_normalizer.py

from __future__ import annotations

import os
import pathlib
from base64 import b64encode
from datetime import datetime, date
from functools import singledispatch
from typing import List, Any, Union, AsyncGenerator

from result_protocols import ResultContainer, SingleResult, AsyncResultGenerator


def datetime_handler(obj):
    """Handle datetime serialization - imported from existing logic."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    return obj


@singledispatch
def normalize_results(results: Any) -> List[Any]:
    """
    Default handler for unknown result types.

    Args:
        results: Any type of results to normalize

    Returns:
        List of normalized results
    """
    if results is None:
        return []
    # Fallback: wrap single unknown object in list
    return [results]


@normalize_results.register
def _(results: list) -> List[Any]:
    """Handle list of results."""
    return results


@normalize_results.register
def _(results: tuple) -> List[Any]:
    """Handle tuple of results."""
    return list(results)


@normalize_results.register
def _(results: type(None)) -> List[Any]:
    """Handle None results."""
    return []


def normalize_results_protocol_dispatch(results: Any) -> List[Any]:
    """
    Protocol-based dispatcher for result containers.

    This handles duck-typed objects that implement the ResultContainer protocol
    without requiring explicit registration.
    """
    # Check for ResultContainer protocol first
    if isinstance(results, ResultContainer):
        return list(results.results)

    # Check for async generator protocol
    if isinstance(results, AsyncResultGenerator):
        # For async generators, we need to collect results
        # This will be handled by the calling code that can await
        raise ValueError("Async generators must be handled by caller with async collection")

    # Check for other iterables (but not strings/bytes/dicts)
    if hasattr(results, '__iter__') and not isinstance(results, (str, bytes, dict)):
        try:
            return list(results)
        except (TypeError, ValueError):
            pass

    # Fall back to single dispatch
    return normalize_results(results)


def normalize_value_recursive(val: Any) -> Any:
    """
    Recursively normalize values for JSON serialization.

    Handles Path objects, datetime objects, and nested collections.
    """
    if isinstance(val, (datetime, date)):
        return datetime_handler(val)
    if isinstance(val, (os.PathLike, pathlib.Path)):
        return os.fspath(val)
    if isinstance(val, bytes):
        return b64encode(val).decode('utf-8')
    if isinstance(val, dict):
        return {k: normalize_value_recursive(v) for k, v in val.items()}
    if isinstance(val, (list, tuple, set)):
        return [normalize_value_recursive(v) for v in val]
    return val


def normalize_single_result(result: Any) -> dict:
    """
    Normalize a single result object to a dictionary.

    Args:
        result: Single result object to normalize

    Returns:
        Dictionary representation of the result
    """
    if hasattr(result, "model_dump"):
        result_dict = result.model_dump()
    elif isinstance(result, dict):
        result_dict = result.copy()
        result_dict.setdefault("success", False)
    else:
        result_dict = {
            "url": getattr(result, "url", ""),
            "success": getattr(result, "success", False),
            "error_message": getattr(result, "error_message", "Unknown error"),
        }

    # Recursively normalize all values
    cleaned_dict = {}
    for key, value in result_dict.items():
        # Special handling for PDF binary data (preserve existing logic)
        if key == 'pdf' and value is not None and isinstance(value, bytes):
            cleaned_dict[key] = b64encode(value).decode('utf-8')
            continue

        # Recursively normalize the value
        normalized = normalize_value_recursive(value)
        try:
            # Test JSON serializability by attempting to encode
            import json
            json.dumps(normalized)
            cleaned_dict[key] = normalized
        except (TypeError, ValueError):
            # If it still can't be serialized, skip it
            pass

    return cleaned_dict
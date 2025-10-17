# deploy/docker/result_handler.py

from __future__ import annotations

import json
import os
import pathlib
from base64 import b64encode
from datetime import datetime, date
from typing import Any, List, Dict, Union, AsyncGenerator


class ResultHandler:
    """
    Unified result normalization handler.

    Replaces result_protocols.py and result_normalizer.py with a single,
    clean implementation that handles all result types without protocol complexity.
    """

    @staticmethod
    def normalize_value(val: Any) -> Any:
        """
        Normalize a single value for JSON serialization.

        Handles datetime, Path, bytes, and nested collections.
        """
        if val is None:
            return None

        if isinstance(val, (datetime, date)):
            return val.isoformat()

        if isinstance(val, (os.PathLike, pathlib.Path)):
            return os.fspath(val)

        if isinstance(val, bytes):
            return b64encode(val).decode('utf-8')

        if isinstance(val, dict):
            return {k: ResultHandler.normalize_value(v) for k, v in val.items()}

        if isinstance(val, (list, tuple, set)):
            return [ResultHandler.normalize_value(v) for v in val]

        return val

    @staticmethod
    def normalize_single_result(result: Any) -> Dict[str, Any]:
        """
        Normalize a single result object to a dictionary.

        Args:
            result: Single result object (Pydantic model, dict, or object with attributes)

        Returns:
            Dictionary representation ready for JSON serialization
        """
        # Handle Pydantic models
        if hasattr(result, "model_dump"):
            result_dict = result.model_dump()
        # Handle plain dicts
        elif isinstance(result, dict):
            result_dict = result.copy()
            result_dict.setdefault("success", False)
        # Handle objects with attributes
        else:
            result_dict = {
                "url": getattr(result, "url", ""),
                "success": getattr(result, "success", False),
                "error_message": getattr(result, "error_message", "Unknown error"),
            }

        # Normalize all values
        cleaned_dict = {}
        for key, value in result_dict.items():
            normalized = ResultHandler.normalize_value(value)

            # Test JSON serializability
            try:
                json.dumps(normalized)
                cleaned_dict[key] = normalized
            except (TypeError, ValueError):
                # Skip non-serializable values
                pass

        return cleaned_dict

    @staticmethod
    def normalize_results(results: Any) -> List[Dict[str, Any]]:
        """
        Normalize any result type to a list of dictionaries.

        Handles:
        - None → []
        - Single result → [result]
        - List/tuple → [result1, result2, ...]
        - Objects with .results attribute → [result1, result2, ...]
        - Iterables → [result1, result2, ...]

        Args:
            results: Any type of results

        Returns:
            List of normalized result dictionaries
        """
        # Handle None
        if results is None:
            return []

        # Handle objects with .results attribute (containers)
        if hasattr(results, 'results'):
            try:
                return [
                    ResultHandler.normalize_single_result(r)
                    for r in results.results
                ]
            except (TypeError, AttributeError):
                pass

        # Handle lists and tuples directly
        if isinstance(results, (list, tuple)):
            return [ResultHandler.normalize_single_result(r) for r in results]

        # Handle other iterables (but not strings/bytes/dicts)
        if hasattr(results, '__iter__') and not isinstance(results, (str, bytes, dict)):
            try:
                return [ResultHandler.normalize_single_result(r) for r in results]
            except (TypeError, ValueError):
                pass

        # Handle single result
        return [ResultHandler.normalize_single_result(results)]

    @staticmethod
    async def collect_async_results(
        async_gen: AsyncGenerator[Any, None]
    ) -> List[Dict[str, Any]]:
        """
        Collect and normalize results from async generator.

        Args:
            async_gen: Async generator yielding results

        Returns:
            List of normalized result dictionaries
        """
        results = []
        async for result in async_gen:
            normalized = ResultHandler.normalize_single_result(result)
            results.append(normalized)
        return results

    @staticmethod
    def is_json_serializable(obj: Any) -> bool:
        """
        Test if an object is JSON serializable.

        Args:
            obj: Object to test

        Returns:
            True if serializable, False otherwise
        """
        try:
            json.dumps(obj)
            return True
        except (TypeError, ValueError):
            return False
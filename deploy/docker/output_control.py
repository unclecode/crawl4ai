"""
Output Control Module - Pagination and field control for API responses.

This module provides the `apply_output_control()` function that applies pagination,
limiting, and field exclusion to CrawlResult dictionaries before returning them
to clients.

The function is designed to be:
- Non-destructive: Makes copies, doesn't modify the original data
- Backward compatible: Returns unchanged data when control is None
- Comprehensive: Handles all field types (text, collections, nested)
- Informative: Returns metadata about what was truncated
"""

import copy
from typing import Any, Dict, List, Optional, Tuple

from schemas import (
    CollectionStats,
    ContentFieldStats,
    OutputControl,
    OutputMeta,
)


def _get_nested_value(data: Dict[str, Any], path: str) -> Optional[Any]:
    """Get a value from a nested dict using dot notation.

    Args:
        data: The dictionary to traverse
        path: Dot-separated path (e.g., 'markdown.raw_markdown')

    Returns:
        The value at the path, or None if not found
    """
    parts = path.split(".")
    current = data
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _set_nested_value(data: Dict[str, Any], path: str, value: Any) -> None:
    """Set a value in a nested dict using dot notation.

    Args:
        data: The dictionary to modify
        path: Dot-separated path (e.g., 'markdown.raw_markdown')
        value: The value to set
    """
    parts = path.split(".")
    current = data
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def _delete_nested_value(data: Dict[str, Any], path: str) -> bool:
    """Delete a value from a nested dict using dot notation.

    Args:
        data: The dictionary to modify
        path: Dot-separated path (e.g., 'markdown.raw_markdown')

    Returns:
        True if the value was deleted, False if not found
    """
    parts = path.split(".")
    current = data
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]

    if isinstance(current, dict) and parts[-1] in current:
        del current[parts[-1]]
        return True
    return False


def apply_output_control(
    data: Dict[str, Any], control: Optional[OutputControl]
) -> Tuple[Dict[str, Any], Optional[OutputMeta]]:
    """
    Apply pagination, limiting, and field exclusion to a CrawlResult dict.

    This function is the core of the output control system. It processes a
    CrawlResult dictionary and applies the requested pagination, collection
    limiting, and field exclusion operations.

    Args:
        data: The result of CrawlResult.model_dump() - a dictionary representation
              of the crawl result. This should contain fields like:
              - html: str
              - cleaned_html: str
              - markdown: dict with raw_markdown, fit_markdown, etc.
              - links: dict with internal, external lists
              - media: dict with images, videos, audios lists
              - tables: list
              - etc.
        control: Output control configuration. If None, returns the original
                 data unchanged with no metadata.

    Returns:
        Tuple of:
        - Modified data dictionary (deep copy if any modifications were made)
        - OutputMeta if any truncation occurred, None otherwise

    Notes:
        - The function makes a deep copy of the data before modifications
        - Metadata is added to the result under the '_output_meta' key
        - All parameters in OutputControl are optional; only specified
          operations are applied
        - The function handles missing fields gracefully

    Example:
        >>> control = OutputControl(content_limit=5000, max_links=10)
        >>> result, meta = apply_output_control(crawl_result, control)
        >>> if meta and meta.truncated:
        ...     print(f"Content was truncated: {meta.content_stats}")
    """
    # Fast path: no control specified means no changes
    if control is None:
        return data, None

    # Check if any control options are actually set
    has_pagination = (
        control.content_offset is not None or control.content_limit is not None
    )
    has_collection_limits = (
        control.max_links is not None
        or control.max_media is not None
        or control.max_tables is not None
    )
    has_exclusions = (
        control.exclude_fields is not None and len(control.exclude_fields) > 0
    )

    # If no options are set, return unchanged
    if not (has_pagination or has_collection_limits or has_exclusions):
        return data, None

    # Make a deep copy to avoid modifying the original
    data = copy.deepcopy(data)

    # Initialize metadata
    meta = OutputMeta(truncated=False)

    # 1. Apply field exclusion first (before other processing)
    if has_exclusions:
        excluded = []
        for field in control.exclude_fields:
            if "." in field:
                # Nested field exclusion (e.g., 'markdown.references_markdown')
                if _delete_nested_value(data, field):
                    excluded.append(field)
            elif field in data:
                # Top-level field exclusion
                del data[field]
                excluded.append(field)

        if excluded:
            meta.excluded_fields = excluded
            meta.truncated = True

    # 2. Apply content pagination to text fields
    if has_pagination:
        content_stats: Dict[str, ContentFieldStats] = {}

        # Define text fields to paginate
        # Top-level text fields
        top_level_text_fields = [
            "html",
            "cleaned_html",
            "fit_html",
            "extracted_content",
        ]

        # Nested markdown fields
        markdown_fields = [
            "markdown.raw_markdown",
            "markdown.fit_markdown",
            "markdown.markdown_with_citations",
            "markdown.references_markdown",
        ]

        offset = control.content_offset or 0
        limit = control.content_limit

        # Process top-level text fields
        for field in top_level_text_fields:
            if field in data and isinstance(data[field], str):
                content = data[field]
                total = len(content)

                if limit is not None or offset > 0:
                    sliced = (
                        content[offset : offset + limit] if limit else content[offset:]
                    )
                    returned = len(sliced)
                    data[field] = sliced

                    # Record stats if truncation occurred
                    if returned < total or offset > 0:
                        content_stats[field] = ContentFieldStats(
                            total_chars=total,
                            returned_chars=returned,
                            offset=offset,
                            has_more=(offset + returned) < total,
                        )

        # Process nested markdown fields
        for field_path in markdown_fields:
            content = _get_nested_value(data, field_path)
            if content is not None and isinstance(content, str):
                total = len(content)

                if limit is not None or offset > 0:
                    sliced = (
                        content[offset : offset + limit] if limit else content[offset:]
                    )
                    returned = len(sliced)
                    _set_nested_value(data, field_path, sliced)

                    # Record stats if truncation occurred
                    if returned < total or offset > 0:
                        content_stats[field_path] = ContentFieldStats(
                            total_chars=total,
                            returned_chars=returned,
                            offset=offset,
                            has_more=(offset + returned) < total,
                        )

        if content_stats:
            meta.content_stats = content_stats
            meta.truncated = True

    # 3. Apply collection limiting
    collection_stats: Dict[str, CollectionStats] = {}

    # Limit links (applies to both internal and external)
    if (
        control.max_links is not None
        and "links" in data
        and isinstance(data["links"], dict)
    ):
        for link_type in ["internal", "external"]:
            if link_type in data["links"] and isinstance(
                data["links"][link_type], list
            ):
                items = data["links"][link_type]
                total = len(items)
                if total > control.max_links:
                    data["links"][link_type] = items[: control.max_links]
                    collection_stats[f"links.{link_type}"] = CollectionStats(
                        total_count=total, returned_count=control.max_links
                    )

    # Limit media (applies to images, videos, audios)
    if (
        control.max_media is not None
        and "media" in data
        and isinstance(data["media"], dict)
    ):
        for media_type in ["images", "videos", "audios"]:
            if media_type in data["media"] and isinstance(
                data["media"][media_type], list
            ):
                items = data["media"][media_type]
                total = len(items)
                if total > control.max_media:
                    data["media"][media_type] = items[: control.max_media]
                    collection_stats[f"media.{media_type}"] = CollectionStats(
                        total_count=total, returned_count=control.max_media
                    )

    # Limit tables
    if (
        control.max_tables is not None
        and "tables" in data
        and isinstance(data["tables"], list)
    ):
        items = data["tables"]
        total = len(items)
        if total > control.max_tables:
            data["tables"] = items[: control.max_tables]
            collection_stats["tables"] = CollectionStats(
                total_count=total, returned_count=control.max_tables
            )

    if collection_stats:
        meta.collection_stats = collection_stats
        meta.truncated = True

    # Only add metadata to response if something was actually modified
    if meta.truncated:
        data["_output_meta"] = meta.model_dump(exclude_none=True)
        return data, meta

    return data, None


def apply_output_control_to_batch(
    results: List[Dict[str, Any]], control: Optional[OutputControl]
) -> List[Dict[str, Any]]:
    """
    Apply output control to a batch of results.

    Convenience function for applying output control to multiple CrawlResult
    dictionaries, such as when processing batch crawl results.

    Args:
        results: List of CrawlResult dictionaries
        control: Output control configuration (applied to each result)

    Returns:
        List of modified result dictionaries
    """
    if control is None:
        return results

    return [apply_output_control(result, control)[0] for result in results]

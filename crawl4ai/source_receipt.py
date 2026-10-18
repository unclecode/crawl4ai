"""Opt-in provenance for exact returned Markdown; never serialize config secrets."""

import hashlib
import json
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

from .__version__ import __version__

_METADATA_KEY = "_crawl4ai_source_receipt_v1"
_PROCESSING_OPTIONS = (
    "word_count_threshold",
    "only_text",
    "remove_forms",
    "parser_type",
)


def _url(value):
    """Omit credentials, query parameters, fragments, and caller-provided HTML."""
    try:
        parts = urlsplit(value or "")
        if parts.scheme not in ("http", "https") or not parts.hostname:
            return None
        host = parts.hostname
        if ":" in host:
            host = "[" + host + "]"
        if parts.port:
            host += ":" + str(parts.port)
        return urlunsplit((parts.scheme, host, parts.path, "", ""))
    except ValueError:
        return None


def _timestamp(value):
    return (
        datetime.fromtimestamp(value, timezone.utc).isoformat()
        if value is not None
        else None
    )


def attach_source_receipt(result, config, *, fetched_at=None):
    """Attach a JSON-safe receipt and persist minimal provenance in cache metadata.

    Cache hits use only previously recorded fetch metadata. Legacy cache entries
    keep unknown values as null; served_at is never substituted for fetched_at.
    """
    if not result.success:
        return
    cached = (result.cache_status or "").startswith("hit")
    metadata = dict(result.metadata or {})
    previous = metadata.get(_METADATA_KEY)
    if cached:
        provenance = previous if isinstance(previous, dict) else {}
    else:
        options = {key: getattr(config, key, None) for key in _PROCESSING_OPTIONS}
        # Only a small, documented allowlist of primitive processing options.
        encoded = json.dumps(
            options, sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        provenance = {
            "fetched_at": (
                None
                if result.url.startswith(("raw:", "file:"))
                else _timestamp(fetched_at)
            ),
            "crawler_version": __version__,
            "processing_fingerprint": hashlib.sha256(
                encoded.encode("utf-8")
            ).hexdigest(),
        }
        metadata[_METADATA_KEY] = provenance
        result.metadata = metadata
    markdown = result.markdown
    outputs = {}
    for kind in ("raw_markdown", "fit_markdown"):
        value = getattr(markdown, kind, None) if markdown is not None else None
        if isinstance(value, str):
            payload = value.encode("utf-8")
            outputs[kind] = {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "utf8_bytes": len(payload),
            }
    result.source_receipt = {
        "schema_version": 1,
        "requested_url": _url(result.url),
        "final_url": _url(result.redirected_url),
        "fetched_at": provenance.get("fetched_at"),
        "served_at": datetime.now(timezone.utc).isoformat(),
        "cache_status": result.cache_status,
        "crawler_version": provenance.get("crawler_version"),
        "processing_fingerprint": provenance.get("processing_fingerprint"),
        "processing_option_names": list(_PROCESSING_OPTIONS),
        "digest_rule": "sha256-exact-utf8-v1",
        "outputs": outputs,
    }

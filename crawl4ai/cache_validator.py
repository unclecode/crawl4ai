"""
Cache validation using HTTP conditional requests and head fingerprinting.

Uses httpx for fast, lightweight HTTP requests (no browser needed).
This module enables smart cache validation to avoid unnecessary full browser crawls
when content hasn't changed.

Validation Strategy:
1. Send HEAD request with If-None-Match / If-Modified-Since headers
2. If server returns 304 Not Modified → cache is FRESH
3. If server returns 200 → fetch <head> and compare fingerprint
4. If fingerprint matches → cache is FRESH (minor changes only)
5. Otherwise → cache is STALE, need full recrawl
"""

import httpx
from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum

from .utils import compute_head_fingerprint


class CacheValidationResult(Enum):
    """Result of cache validation check."""
    FRESH = "fresh"       # Content unchanged, use cache
    STALE = "stale"       # Content changed, need recrawl
    UNKNOWN = "unknown"   # Couldn't determine, need recrawl
    ERROR = "error"       # Request failed, use cache as fallback


@dataclass
class ValidationResult:
    """Detailed result of a cache validation attempt."""
    status: CacheValidationResult
    new_etag: Optional[str] = None
    new_last_modified: Optional[str] = None
    new_head_fingerprint: Optional[str] = None
    reason: str = ""


class CacheValidator:
    """
    Validates cache freshness using lightweight HTTP requests.

    This validator uses httpx to make fast HTTP requests without needing
    a full browser. It supports two validation methods:

    1. HTTP Conditional Requests (Layer 3):
       - Uses If-None-Match with stored ETag
       - Uses If-Modified-Since with stored Last-Modified
       - Server returns 304 if content unchanged

    2. Head Fingerprinting (Layer 4):
       - Fetches only the <head> section (~5KB)
       - Compares fingerprint of key meta tags
       - Catches changes even without server support for conditional requests
    """

    def __init__(self, timeout: float = 10.0, user_agent: Optional[str] = None):
        """
        Initialize the cache validator.

        Args:
            timeout: Request timeout in seconds
            user_agent: Custom User-Agent string (optional)
        """
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; Crawl4AI/1.0)"
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the httpx client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                http2=True,
                timeout=self.timeout,
                follow_redirects=True,
                headers={"User-Agent": self.user_agent}
            )
        return self._client

    async def validate(
        self,
        url: str,
        stored_etag: Optional[str] = None,
        stored_last_modified: Optional[str] = None,
        stored_head_fingerprint: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validate if cached content is still fresh.

        Args:
            url: The URL to validate
            stored_etag: Previously stored ETag header value
            stored_last_modified: Previously stored Last-Modified header value
            stored_head_fingerprint: Previously computed head fingerprint

        Returns:
            ValidationResult with status and any updated metadata
        """
        client = await self._get_client()

        # Build conditional request headers
        headers = {}
        if stored_etag:
            headers["If-None-Match"] = stored_etag
        if stored_last_modified:
            headers["If-Modified-Since"] = stored_last_modified

        try:
            # Step 1: Try HEAD request with conditional headers
            if headers:
                response = await client.head(url, headers=headers)

                if response.status_code == 304:
                    return ValidationResult(
                        status=CacheValidationResult.FRESH,
                        reason="Server returned 304 Not Modified"
                    )

                # Got 200, extract new headers for potential update
                new_etag = response.headers.get("etag")
                new_last_modified = response.headers.get("last-modified")

                # If we have fingerprint, compare it
                if stored_head_fingerprint:
                    head_html, _, _ = await self._fetch_head(url)
                    if head_html:
                        new_fingerprint = compute_head_fingerprint(head_html)
                        if new_fingerprint and new_fingerprint == stored_head_fingerprint:
                            return ValidationResult(
                                status=CacheValidationResult.FRESH,
                                new_etag=new_etag,
                                new_last_modified=new_last_modified,
                                new_head_fingerprint=new_fingerprint,
                                reason="Head fingerprint matches"
                            )
                        elif new_fingerprint:
                            return ValidationResult(
                                status=CacheValidationResult.STALE,
                                new_etag=new_etag,
                                new_last_modified=new_last_modified,
                                new_head_fingerprint=new_fingerprint,
                                reason="Head fingerprint changed"
                            )

                # Headers changed and no fingerprint match
                return ValidationResult(
                    status=CacheValidationResult.STALE,
                    new_etag=new_etag,
                    new_last_modified=new_last_modified,
                    reason="Server returned 200, content may have changed"
                )

            # Step 2: No conditional headers available, try fingerprint only
            if stored_head_fingerprint:
                head_html, new_etag, new_last_modified = await self._fetch_head(url)

                if head_html:
                    new_fingerprint = compute_head_fingerprint(head_html)

                    if new_fingerprint and new_fingerprint == stored_head_fingerprint:
                        return ValidationResult(
                            status=CacheValidationResult.FRESH,
                            new_etag=new_etag,
                            new_last_modified=new_last_modified,
                            new_head_fingerprint=new_fingerprint,
                            reason="Head fingerprint matches"
                        )
                    elif new_fingerprint:
                        return ValidationResult(
                            status=CacheValidationResult.STALE,
                            new_etag=new_etag,
                            new_last_modified=new_last_modified,
                            new_head_fingerprint=new_fingerprint,
                            reason="Head fingerprint changed"
                        )

            # Step 3: No validation data available
            return ValidationResult(
                status=CacheValidationResult.UNKNOWN,
                reason="No validation data available (no etag, last-modified, or fingerprint)"
            )

        except httpx.TimeoutException:
            return ValidationResult(
                status=CacheValidationResult.ERROR,
                reason="Validation request timed out"
            )
        except httpx.RequestError as e:
            return ValidationResult(
                status=CacheValidationResult.ERROR,
                reason=f"Validation request failed: {type(e).__name__}"
            )
        except Exception as e:
            # On unexpected error, prefer using cache over failing
            return ValidationResult(
                status=CacheValidationResult.ERROR,
                reason=f"Validation error: {str(e)}"
            )

    async def _fetch_head(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Fetch only the <head> section of a page.

        Uses streaming to stop reading after </head> is found,
        minimizing bandwidth usage.

        Args:
            url: The URL to fetch

        Returns:
            Tuple of (head_html, etag, last_modified)
        """
        client = await self._get_client()

        try:
            async with client.stream(
                "GET",
                url,
                headers={"Accept-Encoding": "identity"}  # Disable compression for easier parsing
            ) as response:
                etag = response.headers.get("etag")
                last_modified = response.headers.get("last-modified")

                if response.status_code != 200:
                    return None, etag, last_modified

                # Read until </head> or max 64KB
                chunks = []
                total_bytes = 0
                max_bytes = 65536

                async for chunk in response.aiter_bytes(4096):
                    chunks.append(chunk)
                    total_bytes += len(chunk)

                    content = b''.join(chunks)
                    # Check for </head> (case insensitive)
                    if b'</head>' in content.lower() or b'</HEAD>' in content:
                        break
                    if total_bytes >= max_bytes:
                        break

                html = content.decode('utf-8', errors='replace')

                # Extract just the head section
                head_end = html.lower().find('</head>')
                if head_end != -1:
                    html = html[:head_end + 7]

                return html, etag, last_modified

        except Exception:
            return None, None, None

    async def close(self):
        """Close the HTTP client and release resources."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

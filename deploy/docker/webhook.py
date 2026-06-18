"""
Webhook delivery service for Crawl4AI.

This module provides webhook notification functionality with exponential backoff retry logic.
"""
import asyncio
import logging
import re
import socket
from typing import Dict, List, Optional
from datetime import datetime, timezone

import aiohttp
from aiohttp.abc import AbstractResolver

logger = logging.getLogger(__name__)

_MAX_WEBHOOK_REDIRECTS = 5


class _WebhookBlocked(Exception):
    """Webhook target (or a redirect hop) resolved to a non-global address."""


class _PinnedResolver(AbstractResolver):
    """aiohttp resolver that returns a single pre-pinned IP for the target host.

    aiohttp connects to this IP but still performs TLS SNI / certificate
    verification against the original hostname, so this pins the connection
    (closing DNS rebinding) without weakening TLS or doing a MITM.
    """

    def __init__(self, host: str, ip: str):
        self._host = host
        self._ip = ip

    async def resolve(self, host, port=0, family=socket.AF_INET):
        return [{
            "hostname": host,
            "host": self._ip,
            "port": port,
            "family": family,
            "proto": 0,
            "flags": 0,
        }]

    async def close(self):
        pass

# Webhook request-header policy: user-controlled outbound headers could inject
# hop-by-hop / smuggling headers or CRLF. Allow only well-formed names, reject
# control chars in values, and deny sensitive/hop-by-hop names.
_WEBHOOK_HEADER_NAME = re.compile(r"^[A-Za-z0-9-]{1,64}$")
_WEBHOOK_DENY_HEADERS = {
    "host", "content-length", "transfer-encoding", "connection",
    "content-type", "proxy-authorization", "authorization", "cookie",
    "expect", "upgrade", "te", "trailer",
}
_MAX_WEBHOOK_HEADERS = 20
_MAX_WEBHOOK_HEADER_VALUE = 2048


def sanitize_webhook_headers(headers: Optional[Dict[str, str]]) -> Dict[str, str]:
    """Validate user-supplied webhook headers; raise ValueError on any bad one."""
    if not headers:
        return {}
    if len(headers) > _MAX_WEBHOOK_HEADERS:
        raise ValueError("too many webhook headers")
    clean: Dict[str, str] = {}
    for name, value in headers.items():
        if not isinstance(name, str) or not _WEBHOOK_HEADER_NAME.match(name):
            raise ValueError(f"invalid webhook header name: {name!r}")
        if name.lower() in _WEBHOOK_DENY_HEADERS:
            raise ValueError(f"webhook header not allowed: {name}")
        sval = str(value)
        if len(sval) > _MAX_WEBHOOK_HEADER_VALUE or any(c in sval for c in "\r\n\x00"):
            raise ValueError(f"invalid value for webhook header {name}")
        clean[name] = sval
    return clean


class WebhookDeliveryService:
    """Handles webhook delivery with exponential backoff retry logic."""

    def __init__(self, config: Dict):
        """
        Initialize the webhook delivery service.

        Args:
            config: Application configuration dictionary containing webhook settings
        """
        self.config = config.get("webhooks", {})
        self.max_attempts = self.config.get("retry", {}).get("max_attempts", 5)
        self.initial_delay = self.config.get("retry", {}).get("initial_delay_ms", 1000) / 1000
        self.max_delay = self.config.get("retry", {}).get("max_delay_ms", 32000) / 1000
        self.timeout = self.config.get("retry", {}).get("timeout_ms", 30000) / 1000

    async def send_webhook(
        self,
        webhook_url: str,
        payload: Dict,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send webhook with exponential backoff retry logic.

        Args:
            webhook_url: The URL to send the webhook to
            payload: The JSON payload to send
            headers: Optional custom headers

        Returns:
            bool: True if delivered successfully, False otherwise
        """
        default_headers = self.config.get("headers", {})
        try:
            safe_custom = sanitize_webhook_headers(headers)
        except ValueError as e:
            # Defense in depth (the schema validator rejects these at request
            # time); never send a forged/unsafe header.
            logger.warning(f"Dropping unsafe webhook headers: {e}")
            safe_custom = {}
        merged_headers = {**default_headers, **safe_custom}
        merged_headers["Content-Type"] = "application/json"

        for attempt in range(self.max_attempts):
            try:
                status = await self._deliver(webhook_url, payload, merged_headers)
                if 200 <= status < 300:
                    logger.info("Webhook delivered successfully")
                    return True
                if status < 500:
                    logger.warning(f"Webhook rejected with status {status}")
                    return False  # client error - don't retry
                logger.warning(f"Webhook failed with status {status}, will retry")
            except _WebhookBlocked as exc:
                # SSRF: target (or a redirect hop) resolved non-global. Do not
                # retry - it will not become safe.
                logger.warning(f"Webhook blocked (SSRF protection): {exc}")
                return False
            except Exception as exc:
                logger.error(f"Webhook delivery error (attempt {attempt + 1}): {exc}")

            if attempt < self.max_attempts - 1:
                delay = min(self.initial_delay * (2 ** attempt), self.max_delay)
                await asyncio.sleep(delay)
        return False

    async def _deliver(self, url: str, payload: Dict, headers: Dict[str, str]) -> int:
        """POST with the connection pinned to the validated IP, following (and
        re-validating) redirects manually. Returns the final status code."""
        from egress_broker import resolve_and_pin, check_redirect, EgressBlocked, ALLOW_INSECURE_TLS

        current = url
        for _hop in range(_MAX_WEBHOOK_REDIRECTS + 1):
            try:
                pin = resolve_and_pin(current)
            except EgressBlocked as e:
                raise _WebhookBlocked(str(e))

            connector = aiohttp.TCPConnector(resolver=_PinnedResolver(pin.host, pin.ip))
            ssl = None if not ALLOW_INSECURE_TLS else False
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.post(
                    current, json=payload, headers=headers,
                    allow_redirects=False, ssl=ssl,
                ) as resp:
                    if resp.status in (301, 302, 303, 307, 308):
                        loc = resp.headers.get("Location")
                        if not loc:
                            return resp.status
                        # Re-validate every redirect hop before following it.
                        try:
                            check_redirect(loc)
                        except EgressBlocked as e:
                            raise _WebhookBlocked(f"redirect to blocked target: {e}")
                        current = loc
                        continue
                    return resp.status
        raise _WebhookBlocked("too many webhook redirects")

        logger.error(
            f"Webhook delivery failed after {self.max_attempts} attempts to {webhook_url}"
        )
        return False

    async def notify_job_completion(
        self,
        task_id: str,
        task_type: str,
        status: str,
        urls: list,
        webhook_config: Optional[Dict],
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """
        Notify webhook of job completion.

        Args:
            task_id: The task identifier
            task_type: Type of task (e.g., "crawl", "llm_extraction")
            status: Task status ("completed" or "failed")
            urls: List of URLs that were crawled
            webhook_config: Webhook configuration from the job request
            result: Optional crawl result data
            error: Optional error message if failed
        """
        # Determine webhook URL
        webhook_url = None
        data_in_payload = self.config.get("data_in_payload", False)
        custom_headers = None

        if webhook_config:
            webhook_url = webhook_config.get("webhook_url")
            data_in_payload = webhook_config.get("webhook_data_in_payload", data_in_payload)
            custom_headers = webhook_config.get("webhook_headers")

        if not webhook_url:
            webhook_url = self.config.get("default_url")

        if not webhook_url:
            logger.debug("No webhook URL configured, skipping notification")
            return

        # Check if webhooks are enabled
        if not self.config.get("enabled", True):
            logger.debug("Webhooks are disabled, skipping notification")
            return

        # Build payload
        payload = {
            "task_id": task_id,
            "task_type": task_type,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "urls": urls
        }

        if error:
            payload["error"] = error

        if data_in_payload and result:
            payload["data"] = result

        # Send webhook (fire and forget - don't block on completion)
        await self.send_webhook(webhook_url, payload, custom_headers)

"""
Webhook delivery service for Crawl4AI.

This module provides webhook notification functionality with exponential backoff retry logic.
"""
import asyncio
import httpx
import logging
from typing import Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


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
        merged_headers = {**default_headers, **(headers or {})}
        merged_headers["Content-Type"] = "application/json"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_attempts):
                try:
                    logger.info(
                        f"Sending webhook (attempt {attempt + 1}/{self.max_attempts}) to {webhook_url}"
                    )

                    response = await client.post(
                        webhook_url,
                        json=payload,
                        headers=merged_headers
                    )

                    # Success or client error (don't retry client errors)
                    if response.status_code < 500:
                        if 200 <= response.status_code < 300:
                            logger.info(f"Webhook delivered successfully to {webhook_url}")
                            return True
                        else:
                            logger.warning(
                                f"Webhook rejected with status {response.status_code}: {response.text[:200]}"
                            )
                            return False  # Client error - don't retry

                    # Server error - retry with backoff
                    logger.warning(
                        f"Webhook failed with status {response.status_code}, will retry"
                    )

                except httpx.TimeoutException as exc:
                    logger.error(f"Webhook timeout (attempt {attempt + 1}): {exc}")
                except httpx.RequestError as exc:
                    logger.error(f"Webhook request error (attempt {attempt + 1}): {exc}")
                except Exception as exc:
                    logger.error(f"Webhook delivery error (attempt {attempt + 1}): {exc}")

                # Calculate exponential backoff delay
                if attempt < self.max_attempts - 1:
                    delay = min(self.initial_delay * (2 ** attempt), self.max_delay)
                    logger.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)

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

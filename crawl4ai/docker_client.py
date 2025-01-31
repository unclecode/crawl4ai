from typing import List, Optional, Union, AsyncGenerator, Dict, Any
import httpx
import json
from urllib.parse import urljoin

from .async_configs import BrowserConfig, CrawlerRunConfig
from .models import CrawlResult
from .async_logger import AsyncLogger, LogLevel


class Crawl4aiClientError(Exception):
    """Base exception for Crawl4ai Docker client errors."""
    pass


class ConnectionError(Crawl4aiClientError):
    """Raised when connection to the Docker server fails."""
    pass


class RequestError(Crawl4aiClientError):
    """Raised when the server returns an error response."""
    pass


class Crawl4aiDockerClient:
    """
    Client for interacting with Crawl4AI Docker server.
    
    Args:
        base_url (str): Base URL of the Crawl4AI Docker server
        timeout (float): Default timeout for requests in seconds
        verify_ssl (bool): Whether to verify SSL certificates
        verbose (bool): Whether to show logging output
        log_file (str, optional): Path to log file if file logging is desired
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        verify_ssl: bool = True,
        verbose: bool = True,
        log_file: Optional[str] = None
    ) -> None:
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._http_client = httpx.AsyncClient(
            timeout=timeout,
            verify=verify_ssl,
            headers={"Content-Type": "application/json"}
        )
        self.logger = AsyncLogger(
            log_file=log_file,
            log_level=LogLevel.DEBUG,
            verbose=verbose
        )

    async def _check_server_connection(self) -> bool:
        """Check if server is reachable."""
        try:
            self.logger.info("Checking server connection...", tag="INIT")
            response = await self._http_client.get(f"{self.base_url}/health")
            response.raise_for_status()
            self.logger.success(f"Connected to server at {self.base_url}", tag="READY")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to server: {str(e)}", tag="ERROR")
            return False

    def _prepare_request_data(
        self,
        urls: List[str],
        browser_config: Optional[BrowserConfig] = None,
        crawler_config: Optional[CrawlerRunConfig] = None
    ) -> Dict[str, Any]:
        """Prepare request data from configs using dump methods."""
        self.logger.debug("Preparing request data", tag="INIT")
        data = {
            "urls": urls,
            "browser_config": browser_config.dump() if browser_config else {},
            "crawler_config": crawler_config.dump() if crawler_config else {}
        }
        self.logger.debug(f"Request data prepared for {len(urls)} URLs", tag="READY")
        return data

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Union[Dict, AsyncGenerator]:
        """Make HTTP request to the server with error handling."""
        url = urljoin(self.base_url, endpoint)
        
        try:
            self.logger.debug(f"Making {method} request to {endpoint}", tag="FETCH")
            response = await self._http_client.request(method, url, **kwargs)
            response.raise_for_status()
            self.logger.success(f"Request to {endpoint} successful", tag="COMPLETE")
            return response
        except httpx.TimeoutException as e:
            error_msg = f"Request timed out: {str(e)}"
            self.logger.error(error_msg, tag="ERROR")
            raise ConnectionError(error_msg)
        except httpx.RequestError as e:
            error_msg = f"Failed to connect to server: {str(e)}"
            self.logger.error(error_msg, tag="ERROR")
            raise ConnectionError(error_msg)
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get('detail', str(e))
            except (json.JSONDecodeError, AttributeError) as json_err:
                error_detail = f"{str(e)} (Failed to parse error response: {str(json_err)})"
            
            error_msg = f"Server returned error {e.response.status_code}: {error_detail}"
            self.logger.error(error_msg, tag="ERROR")
            raise RequestError(error_msg)

    async def crawl(
        self,
        urls: List[str],
        browser_config: Optional[BrowserConfig] = None,
        crawler_config: Optional[CrawlerRunConfig] = None
    ) -> Union[CrawlResult, AsyncGenerator[CrawlResult, None]]:
        """Execute a crawl operation through the Docker server."""
        # Check server connection first
        if not await self._check_server_connection():
            raise ConnectionError("Cannot proceed with crawl - server is not reachable")

        request_data = self._prepare_request_data(urls, browser_config, crawler_config)
        is_streaming = crawler_config.stream if crawler_config else False
        
        self.logger.info(
            f"Starting crawl for {len(urls)} URLs {'(streaming)' if is_streaming else ''}",
            tag="INIT"
        )
        
        if is_streaming:
            async def result_generator() -> AsyncGenerator[CrawlResult, None]:
                try:
                    async with self._http_client.stream(
                        "POST",
                        f"{self.base_url}/crawl",
                        json=request_data,
                        timeout=None
                    ) as response:
                        response.raise_for_status()
                        async for line in response.aiter_lines():
                            if line.strip():
                                try:
                                    result_dict = json.loads(line)
                                    if "error" in result_dict:
                                        self.logger.error_status(
                                            url=result_dict.get('url', 'unknown'),
                                            error=result_dict['error']
                                        )
                                        continue
                                    
                                    self.logger.url_status(
                                        url=result_dict.get('url', 'unknown'),
                                        success=True,
                                        timing=result_dict.get('timing', 0.0)
                                    )
                                    yield CrawlResult(**result_dict)
                                except json.JSONDecodeError as e:
                                    self.logger.error(f"Failed to parse server response: {e}", tag="ERROR")
                                    continue
                except httpx.StreamError as e:
                    error_msg = f"Stream connection error: {str(e)}"
                    self.logger.error(error_msg, tag="ERROR")
                    raise ConnectionError(error_msg)
                except Exception as e:
                    error_msg = f"Unexpected error during streaming: {str(e)}"
                    self.logger.error(error_msg, tag="ERROR")
                    raise Crawl4aiClientError(error_msg)

            return result_generator()
        
        response = await self._make_request("POST", "/crawl", json=request_data)
        response_data = response.json()
        
        if not response_data.get("success", False):
            error_msg = f"Crawl operation failed: {response_data.get('error', 'Unknown error')}"
            self.logger.error(error_msg, tag="ERROR")
            raise RequestError(error_msg)
        
        results = [CrawlResult(**result_dict) for result_dict in response_data.get("results", [])]
        self.logger.success(f"Crawl completed successfully with {len(results)} results", tag="COMPLETE")
        return results[0] if len(results) == 1 else results

    async def get_schema(self) -> Dict[str, Any]:
        """Retrieve the configuration schemas from the server."""
        self.logger.info("Retrieving schema from server", tag="FETCH")
        response = await self._make_request("GET", "/schema")
        self.logger.success("Schema retrieved successfully", tag="COMPLETE")
        return response.json()

    async def close(self) -> None:
        """Close the HTTP client session."""
        self.logger.info("Closing client connection", tag="COMPLETE")
        await self._http_client.aclose()

    async def __aenter__(self) -> "Crawl4aiDockerClient":
        return self

    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]) -> None:
        await self.close()
from typing import List, Optional, Union, AsyncGenerator, Dict, Any
import httpx
import json
from urllib.parse import urljoin
import asyncio

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
    """Client for interacting with Crawl4AI Docker server with token authentication."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        verify_ssl: bool = True,
        verbose: bool = True,
        log_file: Optional[str] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = AsyncLogger(log_file=log_file, log_level=LogLevel.DEBUG, verbose=verbose)
        self._http_client = httpx.AsyncClient(
            timeout=timeout,
            verify=verify_ssl,
            headers={"Content-Type": "application/json"}
        )
        self._token: Optional[str] = None

    async def authenticate(self, email: str) -> None:
        """Authenticate with the server and store the token."""
        url = urljoin(self.base_url, "/token")
        try:
            self.logger.info(f"Authenticating with email: {email}", tag="AUTH")
            response = await self._http_client.post(url, json={"email": email})
            response.raise_for_status()
            data = response.json()
            self._token = data["access_token"]
            self._http_client.headers["Authorization"] = f"Bearer {self._token}"
            self.logger.success("Authentication successful", tag="AUTH")
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            error_msg = f"Authentication failed: {str(e)}"
            self.logger.error(error_msg, tag="ERROR")
            raise ConnectionError(error_msg)

    async def _check_server(self) -> None:
        """Check if server is reachable, raising an error if not."""
        try:
            await self._http_client.get(urljoin(self.base_url, "/health"))
            self.logger.success(f"Connected to {self.base_url}", tag="READY")
        except httpx.RequestError as e:
            self.logger.error(f"Server unreachable: {str(e)}", tag="ERROR")
            raise ConnectionError(f"Cannot connect to server: {str(e)}")

    def _prepare_request(self, urls: List[str], browser_config: Optional[BrowserConfig] = None, 
                       crawler_config: Optional[CrawlerRunConfig] = None) -> Dict[str, Any]:
        """Prepare request data from configs."""
        if self._token:
            self._http_client.headers["Authorization"] = f"Bearer {self._token}"
        return {
            "urls": urls,
            "browser_config": browser_config.dump() if browser_config else {},
            "crawler_config": crawler_config.dump() if crawler_config else {}
        }

    async def _request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make an HTTP request with error handling."""
        url = urljoin(self.base_url, endpoint)
        try:
            response = await self._http_client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except httpx.TimeoutException as e:
            raise ConnectionError(f"Request timed out: {str(e)}")
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect: {str(e)}")
        except httpx.HTTPStatusError as e:
            error_msg = (e.response.json().get("detail", str(e)) 
                        if "application/json" in e.response.headers.get("content-type", "") 
                        else str(e))
            raise RequestError(f"Server error {e.response.status_code}: {error_msg}")

    async def crawl(
        self,
        urls: List[str],
        browser_config: Optional[BrowserConfig] = None,
        crawler_config: Optional[CrawlerRunConfig] = None
    ) -> Union[CrawlResult, List[CrawlResult], AsyncGenerator[CrawlResult, None]]:
        """Execute a crawl operation."""
        await self._check_server()
        
        data = self._prepare_request(urls, browser_config, crawler_config)
        is_streaming = crawler_config and crawler_config.stream
        
        self.logger.info(f"Crawling {len(urls)} URLs {'(streaming)' if is_streaming else ''}", tag="CRAWL")
        
        if is_streaming:
            async def stream_results() -> AsyncGenerator[CrawlResult, None]:
                async with self._http_client.stream("POST", f"{self.base_url}/crawl/stream", json=data) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line.strip():
                            result = json.loads(line)
                            if "error" in result:
                                self.logger.error_status(url=result.get("url", "unknown"), error=result["error"])
                                continue
                            self.logger.url_status(url=result.get("url", "unknown"), success=True, timing=result.get("timing", 0.0))
                            if result.get("status") == "completed":
                                continue
                            else:
                                yield CrawlResult(**result)
            return stream_results()
        
        response = await self._request("POST", "/crawl", json=data)
        result_data = response.json()
        if not result_data.get("success", False):
            raise RequestError(f"Crawl failed: {result_data.get('msg', 'Unknown error')}")
        
        results = [CrawlResult(**r) for r in result_data.get("results", [])]
        self.logger.success(f"Crawl completed with {len(results)} results", tag="CRAWL")
        return results[0] if len(results) == 1 else results

    async def get_schema(self) -> Dict[str, Any]:
        """Retrieve configuration schemas."""
        response = await self._request("GET", "/schema")
        return response.json()

    async def close(self) -> None:
        """Close the HTTP client session."""
        self.logger.info("Closing client", tag="CLOSE")
        await self._http_client.aclose()

    async def __aenter__(self) -> "Crawl4aiDockerClient":
        return self

    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[Any]) -> None:
        await self.close()


# Example usage
async def main():
    async with Crawl4aiDockerClient(verbose=True) as client:
        await client.authenticate("user@example.com")
        result = await client.crawl(["https://example.com"])
        print(result)
        schema = await client.get_schema()
        print(schema)

if __name__ == "__main__":
    asyncio.run(main())

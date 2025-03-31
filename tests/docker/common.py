from typing import List

import pytest
from _pytest.mark import ParameterSet
from httpx import ASGITransport, AsyncClient

from crawl4ai.docker_client import Crawl4aiDockerClient
from deploy.docker.server import app

TEST_URLS = [
    "example.com",
    "https://www.python.org",
    "https://news.ycombinator.com/news",
    "https://github.com/trending",
]
BASE_URL = "http://localhost:8000"


def async_client() -> AsyncClient:
    """Create an async client for the server.

    This can be used to test the API server without running the server."""
    return AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL)


def docker_client() -> Crawl4aiDockerClient:
    """Crawl4aiDockerClient docker client via local transport.

    This can be used to test the API server without running the server."""
    return Crawl4aiDockerClient(transport=ASGITransport(app=app), verbose=True)


def markdown_params(urls: List[str] = TEST_URLS) -> List[ParameterSet]:
    """Parameters for markdown endpoint tests with different filters"""
    tests = []
    for url in urls:
        for filter_type in ["raw", "fit", "bm25", "llm"]:
            for cache in ["0", "1"]:
                params: dict[str, str] = {"f": filter_type, "c": cache}
                if filter_type in ["bm25", "llm"]:
                    params["q"] = "extract main content"

                tests.append(
                    pytest.param(
                        url,
                        params,
                        id=f"{url} {filter_type}" + (" cached" if cache == "1" else ""),
                    )
                )

    return tests

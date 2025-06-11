from enum import Enum
import pytest
import httpx
import asyncio

class FilterType(str, Enum):
    RAW = "raw"
    FIT = "fit"
    BM25 = "bm25"
    LLM = "llm"

BASE_URL = "http://127.0.0.1:11234"

@pytest.mark.asyncio
async def test_valid_list():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/md", json={
            "urls": "not-a-list",
            "f": FilterType.FIT,
            "q": None,
            "c": "0"
        })
        assert response.status_code == 422

        assert any(
            "Input should be a valid list" in detail['msg']
            for detail in response.json()["detail"]
        )

@pytest.mark.asyncio
async def test_empty_array():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/md", json={
            "urls": [],
            "f": FilterType.FIT,
            "q": None,
            "c": "0"
        })
        assert response.status_code == 422
        assert any(
            "List should have at least 1 item after validation, not 0" in detail['msg']
            for detail in response.json()["detail"]
        )

@pytest.mark.asyncio
async def test_invalid_url():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/md", json={
            "urls": ["https://example.com", "invalid-url"],
            "f": FilterType.FIT,
            "q": None,
            "c": "0"
        })
        assert response.status_code == 400
        assert "URL must be absolute and start with http/https" in response.json()["detail"]

@pytest.mark.asyncio
async def test_valid_url():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/md", json={
            "urls": ["https://example.com"],
            "f": FilterType.FIT,
            "q": None,
            "c": "0"
        })
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 1
        assert "url" in data["results"][0]
        assert "markdown" in data["results"][0]
        assert "server_processing_time_s" in data
        assert "server_memory_delta_mb" in data
        assert "server_peak_memory_mb" in data
        assert data["success"] is True

@pytest.mark.asyncio
async def test_multiple_urls():
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/md", json={
            "urls": ["https://example.com", "https://example.org"],
            "f": FilterType.FIT,
            "q": None,
            "c": "0"
        })
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert all("url" in result and "markdown" in result for result in data["results"])
        assert "server_processing_time_s" in data
        assert "server_memory_delta_mb" in data
        assert "server_peak_memory_mb" in data
        assert data["success"] is True

@pytest.mark.parametrize("filter_type", [
    FilterType.FIT,
    FilterType.RAW,
    FilterType.BM25,
    FilterType.LLM
])
@pytest.mark.asyncio
async def test_filter_types(filter_type):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/md", json={
            "urls": ["https://example.com"],
            "f": filter_type,
            "q": "test query" if filter_type in [FilterType.BM25, FilterType.LLM] else None,
            "c": "0"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["filter"] == filter_type
        assert "results" in data
        assert len(data["results"]) == 1

@pytest.mark.asyncio
async def test_with_cache():
    async with httpx.AsyncClient() as client:
        response1 = await client.post(f"{BASE_URL}/md", json={
            "urls": ["https://example.com"],
            "f": FilterType.FIT,
            "q": None,
            "c": "0"
        })
        assert response1.status_code == 200
        response2 = await client.post(f"{BASE_URL}/md", json={
            "urls": ["https://example.com"],
            "f": FilterType.FIT,
            "q": None,
            "c": "1"
        })
        assert response2.status_code == 200
        time1 = response1.json()["server_processing_time_s"]
        time2 = response2.json()["server_processing_time_s"]
        assert time2 <= time1

@pytest.mark.asyncio
async def test_stress():
    async def make_request():
        async with httpx.AsyncClient() as client:
            return await client.post(f"{BASE_URL}/md", json={
                "urls": ["https://example.com"],
                "f": FilterType.FIT,
                "q": None,
                "c": "0"
            })
    responses = await asyncio.gather(*[make_request() for _ in range(10)])
    assert all(r.status_code == 200 for r in responses)
    assert all(len(r.json()["results"]) == 1 for r in responses)
    assert all(r.json()["success"] for r in responses)

@pytest.mark.asyncio
async def test_stress_multiple_urls():
    async with httpx.AsyncClient(timeout=30.0) as client:
        maxUrls = 100

        urls = ["https://example.com"] * maxUrls
        response = await client.post(f"{BASE_URL}/md", json={
            "urls": urls,
            "f": FilterType.FIT,
            "q": None,
            "c": "0"
        })
    assert response.status_code == 200
    assert len(response.json()["results"]) == maxUrls
    assert response.json()["success"]

@pytest.mark.asyncio
async def test_overload():
    async with httpx.AsyncClient() as client:
        maxUrls = 101
        urls = ["https://example.com"] * maxUrls
        response = await client.post(f"{BASE_URL}/md", json={
            "urls": urls,
            "f": FilterType.FIT,
            "q": None,
            "c": "0"
        })
        
        assert response.status_code == 422
        assert any("List should have at most 100 items after validation, not 101" in detail['msg'] for detail in response.json()["detail"])

if __name__ == "__main__":
    import sys
    import pytest
    # Define arguments for pytest programmatically
    # -v: verbose output
    # -s: show print statements immediately (useful for debugging)
    # __file__: tells pytest to run tests in the current file
    pytest_args = ["-v", "-s", __file__]

    # You can add more pytest arguments here if needed, for example:
    # '-k test_llm_extraction': Run only the LLM test function
    # pytest_args.append("-k test_llm_extraction")

    print(f"Running pytest with args: {pytest_args}")

    # Execute pytest
    exit_code = pytest.main(pytest_args)

    print(f"Pytest finished with exit code: {exit_code}")
    sys.exit(exit_code)
import os
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import AsyncGenerator
from crawl4ai import (
    BrowserConfig,
    CrawlerRunConfig,
    AsyncWebCrawler,
    MemoryAdaptiveDispatcher,
    RateLimiter,
)

from typing import List, Optional
from pydantic import BaseModel

class CrawlRequest(BaseModel):
    urls: List[str]
    browser_config: Optional[dict] = None
    crawler_config: Optional[dict] = None

class CrawlResponse(BaseModel):
    success: bool
    results: List[dict]  

    class Config:
        arbitrary_types_allowed = True

app = FastAPI(title="Crawl4AI API")

async def stream_results(crawler: AsyncWebCrawler, results_gen: AsyncGenerator) -> AsyncGenerator[bytes, None]:
    """Stream results and manage crawler lifecycle"""
    def datetime_handler(obj):
        """Custom handler for datetime objects during JSON serialization"""
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    try:
        async for result in results_gen:
            try:
                # Use dump method for serialization
                result_dict = result.model_dump()
                print(f"Streaming result for URL: {result_dict['url']}, Success: {result_dict['success']}")
                # Use custom JSON encoder with datetime handler
                yield (json.dumps(result_dict, default=datetime_handler) + "\n").encode('utf-8')
            except Exception as e:
                print(f"Error serializing result: {e}")
                error_response = {
                    "error": str(e),
                    "url": getattr(result, 'url', 'unknown')
                }
                yield (json.dumps(error_response, default=datetime_handler) + "\n").encode('utf-8')
    except asyncio.CancelledError:
        print("Client disconnected, cleaning up...")
    finally:
        try:
            await crawler.close()
        except Exception as e:
            print(f"Error closing crawler: {e}")

@app.post("/crawl")
async def crawl(request: CrawlRequest):
    # Load configs using our new utilities
    browser_config = BrowserConfig.load(request.browser_config)
    crawler_config = CrawlerRunConfig.load(request.crawler_config)

    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=95.0,
        rate_limiter=RateLimiter(base_delay=(1.0, 2.0)),
    )

    try:
        if crawler_config.stream:
            crawler = AsyncWebCrawler(config=browser_config)
            await crawler.start()

            results_gen = await crawler.arun_many(
                urls=request.urls,
                config=crawler_config,
                dispatcher=dispatcher
            )

            return StreamingResponse(
                stream_results(crawler, results_gen),
                media_type='application/x-ndjson'
            )
        else:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                results = await crawler.arun_many(
                    urls=request.urls,
                    config=crawler_config,
                    dispatcher=dispatcher
                )
                # Use dump method for each result
                results_dict = [result.model_dump() for result in results]
                return CrawlResponse(success=True, results=results_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema")
async def get_schema():
    """Return config schemas for client validation"""
    return {
        "browser": BrowserConfig.model_json_schema(),
        "crawler": CrawlerRunConfig.model_json_schema()
    }

@app.get("/health")
async def health():
    return {"status": "ok"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
# pyright: ignore
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
from typing import AsyncGenerator
from datetime import datetime
from crawl4ai import (
    BrowserConfig,
    CrawlerRunConfig,
    AsyncWebCrawler,
    MemoryAdaptiveDispatcher,
    RateLimiter,
)
from .models import CrawlRequest, CrawlResponse

class CrawlJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for crawler results"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='ignore')
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        if hasattr(obj, '__dict__'):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        return str(obj)  # Fallback to string representation

def serialize_result(result) -> dict:
    """Safely serialize a crawler result"""
    try:
        # Convert to dict handling special cases
        if hasattr(result, 'model_dump'):
            result_dict = result.model_dump()
        else:
            result_dict = {
                k: v for k, v in result.__dict__.items()
                if not k.startswith('_')
            }

        # Remove known non-serializable objects
        result_dict.pop('ssl_certificate', None)
        result_dict.pop('downloaded_files', None)

        return result_dict
    except Exception as e:
        print(f"Error serializing result: {e}")
        return {"error": str(e), "url": getattr(result, 'url', 'unknown')}

app = FastAPI(title="Crawl4AI API")

async def stream_results(crawler: AsyncWebCrawler, results_gen: AsyncGenerator) -> AsyncGenerator[bytes, None]:
    """Stream results and manage crawler lifecycle"""
    try:
        async for result in results_gen:
            try:
                # Handle serialization of result
                result_dict = serialize_result(result)
                # Remove non-serializable objects
                print(f"Streaming result for URL: {result_dict['url']}, Success: {result_dict['success']}")
                yield (json.dumps(result_dict, cls=CrawlJSONEncoder) + "\n").encode('utf-8')
            except Exception as e:
                # Log error but continue streaming
                print(f"Error serializing result: {e}")
                error_response = {
                    "error": str(e),
                    "url": getattr(result, 'url', 'unknown')
                }
                yield (json.dumps(error_response) + "\n").encode('utf-8')
    except asyncio.CancelledError:
        # Handle client disconnection gracefully
        print("Client disconnected, cleaning up...")
    finally:
        # Ensure crawler cleanup happens in all cases
        try:
            await crawler.close()
        except Exception as e:
            print(f"Error closing crawler: {e}")

@app.post("/crawl")
async def crawl(request: CrawlRequest):
    browser_config, crawler_config = request.get_configs()

    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=75.0,
        rate_limiter=RateLimiter(base_delay=(1.0, 2.0)),
        # monitor=CrawlerMonitor(display_mode=DisplayMode.DETAILED)
    )

    try:
        if crawler_config.stream:
            # For streaming, manage crawler lifecycle manually
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
            # For non-streaming, use context manager
            async with AsyncWebCrawler(config=browser_config) as crawler:
                results = await crawler.arun_many(
                    urls=request.urls,
                    config=crawler_config,
                    dispatcher=dispatcher
                )
                # Handle serialization of results
                results_dict = []
                for result in results:
                    try:
                        result_dict = {
                            k: v for k, v in (result.model_dump() if hasattr(result, 'model_dump')
                                            else result.__dict__).items()
                            if not k.startswith('_')
                        }
                        result_dict.pop('ssl_certificate', None)
                        result_dict.pop('downloaded_files', None)
                        results_dict.append(result_dict)
                    except Exception as e:
                        print(f"Error serializing result: {e}")
                        continue

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


if __name__ == "__main__":
    import uvicorn
    # Run in auto reload mode
    # WARNING:  You must pass the application as an import string to enable 'reload' or 'workers'.
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
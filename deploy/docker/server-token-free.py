import os
import sys
import time
from typing import  List, Optional

sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from redis import asyncio as aioredis
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import StreamingResponse, RedirectResponse
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.responses import PlainTextResponse
from fastapi.responses import JSONResponse
from fastapi.background import BackgroundTasks
from typing import Dict
from fastapi import Query, Path
import os

from utils import (
    FilterType,
    load_config,
    setup_logging
)
from api import (
    handle_markdown_request,
    handle_llm_request,
    handle_llm_qa
)

# Load configuration and setup
config = load_config()
setup_logging(config)

# Initialize Redis
redis = aioredis.from_url(config["redis"].get("uri", "redis://localhost"))

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[config["rate_limiting"]["default_limit"]],
    storage_uri=config["rate_limiting"]["storage_uri"]
)

app = FastAPI(
    title=config["app"]["title"],
    version=config["app"]["version"]
)

# Configure middleware
if config["security"]["enabled"]:
    if config["security"]["https_redirect"]:
        app.add_middleware(HTTPSRedirectMiddleware)
    if config["security"]["trusted_hosts"] and config["security"]["trusted_hosts"] != ["*"]:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=config["security"]["trusted_hosts"]
        )

# Prometheus instrumentation
if config["observability"]["prometheus"]["enabled"]:
    Instrumentator().instrument(app).expose(app)

class CrawlRequest(BaseModel):
    urls: List[str] = Field(
        min_length=1, 
        max_length=100,
        json_schema_extra={
            "items": {"type": "string", "maxLength": 2000, "pattern": "\\S"}
        }
    )
    browser_config: Optional[Dict] = Field(
        default_factory=dict,
        example={"headless": True, "viewport": {"width": 1200}}
    )
    crawler_config: Optional[Dict] = Field(
        default_factory=dict,
        example={"stream": True, "cache_mode": "aggressive"}
    )

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    if config["security"]["enabled"]:
        response.headers.update(config["security"]["headers"])
    return response

@app.get("/md/{url:path}")
@limiter.limit(config["rate_limiting"]["default_limit"])
async def get_markdown(
    request: Request,
    url: str,
    f: FilterType = FilterType.FIT,
    q: Optional[str] = None,
    c: Optional[str] = "0"
):
    """Get markdown from URL with optional filtering."""
    result = await handle_markdown_request(url, f, q, c, config)
    return PlainTextResponse(result)

@app.get("/llm/{url:path}", description="URL should be without http/https prefix")
async def llm_endpoint(
    request: Request,
    url: str = Path(..., description="Domain and path without protocol"),
    q: Optional[str] = Query(None, description="Question to ask about the page content"),
):
    """QA endpoint that uses LLM with crawled content as context."""
    if not q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'q' is required"
        )

    # Ensure URL starts with http/https
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        answer = await handle_llm_qa(url, q, config)
        return JSONResponse({"answer": answer})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# @app.get("/llm/{input:path}")
# @limiter.limit(config["rate_limiting"]["default_limit"])
# async def llm_endpoint(
#     request: Request,
#     background_tasks: BackgroundTasks,
#     input: str,
#     q: Optional[str] = None,
#     s: Optional[str] = None,
#     c: Optional[str] = "0"
# ):
#     """Handle LLM extraction requests."""
#     return await handle_llm_request(
#         redis, background_tasks, request, input, q, s, c, config
#     )


    
@app.get("/schema")
async def get_schema():
    """Endpoint for client-side validation schema."""
    from crawl4ai import BrowserConfig, CrawlerRunConfig
    return {
        "browser": BrowserConfig().dump(),
        "crawler": CrawlerRunConfig().dump()
    }

@app.get(config["observability"]["health_check"]["endpoint"])
async def health():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": time.time()}

@app.get(config["observability"]["prometheus"]["endpoint"])
async def metrics():
    """Prometheus metrics endpoint."""
    return RedirectResponse(url=config["observability"]["prometheus"]["endpoint"])

@app.post("/crawl")
@limiter.limit(config["rate_limiting"]["default_limit"])
async def crawl(request: Request, crawl_request: CrawlRequest):
    """Handle crawl requests."""
    from crawl4ai import (
        AsyncWebCrawler,
        BrowserConfig,
        CrawlerRunConfig,
        MemoryAdaptiveDispatcher,
        RateLimiter
    )
    import asyncio
    import logging

    logger = logging.getLogger(__name__)
    crawler = None

    try:
        if not crawl_request.urls:
            logger.error("Empty URL list received")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one URL required"
            )

        browser_config = BrowserConfig.load(crawl_request.browser_config)
        crawler_config = CrawlerRunConfig.load(crawl_request.crawler_config)

        dispatcher = MemoryAdaptiveDispatcher(
            memory_threshold_percent=config["crawler"]["memory_threshold_percent"],
            rate_limiter=RateLimiter(
                base_delay=tuple(config["crawler"]["rate_limiter"]["base_delay"])
            )
        )

        if crawler_config.stream:
            crawler = AsyncWebCrawler(config=browser_config)
            await crawler.start()

            results_gen = await asyncio.wait_for(
                crawler.arun_many(
                    urls=crawl_request.urls,
                    config=crawler_config,
                    dispatcher=dispatcher
                ),
                timeout=config["crawler"]["timeouts"]["stream_init"]
            )

            from api import stream_results
            return StreamingResponse(
                stream_results(crawler, results_gen),
                media_type='application/x-ndjson',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Stream-Status': 'active'
                }
            )
        else:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                results = await asyncio.wait_for(
                    crawler.arun_many(
                        urls=crawl_request.urls,
                        config=crawler_config,
                        dispatcher=dispatcher
                    ),
                    timeout=config["crawler"]["timeouts"]["batch_process"]
                )
                return JSONResponse({
                    "success": True,
                    "results": [result.model_dump() for result in results]
                })

    except asyncio.TimeoutError as e:
        logger.error(f"Operation timed out: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Processing timeout"
        )
    except Exception as e:
        logger.error(f"Server error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
    finally:
        if crawler:
            try:
                await crawler.close()
            except Exception as e:
                logger.error(f"Final crawler cleanup error: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host=config["app"]["host"],
        port=config["app"]["port"],
        reload=config["app"]["reload"],
        timeout_keep_alive=config["app"]["timeout_keep_alive"]
    )
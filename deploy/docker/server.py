import os
import sys
import time
from typing import Optional, Dict, Any, Annotated
from fastapi import FastAPI, HTTPException, Request, Query, Path, Depends, status
from fastapi.responses import StreamingResponse, RedirectResponse, PlainTextResponse, JSONResponse
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from prometheus_fastapi_instrumentator import Instrumentator
from redis import asyncio as aioredis

from crawl4ai.async_configs import Serialisable

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
from utils import FilterType, load_config, setup_logging, verify_email_domain
from api import (
    handle_markdown_request,
    handle_llm_qa,
    handle_stream_crawl_request,
    handle_crawl_request,
    stream_results,
    CrawlRequest
)
from auth import create_access_token, get_token_dependency, TokenRequest  # Import from auth.py

__version__ = "0.2.6"


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
def setup_security_middleware(app, config):
    sec_config = config.get("security", {})
    if sec_config.get("enabled", False):
        if sec_config.get("https_redirect", False):
            app.add_middleware(HTTPSRedirectMiddleware)
        if sec_config.get("trusted_hosts", []) != ["*"]:
            app.add_middleware(TrustedHostMiddleware, allowed_hosts=sec_config["trusted_hosts"])

setup_security_middleware(app, config)

# Prometheus instrumentation
if config["observability"]["prometheus"]["enabled"]:
    Instrumentator().instrument(app).expose(app)

# Get token dependency based on config
token_dependency = get_token_dependency(config)

# Middleware for security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    if config["security"]["enabled"]:
        response.headers.update(config["security"]["headers"])
    return response

# Token endpoint (always available, but usage depends on config)
@app.post("/token")
async def get_token(request_data: TokenRequest):
    if not verify_email_domain(request_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email domain"
        )
    token = create_access_token({"sub": request_data.email})
    return {"email": request_data.email, "access_token": token, "token_type": "bearer"}

# Endpoints with conditional auth
@app.get("/md/{url:path}")
@limiter.limit(config["rate_limiting"]["default_limit"])
async def get_markdown(
    request: Request,
    url: str,
    f: FilterType = FilterType.FIT,
    q: Optional[str] = None,
    c: str = "0",
    token_data: Optional[Dict] = Depends(token_dependency),
) -> PlainTextResponse:
    result = await handle_markdown_request(url, f, config, q, c)
    return PlainTextResponse(result)

@app.get("/llm/{url:path}", description="URL should be without http/https prefix")
async def llm_endpoint(
    request: Request,
    url: str = Path(...),
    q: Optional[str] = Query(None),
    # TODO: Add schema and cache support as per get_markdown
    token_data: Optional[Dict] = Depends(token_dependency),
) -> JSONResponse:
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    try:
        answer = await handle_llm_qa(url, q, config)
        return JSONResponse({"answer": answer})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema")
async def get_schema() -> dict[str, Serialisable]:
    from crawl4ai import BrowserConfig, CrawlerRunConfig
    return {"browser": BrowserConfig().dump(), "crawler": CrawlerRunConfig().dump()}

@app.get(config["observability"]["health_check"]["endpoint"])
async def health() -> dict[str, Any]:
    return {"status": "ok", "timestamp": time.time(), "version": __version__}

@app.get(config["observability"]["prometheus"]["endpoint"])
async def metrics() -> RedirectResponse:
    return RedirectResponse(url=config["observability"]["prometheus"]["endpoint"])

@app.post("/crawl")
@limiter.limit(config["rate_limiting"]["default_limit"])
async def crawl(
    request: Request,
    crawl_request: Annotated[CrawlRequest, Depends(CrawlRequest)],
    token_data: Optional[Dict] = Depends(token_dependency),
) -> JSONResponse:
    if not crawl_request.urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="At least one URL required"
        )

    if crawl_request.crawler_config.stream:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Streaming mode not allowed for this endpoint. Use /crawl/stream instead.",
        )

    results = await handle_crawl_request(
        crawl_request=crawl_request,
        config=config,
    )

    return JSONResponse(results)


@app.post("/crawl/stream")
@limiter.limit(config["rate_limiting"]["default_limit"])
async def crawl_stream(
    request: Request,
    crawl_request: Annotated[CrawlRequest, Depends(CrawlRequest)],
    token_data: Optional[Dict] = Depends(token_dependency),
):
    if not crawl_request.urls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="At least one URL required"
        )

    if not crawl_request.crawler_config.stream:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Streaming mode must be set for this endpoint. Use /crawl instead {crawl_request.crawler_config}.",
        )

    crawler, results_gen = await handle_stream_crawl_request(
        crawl_request=crawl_request,
        config=config,
    )

    return StreamingResponse(
        stream_results(crawler, results_gen),
        media_type='application/x-ndjson',
        headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'X-Stream-Status': 'active'}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "server:app",
        host=config["app"]["host"],
        port=config["app"]["port"],
        reload=config["app"]["reload"],
        timeout_keep_alive=config["app"]["timeout_keep_alive"]
    )
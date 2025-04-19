# Import from auth.py
from auth import create_access_token, get_token_dependency, TokenRequest
from api import (
    handle_markdown_request,
    handle_llm_qa,
    handle_stream_crawl_request,
    handle_crawl_request,
    stream_results,
    _get_memory_mb
)
from utils import FilterType, load_config, setup_logging, verify_email_domain
import os
import sys
import time
from typing import List, Optional, Dict, AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Query, Path, Depends, status
from fastapi.responses import StreamingResponse, RedirectResponse, PlainTextResponse, JSONResponse
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from prometheus_fastapi_instrumentator import Instrumentator
from redis import asyncio as aioredis
from crawl4ai import (
    BrowserConfig,
    CrawlerRunConfig,
    AsyncLogger
)

from crawler_manager import (
    CrawlerManager,
    CrawlerManagerConfig,
    PoolTimeoutError,
    NoHealthyCrawlerError
)
import json


sys.path.append(os.path.dirname(os.path.realpath(__file__)))

__version__ = "0.2.6"


class CrawlRequest(BaseModel):
    urls: List[str] = Field(min_length=1, max_length=100)
    browser_config: Optional[Dict] = Field(default_factory=dict)
    crawler_config: Optional[Dict] = Field(default_factory=dict)


# Load configuration and setup
config = load_config()
setup_logging(config)
logger = AsyncLogger(
    log_file=config["logging"].get("log_file", "app.log"),
    verbose=config["logging"].get("verbose", False),
    tag_width=10,
)

# Initialize Redis
redis = aioredis.from_url(config["redis"].get("uri", "redis://localhost"))

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[config["rate_limiting"]["default_limit"]],
    storage_uri=config["rate_limiting"]["storage_uri"]
)

# --- Initialize Manager (will be done in lifespan) ---
# Load manager config from the main config
manager_config_dict = config.get("crawler_pool", {})
# Use Pydantic to parse and validate
manager_config = CrawlerManagerConfig(**manager_config_dict)
crawler_manager = CrawlerManager(config=manager_config, logger=logger)

# --- FastAPI App and Lifespan ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up the server...")
    if manager_config.enabled:
        logger.info("Initializing Crawler Manager...")
        await crawler_manager.initialize()
        app.state.crawler_manager = crawler_manager  # Store manager in app state
        logger.info("Crawler Manager is enabled.")
    else:
        logger.warning("Crawler Manager is disabled.")
        app.state.crawler_manager = None  # Indicate disabled state

    yield  # Server runs here

    # Shutdown
    logger.info("Shutting down server...")
    if app.state.crawler_manager:
        logger.info("Shutting down Crawler Manager...")
        await app.state.crawler_manager.shutdown()
        logger.info("Crawler Manager shut down.")
    logger.info("Server shut down.")

app = FastAPI(
    title=config["app"]["title"],
    version=config["app"]["version"],
    lifespan=lifespan,
)

# Configure middleware
def setup_security_middleware(app, config):
    sec_config = config.get("security", {})
    if sec_config.get("enabled", False):
        if sec_config.get("https_redirect", False):
            app.add_middleware(HTTPSRedirectMiddleware)
        if sec_config.get("trusted_hosts", []) != ["*"]:
            app.add_middleware(TrustedHostMiddleware,
                               allowed_hosts=sec_config["trusted_hosts"])


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


async def get_manager() -> CrawlerManager:
    # Ensure manager exists and is enabled before yielding
    if not hasattr(app.state, 'crawler_manager') or app.state.crawler_manager is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Crawler service is disabled or not initialized"
        )
    if not app.state.crawler_manager.is_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Crawler service is currently disabled"
        )
    return app.state.crawler_manager

# Token endpoint (always available, but usage depends on config)


@app.post("/token")
async def get_token(request_data: TokenRequest):
    if not verify_email_domain(request_data.email):
        raise HTTPException(status_code=400, detail="Invalid email domain")
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
    c: Optional[str] = "0",
    token_data: Optional[Dict] = Depends(token_dependency)
):
    result = await handle_markdown_request(url, f, q, c, config)
    return PlainTextResponse(result)


@app.get("/llm/{url:path}", description="URL should be without http/https prefix")
async def llm_endpoint(
    request: Request,
    url: str = Path(...),
    q: str = Query(...),
    token_data: Optional[Dict] = Depends(token_dependency)
):
    try:
        answer = await handle_llm_qa(url, q, config)
        return JSONResponse({"answer": answer})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schema")
async def get_schema():
    from crawl4ai import BrowserConfig, CrawlerRunConfig
    return {"browser": BrowserConfig().dump(), "crawler": CrawlerRunConfig().dump()}


@app.get(config["observability"]["health_check"]["endpoint"])
async def health():
    return {"status": "ok", "timestamp": time.time(), "version": __version__}


@app.get(config["observability"]["prometheus"]["endpoint"])
async def metrics():
    return RedirectResponse(url=config["observability"]["prometheus"]["endpoint"])


@app.get("/browswers")
# Optional dependency
async def health(manager: Optional[CrawlerManager] = Depends(get_manager, use_cache=False)):
    base_status = {"status": "ok", "timestamp": time.time(),
                   "version": __version__}
    if manager:
        try:
            manager_status = await manager.get_status()
            base_status["crawler_manager"] = manager_status
        except Exception as e:
            base_status["crawler_manager"] = {
                "status": "error", "detail": str(e)}
    else:
        base_status["crawler_manager"] = {"status": "disabled"}
    return base_status


@app.post("/crawl")
@limiter.limit(config["rate_limiting"]["default_limit"])
async def crawl(
    request: Request,
    crawl_request: CrawlRequest,
    manager: CrawlerManager = Depends(get_manager),  # Use dependency
    token_data: Optional[Dict] = Depends(token_dependency)  # Keep auth
):
    if not crawl_request.urls:
        raise HTTPException(
            status_code=400, detail="At least one URL required")

    try:
        # Use the manager's context to get a crawler instance
        async with manager.get_crawler() as active_crawler:
            # Call the actual handler from api.py, passing the acquired crawler
            results_dict = await handle_crawl_request(
                crawler=active_crawler,  # Pass the live crawler instance
                urls=crawl_request.urls,
                # Pass user-provided configs, these might override pool defaults if needed
                # Or the manager/handler could decide how to merge them
                browser_config=crawl_request.browser_config or {},  # Ensure dict
                crawler_config=crawl_request.crawler_config or {},  # Ensure dict
                config=config  # Pass the global server config
            )
            return JSONResponse(results_dict)

    except PoolTimeoutError as e:
        logger.warning(f"Request rejected due to pool timeout: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,  # Or 429
            detail=f"Crawler resources busy. Please try again later. Timeout: {e}"
        )
    except NoHealthyCrawlerError as e:
        logger.error(f"Request failed as no healthy crawler available: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Crawler service temporarily unavailable: {e}"
        )
    except HTTPException:  # Re-raise HTTP exceptions from handler
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error during batch crawl processing: {e}", exc_info=True)
        # Return generic error, details might be logged by handle_crawl_request
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )


@app.post("/crawl/stream")
@limiter.limit(config["rate_limiting"]["default_limit"])
async def crawl_stream(
    request: Request,
    crawl_request: CrawlRequest,
    manager: CrawlerManager = Depends(get_manager),
    token_data: Optional[Dict] = Depends(token_dependency)
):
    if not crawl_request.urls:
        raise HTTPException(
            status_code=400, detail="At least one URL required")

    try:
        # THIS IS A BIT WORK OF ART RATHER THAN ENGINEERING
        # Acquire the crawler context from the manager
        # IMPORTANT: The context needs to be active for the *duration* of the stream
        # This structure might be tricky with FastAPI's StreamingResponse which consumes
        # the generator *after* the endpoint function returns.

        # --- Option A: Acquire crawler, pass to handler, handler yields ---
        # (Requires handler NOT to be async generator itself, but return one)
        # async with manager.get_crawler() as active_crawler:
        #     # Handler returns the generator
        #     _, results_gen = await handle_stream_crawl_request(
        #         crawler=active_crawler,
        #         urls=crawl_request.urls,
        #         browser_config=crawl_request.browser_config or {},
        #         crawler_config=crawl_request.crawler_config or {},
        #         config=config
        #     )
        #     # PROBLEM: `active_crawler` context exits before StreamingResponse uses results_gen
        #     # This releases the semaphore too early.

        # --- Option B: Pass manager to handler, handler uses context internally ---
        # (Requires modifying handle_stream_crawl_request signature/logic)
        # This seems cleaner. Let's assume api.py is adapted for this.
        # We need a way for the generator yielded by stream_results to know when
        # to release the semaphore.

        # --- Option C: Create a wrapper generator that handles context ---
        async def stream_wrapper(manager: CrawlerManager, crawl_request: CrawlRequest, config: dict) -> AsyncGenerator[bytes, None]:
            active_crawler = None
            try:
                async with manager.get_crawler() as acquired_crawler:
                    active_crawler = acquired_crawler  # Keep reference for cleanup
                    # Call the handler which returns the raw result generator
                    _crawler_ref, results_gen = await handle_stream_crawl_request(
                        crawler=acquired_crawler,
                        urls=crawl_request.urls,
                        browser_config=crawl_request.browser_config or {},
                        crawler_config=crawl_request.crawler_config or {},
                        config=config
                    )
                    # Use the stream_results utility to format and yield
                    async for data_bytes in stream_results(_crawler_ref, results_gen):
                        yield data_bytes
            except (PoolTimeoutError, NoHealthyCrawlerError) as e:
                # Yield a final error message in the stream
                error_payload = {"status": "error", "detail": str(e)}
                yield (json.dumps(error_payload) + "\n").encode('utf-8')
                logger.warning(f"Stream request failed: {e}")
                # Re-raise might be better if StreamingResponse handles it? Test needed.
            except HTTPException as e:  # Catch HTTP exceptions from handler setup
                error_payload = {"status": "error",
                                 "detail": e.detail, "status_code": e.status_code}
                yield (json.dumps(error_payload) + "\n").encode('utf-8')
                logger.warning(
                    f"Stream request failed with HTTPException: {e.detail}")
            except Exception as e:
                error_payload = {"status": "error",
                                 "detail": f"Unexpected stream error: {e}"}
                yield (json.dumps(error_payload) + "\n").encode('utf-8')
                logger.error(
                    f"Unexpected error during stream processing: {e}", exc_info=True)
            # finally:
                # Ensure crawler cleanup if stream_results doesn't handle it?
                # stream_results *should* call crawler.close(), but only on the
                # instance it received. If we pass the *manager* instead, this gets complex.
                # Let's stick to passing the acquired_crawler and rely on stream_results.

        # Create the generator using the wrapper
        streaming_generator = stream_wrapper(manager, crawl_request, config)

        return StreamingResponse(
            streaming_generator,  # Use the wrapper
            media_type='application/x-ndjson',
            headers={'Cache-Control': 'no-cache',
                     'Connection': 'keep-alive', 'X-Stream-Status': 'active'}
        )

    except (PoolTimeoutError, NoHealthyCrawlerError) as e:
        # These might occur if get_crawler fails *before* stream starts
        # Or if the wrapper re-raises them.
        logger.warning(f"Stream request rejected before starting: {e}")
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE  # Or 429 for timeout
        # Don't raise HTTPException here, let the wrapper yield the error message.
        # If we want to return a non-200 initial status, need more complex handling.
        # Return an *empty* stream with error headers? Or just let wrapper yield error.

        async def _error_stream(e):
            error_payload = {"status": "error", "detail": str(e)}
            yield (json.dumps(error_payload) + "\n").encode('utf-8')
        return StreamingResponse(_error_stream(e), status_code=status_code, media_type='application/x-ndjson')

    except HTTPException:  # Re-raise HTTP exceptions from setup
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error setting up stream crawl: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred setting up the stream: {e}"
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

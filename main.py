import os
import importlib
import asyncio
from functools import lru_cache
import logging
logging.basicConfig(level=logging.DEBUG)

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware  
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import FileResponse
from fastapi.responses import RedirectResponse

from pydantic import BaseModel, HttpUrl
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

from crawl4ai.web_crawler import WebCrawler
from crawl4ai.database import get_total_count, clear_db

import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# load .env file
from dotenv import load_dotenv
load_dotenv()

# Configuration
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
MAX_CONCURRENT_REQUESTS = 10  # Adjust this to change the maximum concurrent requests
current_requests = 0
lock = asyncio.Lock()

app = FastAPI()

# Initialize rate limiter
def rate_limit_key_func(request: Request):
    access_token = request.headers.get("access-token")
    if access_token == os.environ.get('ACCESS_TOKEN'):
        return None
    return get_remote_address(request)

limiter = Limiter(key_func=rate_limit_key_func)
app.state.limiter = limiter

# Dictionary to store last request times for each client
last_request_times = {}
last_rate_limit = {}


def get_rate_limit():
    limit = os.environ.get('ACCESS_PER_MIN', "5")
    return f"{limit}/minute"

# Custom rate limit exceeded handler
async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    if request.client.host not in last_rate_limit or time.time() - last_rate_limit[request.client.host] > 60:
        last_rate_limit[request.client.host] = time.time()
    retry_after = 60 - (time.time() - last_rate_limit[request.client.host])
    reset_at = time.time() + retry_after
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded",
            "limit": str(exc.limit.limit),
            "retry_after": retry_after,
            'reset_at': reset_at,
            "message": f"You have exceeded the rate limit of {exc.limit.limit}."
        }
    )
    
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)


# Middleware for token-based bypass and per-request limit
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        SPAN = int(os.environ.get('ACCESS_TIME_SPAN', 10))
        access_token = request.headers.get("access-token")
        if access_token == os.environ.get('ACCESS_TOKEN'):
            return await call_next(request)
        
        path = request.url.path
        if path in ["/crawl", "/old"]:
            client_ip = request.client.host
            current_time = time.time()
            
            # Check time since last request
            if client_ip in last_request_times:
                time_since_last_request = current_time - last_request_times[client_ip]
                if time_since_last_request < SPAN:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": "Too many requests",
                            "message": "Rate limit exceeded. Please wait 10 seconds between requests.",
                            "retry_after": max(0, SPAN - time_since_last_request),
                            "reset_at": current_time + max(0, SPAN - time_since_last_request),
                        }
                    )
            
            last_request_times[client_ip] = current_time

        return await call_next(request)

app.add_middleware(RateLimitMiddleware)

# CORS configuration
origins = ["*"]  # Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of origins that are allowed to make requests
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Mount the pages directory as a static directory
app.mount("/pages", StaticFiles(directory=__location__ + "/pages"), name="pages")
app.mount("/mkdocs", StaticFiles(directory="site", html=True), name="mkdocs")
site_templates = Jinja2Templates(directory=__location__ + "/site")
templates = Jinja2Templates(directory=__location__ + "/pages")

@lru_cache()
def get_crawler():
    # Initialize and return a WebCrawler instance
    crawler = WebCrawler(verbose = True)
    crawler.warmup()
    return crawler

class CrawlRequest(BaseModel):
    urls: List[str]
    include_raw_html: Optional[bool] = False
    bypass_cache: bool = False
    extract_blocks: bool = True
    word_count_threshold: Optional[int] = 5
    extraction_strategy: Optional[str] = "NoExtractionStrategy"
    extraction_strategy_args: Optional[dict] = {}
    chunking_strategy: Optional[str] = "RegexChunking"
    chunking_strategy_args: Optional[dict] = {}
    css_selector: Optional[str] = None
    screenshot: Optional[bool] = False
    user_agent: Optional[str] = None
    verbose: Optional[bool] = True

@app.get("/")
def read_root():
    return RedirectResponse(url="/mkdocs")

@app.get("/old", response_class=HTMLResponse)
@limiter.limit(get_rate_limit())
async def read_index(request: Request):
    partials_dir = os.path.join(__location__, "pages", "partial")
    partials = {}

    for filename in os.listdir(partials_dir):
        if filename.endswith(".html"):
            with open(os.path.join(partials_dir, filename), "r", encoding="utf8") as file:
                partials[filename[:-5]] = file.read()

    return templates.TemplateResponse("index.html", {"request": request, **partials})

@app.get("/total-count")
async def get_total_url_count():
    count = get_total_count()
    return JSONResponse(content={"count": count})

@app.get("/clear-db")
async def clear_database():
    # clear_db()
    return JSONResponse(content={"message": "Database cleared."})

def import_strategy(module_name: str, class_name: str, *args, **kwargs):
    try:
        module = importlib.import_module(module_name)
        strategy_class = getattr(module, class_name)
        return strategy_class(*args, **kwargs)
    except ImportError:
        print("ImportError: Module not found.")
        raise HTTPException(status_code=400, detail=f"Module {module_name} not found.")
    except AttributeError:
        print("AttributeError: Class not found.")
        raise HTTPException(status_code=400, detail=f"Class {class_name} not found in {module_name}.")

@app.post("/crawl")
@limiter.limit(get_rate_limit())
async def crawl_urls(crawl_request: CrawlRequest, request: Request):
    logging.debug(f"[LOG] Crawl request for URL: {crawl_request.urls}")
    global current_requests
    async with lock:
        if current_requests >= MAX_CONCURRENT_REQUESTS:
            raise HTTPException(status_code=429, detail="Too many requests - please try again later.")
        current_requests += 1

    try:
        logging.debug("[LOG] Loading extraction and chunking strategies...")
        crawl_request.extraction_strategy_args['verbose'] = True
        crawl_request.chunking_strategy_args['verbose'] = True
        
        extraction_strategy = import_strategy("crawl4ai.extraction_strategy", crawl_request.extraction_strategy, **crawl_request.extraction_strategy_args)
        chunking_strategy = import_strategy("crawl4ai.chunking_strategy", crawl_request.chunking_strategy, **crawl_request.chunking_strategy_args)

        # Use ThreadPoolExecutor to run the synchronous WebCrawler in async manner
        logging.debug("[LOG] Running the WebCrawler...")
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            futures = [
                loop.run_in_executor(
                    executor, 
                    get_crawler().run,
                    str(url),
                    crawl_request.word_count_threshold,
                    extraction_strategy,
                    chunking_strategy,
                    crawl_request.bypass_cache,
                    crawl_request.css_selector,
                    crawl_request.screenshot,
                    crawl_request.user_agent,
                    crawl_request.verbose
                )
                for url in crawl_request.urls
            ]
            results = await asyncio.gather(*futures)

        # if include_raw_html is False, remove the raw HTML content from the results
        if not crawl_request.include_raw_html:
            for result in results:
                result.html = None

        return {"results": [result.model_dump() for result in results]}
    finally:
        async with lock:
            current_requests -= 1
            
@app.get("/strategies/extraction", response_class=JSONResponse)
async def get_extraction_strategies():
    with open(f"{__location__}/docs/extraction_strategies.json", "r") as file:
        return JSONResponse(content=file.read())

@app.get("/strategies/chunking", response_class=JSONResponse)
async def get_chunking_strategies():
    with open(f"{__location__}/docs/chunking_strategies.json", "r") as file:
        return JSONResponse(content=file.read())


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)

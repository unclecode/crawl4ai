from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from crawler.web_crawler import WebCrawler
from crawler.models import UrlModel
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import chromedriver_autoinstaller
from functools import lru_cache
from crawler.database import get_total_count
import os
import uuid

# Task management
tasks = {}

# Configuration
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
MAX_CONCURRENT_REQUESTS = 10  # Adjust this to change the maximum concurrent requests
current_requests = 0
lock = asyncio.Lock()

app = FastAPI()

# Mount the pages directory as a static directory
app.mount("/pages", StaticFiles(directory=__location__ + "/pages"), name="pages")


chromedriver_autoinstaller.install()  # Ensure chromedriver is installed

class UrlsInput(BaseModel):
    urls: List[HttpUrl]
    provider_model: str
    api_token: str
    include_raw_html: Optional[bool] = False
    forced: bool = False
    extract_blocks: bool = True
    word_count_threshold: Optional[int] = 5

@lru_cache()
def get_crawler():
    # Initialize and return a WebCrawler instance
    return WebCrawler(db_path='crawler_data.db')

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open(f"{__location__}/pages/index.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/total-count")
async def get_total_url_count():
    count = get_total_count(db_path='crawler_data.db')
    return JSONResponse(content={"count": count})

@app.post("/crawl")
async def crawl_urls(urls_input: UrlsInput, request: Request):
    global current_requests
    # Raise error if api_token is not provided
    if not urls_input.api_token:
        raise HTTPException(status_code=401, detail="API token is required.")
    async with lock:
        if current_requests >= MAX_CONCURRENT_REQUESTS:
            raise HTTPException(status_code=429, detail="Too many requests - please try again later.")
        current_requests += 1

    try:
        # Prepare URL models for crawling
        url_models = [UrlModel(url=url, forced=urls_input.forced) for url in urls_input.urls]

        # Use ThreadPoolExecutor to run the synchronous WebCrawler in async manner
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_event_loop()
            futures = [
                loop.run_in_executor(executor, get_crawler().fetch_page, url_model, urls_input.provider_model, urls_input.api_token, urls_input.extract_blocks, urls_input.word_count_threshold)
                for url_model in url_models
            ]
            results = await asyncio.gather(*futures)

        # if include_raw_html is False, remove the raw HTML content from the results
        if not urls_input.include_raw_html:
            for result in results:
                result.html = None
        
        return {"results": [result.dict() for result in results]}
    finally:
        async with lock:
            current_requests -= 1

@app.post("/crawl_async")
async def crawl_urls(urls_input: UrlsInput, request: Request):
    global current_requests
    if not urls_input.api_token:
        raise HTTPException(status_code=401, detail="API token is required.")

    async with lock:
        if current_requests >= MAX_CONCURRENT_REQUESTS:
            raise HTTPException(status_code=429, detail="Too many requests - please try again later.")
        current_requests += 1

    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "results": None}

    try:
        url_models = [UrlModel(url=url, forced=urls_input.forced) for url in urls_input.urls]

        loop = asyncio.get_running_loop()
        loop.create_task(
            process_crawl_task(url_models, urls_input.provider_model, urls_input.api_token, task_id, urls_input.extract_blocks)
        )
        return {"task_id": task_id}
    finally:
        async with lock:
            current_requests -= 1

async def process_crawl_task(url_models, provider, api_token, task_id, extract_blocks_flag):
    try:
        with ThreadPoolExecutor() as executor:
            loop = asyncio.get_running_loop()
            futures = [
                loop.run_in_executor(executor, get_crawler().fetch_page, url_model, provider, api_token, extract_blocks_flag)
                for url_model in url_models
            ]
            results = await asyncio.gather(*futures)

        tasks[task_id] = {"status": "done", "results": results}
    except Exception as e:
        tasks[task_id] = {"status": "failed", "error": str(e)}

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task['status'] == 'done':
        return {
            "status": task['status'],
            "results": [result.dict() for result in task['results']]
        }
    elif task['status'] == 'failed':
        return {
            "status": task['status'],
            "error": task['error']
        }
    else:
        return {"status": task['status']}
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
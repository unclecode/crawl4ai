import uuid
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException
from schemas import AdaptiveConfigPayload, AdaptiveCrawlRequest, AdaptiveJobStatus

from crawl4ai import AsyncWebCrawler
from crawl4ai.adaptive_crawler import AdaptiveConfig, AdaptiveCrawler
from crawl4ai.utils import get_error_context

# --- In-memory storage for job statuses. For production, use Redis or a database. ---
ADAPTIVE_JOBS: Dict[str, Dict[str, Any]] = {}

# --- APIRouter for Adaptive Crawling Endpoints ---
router = APIRouter(
    prefix="/adaptive/digest",
    tags=["Adaptive Crawling"],
)

# --- Background Worker Function ---


async def run_adaptive_digest(task_id: str, request: AdaptiveCrawlRequest):
    """The actual async worker that performs the adaptive crawl."""
    try:
        # Update job status to RUNNING
        ADAPTIVE_JOBS[task_id]["status"] = "RUNNING"

        # Create AdaptiveConfig from payload or use default
        if request.config:
            adaptive_config = AdaptiveConfig(**request.config.model_dump())
        else:
            adaptive_config = AdaptiveConfig()

        # The adaptive crawler needs an instance of the web crawler
        async with AsyncWebCrawler() as crawler:
            adaptive_crawler = AdaptiveCrawler(crawler, config=adaptive_config)

            # This is the long-running operation
            final_state = await adaptive_crawler.digest(
                start_url=request.start_url, query=request.query
            )

            # Process the final state into a clean result
            result_data = {
                "confidence": final_state.metrics.get("confidence", 0.0),
                "is_sufficient": adaptive_crawler.is_sufficient,
                "coverage_stats": adaptive_crawler.coverage_stats,
                "relevant_content": adaptive_crawler.get_relevant_content(top_k=5),
            }

            # Update job with the final result
            ADAPTIVE_JOBS[task_id].update(
                {
                    "status": "COMPLETED",
                    "result": result_data,
                    "metrics": final_state.metrics,
                }
            )

    except Exception as e:
        # On failure, update the job with an error message
        import sys

        error_context = get_error_context(sys.exc_info())
        error_message = f"Adaptive crawl failed: {str(e)}\nContext: {error_context}"

        ADAPTIVE_JOBS[task_id].update({"status": "FAILED", "error": error_message})


# --- API Endpoints ---


@router.post("/job",
    summary="Submit Adaptive Crawl Job",
    description="Start a long-running adaptive crawling job that intelligently discovers relevant content.",
    response_description="Job ID for status polling",
    response_model=AdaptiveJobStatus,
    status_code=202
)
async def submit_adaptive_digest_job(
    request: AdaptiveCrawlRequest,
    background_tasks: BackgroundTasks,
):
    """
    Submit a new adaptive crawling job.
    
    This endpoint starts an intelligent, long-running crawl that automatically
    discovers and extracts relevant content based on your query. Returns
    immediately with a task ID for polling.
    
    **Request Body:**
    ```json
    {
        "start_url": "https://example.com",
        "query": "Find all product documentation",
        "config": {
            "max_depth": 3,
            "max_pages": 50,
            "confidence_threshold": 0.7,
            "timeout": 300
        }
    }
    ```
    
    **Parameters:**
    - `start_url`: Starting URL for the crawl
    - `query`: Natural language query describing what to find
    - `config`: Optional adaptive configuration (max_depth, max_pages, etc.)
    
    **Response:**
    ```json
    {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "PENDING",
        "metrics": null,
        "result": null,
        "error": null
    }
    ```
    
    **Usage:**
    ```python
    # Submit job
    response = requests.post(
        "http://localhost:11235/adaptive/digest/job",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "start_url": "https://example.com",
            "query": "Find all API documentation"
        }
    )
    task_id = response.json()["task_id"]
    
    # Poll for results
    while True:
        status_response = requests.get(
            f"http://localhost:11235/adaptive/digest/job/{task_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        status = status_response.json()
        if status["status"] in ["COMPLETED", "FAILED"]:
            print(status["result"])
            break
        time.sleep(2)
    ```
    
    **Notes:**
    - Job runs in background, returns immediately
    - Use task_id to poll status with GET /adaptive/digest/job/{task_id}
    - Adaptive crawler intelligently follows links based on relevance
    - Automatically stops when sufficient content found
    - Returns HTTP 202 Accepted
    """

    print("Received adaptive crawl request:", request)
    task_id = str(uuid.uuid4())

    # Initialize the job in our in-memory store
    ADAPTIVE_JOBS[task_id] = {
        "task_id": task_id,
        "status": "PENDING",
        "metrics": None,
        "result": None,
        "error": None,
    }

    # Add the long-running task to the background
    background_tasks.add_task(run_adaptive_digest, task_id, request)

    return ADAPTIVE_JOBS[task_id]


@router.get("/job/{task_id}",
    summary="Get Adaptive Job Status",
    description="Poll the status and results of an adaptive crawling job.",
    response_description="Job status, metrics, and results",
    response_model=AdaptiveJobStatus
)
async def get_adaptive_digest_status(task_id: str):
    """
    Get the status and result of an adaptive crawling job.
    
    Poll this endpoint with the task_id returned from the submission endpoint
    until the status is 'COMPLETED' or 'FAILED'.
    
    **Parameters:**
    - `task_id`: Job ID from POST /adaptive/digest/job
    
    **Response (Running):**
    ```json
    {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "RUNNING",
        "metrics": {
            "confidence": 0.45,
            "pages_crawled": 15,
            "relevant_pages": 8
        },
        "result": null,
        "error": null
    }
    ```
    
    **Response (Completed):**
    ```json
    {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "COMPLETED",
        "metrics": {
            "confidence": 0.85,
            "pages_crawled": 42,
            "relevant_pages": 28
        },
        "result": {
            "confidence": 0.85,
            "is_sufficient": true,
            "coverage_stats": {...},
            "relevant_content": [...]
        },
        "error": null
    }
    ```
    
    **Status Values:**
    - `PENDING`: Job queued, not started yet
    - `RUNNING`: Job actively crawling
    - `COMPLETED`: Job finished successfully
    - `FAILED`: Job encountered an error
    
    **Usage:**
    ```python
    import time
    
    # Poll until complete
    while True:
        response = requests.get(
            f"http://localhost:11235/adaptive/digest/job/{task_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        job = response.json()
        
        print(f"Status: {job['status']}")
        if job['status'] == 'RUNNING':
            print(f"Progress: {job['metrics']['pages_crawled']} pages")
        elif job['status'] == 'COMPLETED':
            print(f"Found {len(job['result']['relevant_content'])} relevant items")
            break
        elif job['status'] == 'FAILED':
            print(f"Error: {job['error']}")
            break
        
        time.sleep(2)
    ```
    
    **Notes:**
    - Poll every 1-5 seconds
    - Metrics updated in real-time while running
    - Returns 404 if task_id not found
    - Results include top relevant content and statistics
    """
    job = ADAPTIVE_JOBS.get(task_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # If the job is running, update the metrics from the live state
    if job["status"] == "RUNNING" and job.get("live_state"):
        job["metrics"] = job["live_state"].metrics

    return job

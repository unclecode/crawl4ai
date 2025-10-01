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


@router.post("/job", response_model=AdaptiveJobStatus, status_code=202)
async def submit_adaptive_digest_job(
    request: AdaptiveCrawlRequest,
    background_tasks: BackgroundTasks,
):
    """
    Submit a new adaptive crawling job.

    This endpoint starts a long-running adaptive crawl in the background and
    immediately returns a task ID for polling the job's status.
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


@router.get("/job/{task_id}", response_model=AdaptiveJobStatus)
async def get_adaptive_digest_status(task_id: str):
    """
    Get the status and result of an adaptive crawling job.

    Poll this endpoint with the `task_id` returned from the submission
    endpoint until the status is 'COMPLETED' or 'FAILED'.
    """
    job = ADAPTIVE_JOBS.get(task_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # If the job is running, update the metrics from the live state
    if job["status"] == "RUNNING" and job.get("live_state"):
        job["metrics"] = job["live_state"].metrics

    return job

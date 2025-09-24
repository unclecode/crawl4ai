### Task 17: Add comprehensive logging and monitoring

**Description:**

This task involves setting up structured, context-rich logging.

17. Add comprehensive logging and monitoring
- Set up structured logging with JSON format for Railway
- Implement log correlation with request and job IDs
- Add performance timing logs for each processing step
- Create log filtering and error aggregation
- Implement log retention and cleanup policies
- Write tests for logging functionality and log format validation
Requirements: 8.4, 10.3

**Logging Strategy:**
- Configure structured logging (JSON format) for Railway.
- All log entries should include a context object.

**Log Context (`app/core/logging_config.py`):**
Define a structure or use a library to ensure logs contain this context:
```python
class LogContext:
    request_id: str
    job_id: Optional[str]
    user_tier: Optional[str]
    url: Optional[str]
    operation: str # e.g., "crawl_request", "process_job"
    duration_ms: Optional[int]
```


**Globs:**
```
app/core/logging_config.py
app/main.py
app/worker.py
app/middleware/logging_middleware.py
```

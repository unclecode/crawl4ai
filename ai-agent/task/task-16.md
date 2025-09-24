### Task 16: Implement comprehensive error handling

**Description:**

This task is to create a centralized and robust error handling system.

- [ ] 16. Implement comprehensive error handling

  - Create custom exception classes for different error types
  - Implement global exception handler with proper error responses
  - Add structured logging with context (request_id, job_id, user_tier)
  - Create error categorization and retry decision logic
  - Implement error metrics and alerting thresholds
  - Write tests for error scenarios and recovery mechanisms
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 10.3_

**Error Classification:**
The system should distinguish between:

1. **Client Errors (4xx):** Invalid URL, invalid API key, rate limit exceeded.
2. **Server Errors (5xx):** Redis connection failures, internal processing errors.
3. **Crawling Errors:** Bot detection, content extraction failures, timeouts.

**Error Response Format (`app/models/error.py`):**
All error responses must conform to this Pydantic model:

```python
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]]
    retry_after: Optional[int]
    request_id: str
```

**Globs:**

```
app/core/exceptions.py
app/middleware/error_handler.py
app/main.py
```

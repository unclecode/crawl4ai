### Task 4: Create FastAPI application with health check endpoint

**Description:**

```
This task involves bootstrapping the main FastAPI application with essential middleware. The primary deliverable is a `/health` endpoint that checks the application's status and its connectivity to essential services.

4. Create FastAPI application with health check endpoint
- Set up FastAPI application with proper middleware configuration
- Implement /health endpoint with Redis connectivity check
- Add request logging middleware with correlation IDs
- Set up CORS configuration for frontend integration
- Create error handling middleware for consistent error responses
- Write integration tests for health check endpoint
Requirements: 3.1

**Endpoint:**
- `GET /health` - Service health check

**Health Check Requirements:**
- API responsiveness (the endpoint returns 200 OK)
- Redis connectivity check
- Background worker process status (if possible to check)
- Memory/CPU thresholds (optional, can be a simple check)
```

**Globs:**

```
app/main.py
app/api/endpoints/health.py
app/middleware/**/*.py
tests/api/test_health.py
```

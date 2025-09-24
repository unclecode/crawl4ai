## Task 1: Set up project structure and core configuration (Revised)

**Description:**

````
This task is to establish the foundational structure of the FastAPI project. This includes creating the main application directory with a logical module layout. We will set up `pyproject.toml` to manage dependencies and create the Pydantic Settings model that reads environment variables.


1. Create FastAPI project directory structure with proper module organization
- Set up pyproject.toml with all required dependencies (FastAPI, Redis, httpx, BeautifulSoup4, etc.)
- Set up environment variable configuration with Pydantic settings
Requirements: 1.1, 3.1


**Configuration Model (`app/core/config.py`):**
Implement a `ServiceConfig` model to manage all settings.
```python
class ServiceConfig(BaseModel):
    redis_url: str
    api_key: str
    admin_api_key: str
    max_concurrent_crawls: int = 10
    max_pages_per_crawl: int = 50
    cache_ttl_seconds: int = 3600
    rate_limit_per_minute: int = 100
    log_level: str = "INFO"

    # Feature Flags
    enable_admin_api: bool = True
    enable_metrics: bool = True
    enable_cache: bool = True
````

````
**Environment Variables:**
The configuration should be sourced from the following environment variables (which will be set manually in Railway):
```bash
# Core Configuration
REDIS_URL=redis://...
API_KEY=your-api-key
ADMIN_API_KEY=admin-key
LOG_LEVEL=INFO

# Service Limits
MAX_CONCURRENT_CRAWLS=10
MAX_PAGES_PER_CRAWL=50
CACHE_TTL_SECONDS=3600
RATE_LIMIT_PER_MINUTE=100

# Feature Flags
ENABLE_ADMIN_API=true
ENABLE_METRICS=true
ENABLE_CACHE=true
````

```
**Note: We will not create or modify the Dockerfile or railway.json.**
```

**Globs:**

```
pyproject.toml
app/core/config.py
app/main.py
```

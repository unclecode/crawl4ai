## Task 2: Implement core data models and validation

**Description:**

````
This task focuses on defining all core data structures and validation logic using Pydantic.

2. Implement core data models and validation

2. Implement core data models and validation
- Create Pydantic models for CrawlRequest, CrawlResponse, CrawlOptions, and CrawlResult
- Implement JobStatus and UserTier enums
- Create configuration models for ServiceConfig and RetryConfig
- Add input validation for URLs with SSRF protection
- Write unit tests for all data models and validation logic
Requirements: 1.1, 1.2, 7.4

**Core Data Models (`app/models/`):**
```python
# Enums
class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class UserTier(str, Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

# Models
class CrawlOptions(BaseModel):
    max_depth: int = 1
    max_pages: int = 50
    extract_focus: str = "general"
    min_word_count: int = 50
    timeout: int = 30

class CrawlResult(BaseModel):
    url: str
    title: str
    content: str
    markdown: str
    word_count: int
    extraction_method: str
    crawled_at: datetime
    quality_score: float

class CrawlRequest(BaseModel):
    url: str
    options: CrawlOptions
    user_tier: UserTier
    job_id: str

class CrawlResponse(BaseModel):
    job_id: str
    status: JobStatus
    result: Optional[CrawlResult]
    metrics: Optional[CrawlMetrics] # Define CrawlMetrics if needed
````

```
**Input Validation (`app/core/validation.py`):**
Implement robust URL validation to prevent SSRF attacks. This must include:
- Scheme validation (allow http/https only)
- Blocking of internal/private IP ranges (e.g., 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- URL length limits
```

**Globs:**

```
app/models/**/*.py
app/core/validation.py
tests/test_models.py
tests/test_validation.py
```

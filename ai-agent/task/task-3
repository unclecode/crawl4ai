### Task 3: Set up Redis connection and basic operations

**Description:**

```
This task involves creating a robust system for interacting with Redis. We will implement a connection manager with pooling and a client wrapper with error handling.

3. Set up Redis connection and basic operations
- Implement Redis connection manager with connection pooling
- Create Redis client wrapper with error handling and retries
- Set up Redis schema for jobs, cache, rate limiting, and metrics
- Implement basic Redis operations (get, set, delete, expire)
- Write unit tests for Redis operations and connection handling
Requirements: 5.1, 6.1, 9.1

**Redis Schema Design:**
The implementation should follow this schema:

**Job Management:**
- `queue:pending` -> List[job_id]
- `queue:processing` -> Set[job_id]
- `job:{job_id}` -> HASH or JSON string for JobData
- `job:{job_id}:status` -> STRING (JobStatus enum)
- `job:{job_id}:result` -> JSON string for CrawlResult

**Caching:**
- `cache:url:{url_hash}` -> JSON string for CachedContent
- `cache:url:{url_hash}:metadata` -> JSON string for CacheMetadata

**Rate Limiting:**
- `rate:{api_key}:{window}` -> INTEGER for RequestCount

**Metrics:**
- `metrics:daily:{date}` -> JSON string for DailyStats
- `metrics:errors:{date}` -> JSON string for ErrorStats
```

**Globs:**

```
app/core/redis.py
tests/test_redis.py
```

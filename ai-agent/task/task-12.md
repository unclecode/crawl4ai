### Task 12: Implement rate limiting system

**Description:**
```
This task is to build a Redis-based rate limiting system. Implement a `RateLimiter` class and middleware based on the following tier-based configuration:


- [ ] 12. Implement rate limiting system

  - Create RateLimiter class with Redis-based counters
  - Implement per-API-key rate limiting with sliding windows
  - Add tier-based rate limits (free: 60/hour, pro: 300/hour, enterprise: 1000/hour)
  - Create rate limit headers and 429 responses with retry-after
  - Implement burst allowance for short-term spikes
  - Write unit tests for rate limiting logic and edge cases
  - _Requirements: 1.3, 9.1, 9.2, 9.3, 9.4_

**Rate Limit Configuration (`app/models/config.py`):**
```python
class RateLimitConfig(BaseModel):
    free_tier: int = 60      # requests per hour
    pro_tier: int = 300      # requests per hour
    enterprise_tier: int = 1000 # requests per hour
    window_size: int = 3600  # seconds
    burst_allowance: int = 10  # extra requests
```
```
The system must use a sliding window algorithm and return a 429 response with a `Retry-After` header when a limit is exceeded.
```

**Globs:**
```
app/services/rate_limiter.py
app/middleware/rate_limit_middleware.py
app/core/dependencies.py
tests/services/test_rate_limiter.py
```
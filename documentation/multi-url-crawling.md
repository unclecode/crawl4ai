Advanced Multi-URL Crawling with Dispatchers
============================================

> **Heads Up**: Crawl4AI supports advanced dispatchers for **parallel** or **throttled** crawling, providing dynamic rate limiting and memory usage checks. The built-in `arun_many()` function uses these dispatchers to handle concurrency efficiently.

1. Introduction
---------------

When crawling many URLs:

* **Basic**: Use `arun()` in a loop (simple but less efficient)
* **Better**: Use `arun_many()`, which efficiently handles multiple URLs with proper concurrency control
* **Best**: Customize dispatcher behavior for your specific needs (memory management, rate limits, etc.)

**Why Dispatchers?**

* **Adaptive**: Memory-based dispatchers can pause or slow down based on system resources
* **Rate-limiting**: Built-in rate limiting with exponential backoff for 429/503 responses
* **Real-time Monitoring**: Live dashboard of ongoing tasks, memory usage, and performance
* **Flexibility**: Choose between memory-adaptive or semaphore-based concurrency

---

2. Core Components
------------------

### 2.1 Rate Limiter

```
class RateLimiter:
    def __init__(
        # Random delay range between requests
        base_delay: Tuple[float, float] = (1.0, 3.0),

        # Maximum backoff delay
        max_delay: float = 60.0,

        # Retries before giving up
        max_retries: int = 3,

        # Status codes triggering backoff
        rate_limit_codes: List[int] = [429, 503]
    )
```

Here’s the revised and simplified explanation of the **RateLimiter**, focusing on constructor parameters and adhering to your markdown style and mkDocs guidelines.

#### RateLimiter Constructor Parameters

The **RateLimiter** is a utility that helps manage the pace of requests to avoid overloading servers or getting blocked due to rate limits. It operates internally to delay requests and handle retries but can be configured using its constructor parameters.

**Parameters of the `RateLimiter` constructor:**

1. **`base_delay`** (`Tuple[float, float]`, default: `(1.0, 3.0)`)
  The range for a random delay (in seconds) between consecutive requests to the same domain.

* A random delay is chosen between `base_delay[0]` and `base_delay[1]` for each request.
* This prevents sending requests at a predictable frequency, reducing the chances of triggering rate limits.

**Example:**
If `base_delay = (2.0, 5.0)`, delays could be randomly chosen as `2.3s`, `4.1s`, etc.

---
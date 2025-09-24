### Task 13: Create metrics collection and Prometheus endpoint

**Description:**
```
This task involves implementing a `MetricsCollector` and exposing the data via a Prometheus-compatible endpoint.

- [ ] 13. Create metrics collection and Prometheus endpoint

  - Implement MetricsCollector class for performance tracking
  - Add metrics for crawl duration, success/failure rates, and response times
  - Create Redis queue depth and cache performance metrics
  - Implement GET /metrics endpoint in Prometheus format
  - Add business metrics (user tier distribution, content quality scores)
  - Write unit tests for metrics collection and formatting
  - _Requirements: 3.2, 10.1, 10.2, 10.3, 10.4_

**Endpoint:**
- `GET /metrics` - Prometheus metrics

**Metrics to Collect:**
1. **Business Metrics:**
   - Crawl success/failure rates
   - Average response times by tier
   - Cache hit ratios
   - User tier distribution of requests
2. **Technical Metrics:**
   - API endpoint latencies (e.g., using a middleware)
   - Redis operation times
   - Queue depth and processing rates
3. **Error Metrics:**
   - Error rates by type (4xx, 5xx, crawl errors)
   - Retry attempt counts
   - Timeout frequencies
```

**Globs:**
```
app/services/metrics.py
app/api/endpoints/metrics.py
tests/services/test_metrics.py
```
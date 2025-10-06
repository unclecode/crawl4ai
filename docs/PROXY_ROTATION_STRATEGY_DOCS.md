# Proxy Rotation Strategy Documentation

## Overview

The Crawl4AI FastAPI server now includes comprehensive proxy rotation functionality that allows you to distribute requests across multiple proxy servers using different rotation strategies. This feature helps prevent IP blocking, distributes load across proxy infrastructure, and provides redundancy for high-availability crawling operations.

## Available Proxy Rotation Strategies

| Strategy | Description | Use Case | Performance |
|----------|-------------|----------|-------------|
| `round_robin` | Cycles through proxies sequentially | Even distribution, predictable pattern | ⭐⭐⭐⭐⭐ |
| `random` | Randomly selects from available proxies | Unpredictable traffic pattern | ⭐⭐⭐⭐ |
| `least_used` | Uses proxy with lowest usage count | Optimal load balancing | ⭐⭐⭐ |
| `failure_aware` | Avoids failed proxies with auto-recovery | High availability, fault tolerance | ⭐⭐⭐⭐ |

## API Endpoints

### POST /crawl

Standard crawling endpoint with proxy rotation support.

**Request Body:**
```json
{
  "urls": ["https://example.com"],
  "proxy_rotation_strategy": "round_robin",
  "proxies": [
    {"server": "http://proxy1.com:8080", "username": "user1", "password": "pass1"},
    {"server": "http://proxy2.com:8080", "username": "user2", "password": "pass2"}
  ],
  "browser_config": {},
  "crawler_config": {}
}
```

### POST /crawl/stream

Streaming crawling endpoint with proxy rotation support.

**Request Body:**
```json
{
  "urls": ["https://example.com"],
  "proxy_rotation_strategy": "failure_aware",
  "proxy_failure_threshold": 3,
  "proxy_recovery_time": 300,
  "proxies": [
    {"server": "http://proxy1.com:8080", "username": "user1", "password": "pass1"},
    {"server": "http://proxy2.com:8080", "username": "user2", "password": "pass2"}
  ],
  "browser_config": {},
  "crawler_config": {
    "stream": true
  }
}
```

## Parameters

### proxy_rotation_strategy (optional)
- **Type:** `string`
- **Default:** `null` (no proxy rotation)
- **Options:** `"round_robin"`, `"random"`, `"least_used"`, `"failure_aware"`
- **Description:** Selects the proxy rotation strategy for distributing requests

### proxies (optional)
- **Type:** `array of objects`
- **Default:** `null`
- **Description:** List of proxy configurations to rotate between
- **Required when:** `proxy_rotation_strategy` is specified

### proxy_failure_threshold (optional)
- **Type:** `integer`
- **Default:** `3`
- **Range:** `1-10`
- **Description:** Number of failures before marking a proxy as unhealthy (failure_aware only)

### proxy_recovery_time (optional)
- **Type:** `integer`
- **Default:** `300` (5 minutes)
- **Range:** `60-3600` seconds
- **Description:** Time to wait before attempting to use a failed proxy again (failure_aware only)

## Proxy Configuration Format

### Full Configuration
```json
{
  "server": "http://proxy.example.com:8080",
  "username": "proxy_user",
  "password": "proxy_pass",
  "ip": "192.168.1.100"
}
```

### Minimal Configuration
```json
{
  "server": "http://192.168.1.100:8080"
}
```

### SOCKS Proxy Support
```json
{
  "server": "socks5://127.0.0.1:1080",
  "username": "socks_user",
  "password": "socks_pass"
}
```

## Usage Examples

### 1. Round Robin Strategy

```bash
curl -X POST "http://localhost:11235/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://httpbin.org/ip"],
    "proxy_rotation_strategy": "round_robin",
    "proxies": [
      {"server": "http://proxy1.com:8080", "username": "user1", "password": "pass1"},
      {"server": "http://proxy2.com:8080", "username": "user2", "password": "pass2"},
      {"server": "http://proxy3.com:8080", "username": "user3", "password": "pass3"}
    ]
  }'
```

### 2. Random Strategy with Minimal Config

```bash
curl -X POST "http://localhost:11235/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://httpbin.org/headers"],
    "proxy_rotation_strategy": "random",
    "proxies": [
      {"server": "http://192.168.1.100:8080"},
      {"server": "http://192.168.1.101:8080"},
      {"server": "http://192.168.1.102:8080"}
    ]
  }'
```

### 3. Least Used Strategy with Load Balancing

```bash
curl -X POST "http://localhost:11235/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com", "https://httpbin.org/html", "https://httpbin.org/json"],
    "proxy_rotation_strategy": "least_used",
    "proxies": [
      {"server": "http://proxy1.com:8080", "username": "user1", "password": "pass1"},
      {"server": "http://proxy2.com:8080", "username": "user2", "password": "pass2"}
    ],
    "crawler_config": {
      "cache_mode": "bypass"
    }
  }'
```

### 4. Failure-Aware Strategy with High Availability

```bash
curl -X POST "http://localhost:11235/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "proxy_rotation_strategy": "failure_aware",
    "proxy_failure_threshold": 2,
    "proxy_recovery_time": 180,
    "proxies": [
      {"server": "http://proxy1.com:8080", "username": "user1", "password": "pass1"},
      {"server": "http://proxy2.com:8080", "username": "user2", "password": "pass2"},
      {"server": "http://proxy3.com:8080", "username": "user3", "password": "pass3"}
    ],
    "headless": true
  }'
```

### 5. Streaming with Proxy Rotation

```bash
curl -X POST "http://localhost:11235/crawl/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com", "https://httpbin.org/html"],
    "proxy_rotation_strategy": "round_robin",
    "proxies": [
      {"server": "http://proxy1.com:8080", "username": "user1", "password": "pass1"},
      {"server": "http://proxy2.com:8080", "username": "user2", "password": "pass2"}
    ],
    "crawler_config": {
      "stream": true,
      "cache_mode": "bypass"
    }
  }'
```

## Combining with Anti-Bot Strategies

You can combine proxy rotation with anti-bot strategies for maximum effectiveness:

```bash
curl -X POST "http://localhost:11235/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://protected-site.com"],
    "anti_bot_strategy": "stealth",
    "proxy_rotation_strategy": "failure_aware",
    "proxy_failure_threshold": 2,
    "proxies": [
      {"server": "http://proxy1.com:8080", "username": "user1", "password": "pass1"},
      {"server": "http://proxy2.com:8080", "username": "user2", "password": "pass2"}
    ],
    "headless": true,
    "browser_config": {
      "enable_stealth": true
    }
  }'
```

## Strategy Details

### Round Robin Strategy
- **Algorithm:** Sequential cycling through proxy list
- **Pros:** Predictable, even distribution, simple
- **Cons:** Predictable pattern may be detectable
- **Best for:** General use, development, testing

### Random Strategy
- **Algorithm:** Random selection from available proxies
- **Pros:** Unpredictable pattern, good for evasion
- **Cons:** Uneven distribution possible
- **Best for:** Anti-detection, varying traffic patterns

### Least Used Strategy
- **Algorithm:** Selects proxy with minimum usage count
- **Pros:** Optimal load balancing, prevents overloading
- **Cons:** Slightly more complex, tracking overhead
- **Best for:** High-volume crawling, load balancing

### Failure-Aware Strategy
- **Algorithm:** Tracks proxy health, auto-recovery
- **Pros:** High availability, fault tolerance, automatic recovery
- **Cons:** Most complex, memory overhead for tracking
- **Best for:** Production environments, critical crawling

## Error Handling

### Common Errors

#### Invalid Proxy Configuration
```json
{
  "error": "Invalid proxy configuration: Proxy configuration missing 'server' field: {'username': 'user1'}"
}
```

#### Unsupported Strategy
```json
{
  "error": "Unsupported proxy rotation strategy: invalid_strategy. Available: round_robin, random, least_used, failure_aware"
}
```

#### Missing Proxies
When `proxy_rotation_strategy` is specified but `proxies` is empty:
```json
{
  "error": "proxy_rotation_strategy specified but no proxies provided"
}
```

## Environment Variable Support

You can also configure proxies using environment variables:

```bash
# Set proxy list (comma-separated)
export PROXIES="proxy1.com:8080:user1:pass1,proxy2.com:8080:user2:pass2"

# Set default strategy
export PROXY_ROTATION_STRATEGY="round_robin"
```

## Performance Considerations

1. **Strategy Overhead:**
   - Round Robin: Minimal overhead
   - Random: Low overhead
   - Least Used: Medium overhead (usage tracking)
   - Failure Aware: High overhead (health tracking)

2. **Memory Usage:**
   - Round Robin: ~O(n) where n = number of proxies
   - Random: ~O(n)
   - Least Used: ~O(n) + usage counters
   - Failure Aware: ~O(n) + health tracking data

3. **Concurrent Safety:**
   - All strategies are async-safe with proper locking
   - No race conditions in proxy selection

## Best Practices

1. **Production Deployment:**
   - Use `failure_aware` strategy for high availability
   - Set appropriate failure thresholds (2-3)
   - Use recovery times between 3-10 minutes

2. **Development/Testing:**
   - Use `round_robin` for predictable behavior
   - Start with small proxy pools (2-3 proxies)

3. **Anti-Detection:**
   - Combine with `stealth` or `undetected` anti-bot strategies
   - Use `random` strategy for unpredictable patterns
   - Vary proxy geographic locations

4. **Load Balancing:**
   - Use `least_used` for even distribution
   - Monitor proxy performance and adjust pools accordingly

5. **Error Monitoring:**
   - Monitor failure rates with `failure_aware` strategy
   - Set up alerts for proxy pool depletion
   - Implement fallback mechanisms

## Integration Examples

### Python Requests
```python
import requests

payload = {
    "urls": ["https://example.com"],
    "proxy_rotation_strategy": "round_robin",
    "proxies": [
        {"server": "http://proxy1.com:8080", "username": "user1", "password": "pass1"},
        {"server": "http://proxy2.com:8080", "username": "user2", "password": "pass2"}
    ]
}

response = requests.post("http://localhost:11235/crawl", json=payload)
print(response.json())
```

### JavaScript/Node.js
```javascript
const axios = require('axios');

const payload = {
  urls: ["https://example.com"],
  proxy_rotation_strategy: "failure_aware",
  proxy_failure_threshold: 2,
  proxies: [
    {server: "http://proxy1.com:8080", username: "user1", password: "pass1"},
    {server: "http://proxy2.com:8080", username: "user2", password: "pass2"}
  ]
};

axios.post('http://localhost:11235/crawl', payload)
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
```

### cURL with Multiple URLs
```bash
curl -X POST "http://localhost:11235/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://example.com",
      "https://httpbin.org/html",
      "https://httpbin.org/json",
      "https://httpbin.org/xml"
    ],
    "proxy_rotation_strategy": "least_used",
    "proxies": [
      {"server": "http://proxy1.com:8080", "username": "user1", "password": "pass1"},
      {"server": "http://proxy2.com:8080", "username": "user2", "password": "pass2"},
      {"server": "http://proxy3.com:8080", "username": "user3", "password": "pass3"}
    ],
    "crawler_config": {
      "cache_mode": "bypass",
      "wait_for_images": false
    }
  }'
```

## Troubleshooting

### Common Issues

1. **All proxies failing:**
   - Check proxy connectivity
   - Verify authentication credentials
   - Ensure proxy servers support the target protocols

2. **Uneven distribution:**
   - Use `least_used` strategy for better balancing
   - Monitor proxy usage patterns

3. **High memory usage:**
   - Reduce proxy pool size
   - Consider using `round_robin` instead of `failure_aware`

4. **Slow performance:**
   - Check proxy response times
   - Use geographically closer proxies
   - Reduce failure thresholds

### Debug Information

Enable verbose logging to see proxy selection details:

```json
{
  "urls": ["https://example.com"],
  "proxy_rotation_strategy": "failure_aware",
  "proxies": [...],
  "crawler_config": {
    "verbose": true
  }
}
```

This will log which proxy is selected for each request and any failure/recovery events.
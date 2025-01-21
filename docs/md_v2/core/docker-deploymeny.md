# Docker Deployment

Crawl4AI provides official Docker images for easy deployment and scalability. This guide covers installation, configuration, and usage of Crawl4AI in Docker environments.

## Quick Start 🚀

Pull and run the basic version:

```bash
# Basic run without security
docker pull unclecode/crawl4ai:basic
docker run -p 11235:11235 unclecode/crawl4ai:basic

# Run with API security enabled
docker run -p 11235:11235 -e CRAWL4AI_API_TOKEN=your_secret_token unclecode/crawl4ai:basic
```

## Running with Docker Compose 🐳

### Use Docker Compose (From Local Dockerfile or Docker Hub)

Crawl4AI provides flexibility to use Docker Compose for managing your containerized services. You can either build the image locally from the provided `Dockerfile` or use the pre-built image from Docker Hub.

### **Option 1: Using Docker Compose to Build Locally**
If you want to build the image locally, use the provided `docker-compose.local.yml` file.

```bash
docker-compose -f docker-compose.local.yml up -d
```

This will:
1. Build the Docker image from the provided `Dockerfile`.
2. Start the container and expose it on `http://localhost:11235`.

---

### **Option 2: Using Docker Compose with Pre-Built Image from Hub**
If you prefer using the pre-built image on Docker Hub, use the `docker-compose.hub.yml` file.

```bash
docker-compose -f docker-compose.hub.yml up -d
```

This will:
1. Pull the pre-built image `unclecode/crawl4ai:basic` (or `all`, depending on your configuration).
2. Start the container and expose it on `http://localhost:11235`.

---

### **Stopping the Running Services**

To stop the services started via Docker Compose, you can use:

```bash
docker-compose -f docker-compose.local.yml down
# OR
docker-compose -f docker-compose.hub.yml down
```

If the containers don’t stop and the application is still running, check the running containers:

```bash
docker ps
```

Find the `CONTAINER ID` of the running service and stop it forcefully:

```bash
docker stop <CONTAINER_ID>
```

---

### **Debugging with Docker Compose**

- **Check Logs**: To view the container logs:
  ```bash
  docker-compose -f docker-compose.local.yml logs -f
  ```

- **Remove Orphaned Containers**: If the service is still running unexpectedly:
  ```bash
  docker-compose -f docker-compose.local.yml down --remove-orphans
  ```

- **Manually Remove Network**: If the network is still in use:
  ```bash
  docker network ls
  docker network rm crawl4ai_default
  ```

---

### Why Use Docker Compose?

Docker Compose is the recommended way to deploy Crawl4AI because:
1. It simplifies multi-container setups.
2. Allows you to define environment variables, resources, and ports in a single file.
3. Makes it easier to switch between local development and production-ready images.

For example, your `docker-compose.yml` could include API keys, token settings, and memory limits, making deployment quick and consistent.




## API Security 🔒

### Understanding CRAWL4AI_API_TOKEN

The `CRAWL4AI_API_TOKEN` provides optional security for your Crawl4AI instance:

- If `CRAWL4AI_API_TOKEN` is set: All API endpoints (except `/health`) require authentication
- If `CRAWL4AI_API_TOKEN` is not set: The API is publicly accessible

```bash
# Secured Instance
docker run -p 11235:11235 -e CRAWL4AI_API_TOKEN=your_secret_token unclecode/crawl4ai:all

# Unsecured Instance
docker run -p 11235:11235 unclecode/crawl4ai:all
```

### Making API Calls

For secured instances, include the token in all requests:

```python
import requests

# Setup headers if token is being used
api_token = "your_secret_token"  # Same token set in CRAWL4AI_API_TOKEN
headers = {"Authorization": f"Bearer {api_token}"} if api_token else {}

# Making authenticated requests
response = requests.post(
    "http://localhost:11235/crawl",
    headers=headers,
    json={
        "urls": "https://example.com",
        "priority": 10
    }
)

# Checking task status
task_id = response.json()["task_id"]
status = requests.get(
    f"http://localhost:11235/task/{task_id}",
    headers=headers
)
```

### Using with Docker Compose

In your `docker-compose.yml`:
```yaml
services:
  crawl4ai:
    image: unclecode/crawl4ai:all
    environment:
      - CRAWL4AI_API_TOKEN=${CRAWL4AI_API_TOKEN:-}  # Optional
    # ... other configuration
```

Then either:
1. Set in `.env` file:
```env
CRAWL4AI_API_TOKEN=your_secret_token
```

2. Or set via command line:
```bash
CRAWL4AI_API_TOKEN=your_secret_token docker-compose up
```

> **Security Note**: If you enable the API token, make sure to keep it secure and never commit it to version control. The token will be required for all API endpoints except the health check endpoint (`/health`).

## Configuration Options 🔧

### Environment Variables

You can configure the service using environment variables:

```bash
# Basic configuration
docker run -p 11235:11235 \
    -e MAX_CONCURRENT_TASKS=5 \
    unclecode/crawl4ai:all

# With security and LLM support
docker run -p 11235:11235 \
    -e CRAWL4AI_API_TOKEN=your_secret_token \
    -e OPENAI_API_KEY=sk-... \
    -e ANTHROPIC_API_KEY=sk-ant-... \
    unclecode/crawl4ai:all
```

### Using Docker Compose (Recommended) 🐳

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  crawl4ai:
    image: unclecode/crawl4ai:all
    ports:
      - "11235:11235"
    environment:
      - CRAWL4AI_API_TOKEN=${CRAWL4AI_API_TOKEN:-}  # Optional API security
      - MAX_CONCURRENT_TASKS=5
      # LLM Provider Keys
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
    volumes:
      - /dev/shm:/dev/shm
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 1G
```

You can run it in two ways:

1. Using environment variables directly:
```bash
CRAWL4AI_API_TOKEN=secret123 OPENAI_API_KEY=sk-... docker-compose up
```

2. Using a `.env` file (recommended):
Create a `.env` file in the same directory:
```env
# API Security (optional)
CRAWL4AI_API_TOKEN=your_secret_token

# LLM Provider Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Other Configuration
MAX_CONCURRENT_TASKS=5
```

Then simply run:
```bash
docker-compose up
```

### Testing the Deployment 🧪

```python
import requests

# For unsecured instances
def test_unsecured():
    # Health check
    health = requests.get("http://localhost:11235/health")
    print("Health check:", health.json())

    # Basic crawl
    response = requests.post(
        "http://localhost:11235/crawl",
        json={
            "urls": "https://www.nbcnews.com/business",
            "priority": 10
        }
    )
    task_id = response.json()["task_id"]
    print("Task ID:", task_id)

# For secured instances
def test_secured(api_token):
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # Basic crawl with authentication
    response = requests.post(
        "http://localhost:11235/crawl",
        headers=headers,
        json={
            "urls": "https://www.nbcnews.com/business",
            "priority": 10
        }
    )
    task_id = response.json()["task_id"]
    print("Task ID:", task_id)
```

### LLM Extraction Example 🤖

When you've configured your LLM provider keys (via environment variables or `.env`), you can use LLM extraction:

```python
request = {
    "urls": "https://example.com",
    "extraction_config": {
        "type": "llm",
        "params": {
            "provider": "openai/gpt-4",
            "instruction": "Extract main topics from the page"
        }
    }
}

# Make the request (add headers if using API security)
response = requests.post("http://localhost:11235/crawl", json=request)
```

> **Note**: Remember to add `.env` to your `.gitignore` to keep your API keys secure!


## Usage Examples 📝

### Basic Crawling

```python
request = {
    "urls": "https://www.nbcnews.com/business",
    "priority": 10
}

response = requests.post("http://localhost:11235/crawl", json=request)
task_id = response.json()["task_id"]

# Get results
result = requests.get(f"http://localhost:11235/task/{task_id}")
```

### Structured Data Extraction

```python
schema = {
    "name": "Crypto Prices",
    "baseSelector": ".cds-tableRow-t45thuk",
    "fields": [
        {
            "name": "crypto",
            "selector": "td:nth-child(1) h2",
            "type": "text",
        },
        {
            "name": "price",
            "selector": "td:nth-child(2)",
            "type": "text",
        }
    ],
}

request = {
    "urls": "https://www.coinbase.com/explore",
    "extraction_config": {
        "type": "json_css",
        "params": {"schema": schema}
    }
}
```

### Dynamic Content Handling

```python
request = {
    "urls": "https://www.nbcnews.com/business",
    "js_code": [
        "const loadMoreButton = Array.from(document.querySelectorAll('button')).find(button => button.textContent.includes('Load More')); loadMoreButton && loadMoreButton.click();"
    ],
    "wait_for": "article.tease-card:nth-child(10)"
}
```

### AI-Powered Extraction (Full Version)

```python
request = {
    "urls": "https://www.nbcnews.com/business",
    "extraction_config": {
        "type": "cosine",
        "params": {
            "semantic_filter": "business finance economy",
            "word_count_threshold": 10,
            "max_dist": 0.2,
            "top_k": 3
        }
    }
}
```

## Platform-Specific Instructions 💻

### macOS
```bash
docker pull unclecode/crawl4ai:basic
docker run -p 11235:11235 unclecode/crawl4ai:basic
```

### Ubuntu
```bash
# Basic version
docker pull unclecode/crawl4ai:basic
docker run -p 11235:11235 unclecode/crawl4ai:basic

# With GPU support
docker pull unclecode/crawl4ai:gpu
docker run --gpus all -p 11235:11235 unclecode/crawl4ai:gpu
```

### Windows (PowerShell)
```powershell
docker pull unclecode/crawl4ai:basic
docker run -p 11235:11235 unclecode/crawl4ai:basic
```

## Testing 🧪

Save this as `test_docker.py`:

```python
import requests
import json
import time
import sys

class Crawl4AiTester:
    def __init__(self, base_url: str = "http://localhost:11235"):
        self.base_url = base_url
        
    def submit_and_wait(self, request_data: dict, timeout: int = 300) -> dict:
        # Submit crawl job
        response = requests.post(f"{self.base_url}/crawl", json=request_data)
        task_id = response.json()["task_id"]
        print(f"Task ID: {task_id}")
        
        # Poll for result
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Task {task_id} timeout")
                
            result = requests.get(f"{self.base_url}/task/{task_id}")
            status = result.json()
            
            if status["status"] == "completed":
                return status
                
            time.sleep(2)

def test_deployment():
    tester = Crawl4AiTester()
    
    # Test basic crawl
    request = {
        "urls": "https://www.nbcnews.com/business",
        "priority": 10
    }
    
    result = tester.submit_and_wait(request)
    print("Basic crawl successful!")
    print(f"Content length: {len(result['result']['markdown'])}")

if __name__ == "__main__":
    test_deployment()
```

## Advanced Configuration ⚙️

### Crawler Parameters

The `crawler_params` field allows you to configure the browser instance and crawling behavior. Here are key parameters you can use:

```python
request = {
    "urls": "https://example.com",
    "crawler_params": {
        # Browser Configuration
        "headless": True,                    # Run in headless mode
        "browser_type": "chromium",          # chromium/firefox/webkit
        "user_agent": "custom-agent",        # Custom user agent
        "proxy": "http://proxy:8080",        # Proxy configuration
        
        # Performance & Behavior
        "page_timeout": 30000,               # Page load timeout (ms)
        "verbose": True,                     # Enable detailed logging
        "semaphore_count": 5,               # Concurrent request limit
        
        # Anti-Detection Features
        "simulate_user": True,               # Simulate human behavior
        "magic": True,                       # Advanced anti-detection
        "override_navigator": True,          # Override navigator properties
        
        # Session Management
        "user_data_dir": "./browser-data",   # Browser profile location
        "use_managed_browser": True,         # Use persistent browser
    }
}
```

### Extra Parameters

The `extra` field allows passing additional parameters directly to the crawler's `arun` function:

```python
request = {
    "urls": "https://example.com",
    "extra": {
        "word_count_threshold": 10,          # Min words per block
        "only_text": True,                   # Extract only text
        "bypass_cache": True,                # Force fresh crawl
        "process_iframes": True,             # Include iframe content
    }
}
```

### Complete Examples

1. **Advanced News Crawling**
```python
request = {
    "urls": "https://www.nbcnews.com/business",
    "crawler_params": {
        "headless": True,
        "page_timeout": 30000,
        "remove_overlay_elements": True      # Remove popups
    },
    "extra": {
        "word_count_threshold": 50,          # Longer content blocks
        "bypass_cache": True                 # Fresh content
    },
    "css_selector": ".article-body"
}
```

2. **Anti-Detection Configuration**
```python
request = {
    "urls": "https://example.com",
    "crawler_params": {
        "simulate_user": True,
        "magic": True,
        "override_navigator": True,
        "user_agent": "Mozilla/5.0 ...",
        "headers": {
            "Accept-Language": "en-US,en;q=0.9"
        }
    }
}
```

3. **LLM Extraction with Custom Parameters**
```python
request = {
    "urls": "https://openai.com/pricing",
    "extraction_config": {
        "type": "llm",
        "params": {
            "provider": "openai/gpt-4",
            "schema": pricing_schema
        }
    },
    "crawler_params": {
        "verbose": True,
        "page_timeout": 60000
    },
    "extra": {
        "word_count_threshold": 1,
        "only_text": True
    }
}
```

4. **Session-Based Dynamic Content**
```python
request = {
    "urls": "https://example.com",
    "crawler_params": {
        "session_id": "dynamic_session",
        "headless": False,
        "page_timeout": 60000
    },
    "js_code": ["window.scrollTo(0, document.body.scrollHeight);"],
    "wait_for": "js:() => document.querySelectorAll('.item').length > 10",
    "extra": {
        "delay_before_return_html": 2.0
    }
}
```

5. **Screenshot with Custom Timing**
```python
request = {
    "urls": "https://example.com",
    "screenshot": True,
    "crawler_params": {
        "headless": True,
        "screenshot_wait_for": ".main-content"
    },
    "extra": {
        "delay_before_return_html": 3.0
    }
}
```

### Parameter Reference Table

| Category | Parameter | Type | Description |
|----------|-----------|------|-------------|
| Browser | headless | bool | Run browser in headless mode |
| Browser | browser_type | str | Browser engine selection |
| Browser | user_agent | str | Custom user agent string |
| Network | proxy | str | Proxy server URL |
| Network | headers | dict | Custom HTTP headers |
| Timing | page_timeout | int | Page load timeout (ms) |
| Timing | delay_before_return_html | float | Wait before capture |
| Anti-Detection | simulate_user | bool | Human behavior simulation |
| Anti-Detection | magic | bool | Advanced protection |
| Session | session_id | str | Browser session ID |
| Session | user_data_dir | str | Profile directory |
| Content | word_count_threshold | int | Minimum words per block |
| Content | only_text | bool | Text-only extraction |
| Content | process_iframes | bool | Include iframe content |
| Debug | verbose | bool | Detailed logging |
| Debug | log_console | bool | Browser console logs |

## Troubleshooting 🔍

### Common Issues

1. **Connection Refused**
   ```
   Error: Connection refused at localhost:11235
   ```
   Solution: Ensure the container is running and ports are properly mapped.

2. **Resource Limits**
   ```
   Error: No available slots
   ```
   Solution: Increase MAX_CONCURRENT_TASKS or container resources.

3. **GPU Access**
   ```
   Error: GPU not found
   ```
   Solution: Ensure proper NVIDIA drivers and use `--gpus all` flag.

### Debug Mode

Access container for debugging:
```bash
docker run -it --entrypoint /bin/bash unclecode/crawl4ai:all
```

View container logs:
```bash
docker logs [container_id]
```

## Best Practices 🌟

1. **Resource Management**
   - Set appropriate memory and CPU limits
   - Monitor resource usage via health endpoint
   - Use basic version for simple crawling tasks

2. **Scaling**
   - Use multiple containers for high load
   - Implement proper load balancing
   - Monitor performance metrics

3. **Security**
   - Use environment variables for sensitive data
   - Implement proper network isolation
   - Regular security updates

## API Reference 📚

### Health Check
```http
GET /health
```

### Submit Crawl Task
```http
POST /crawl
Content-Type: application/json

{
    "urls": "string or array",
    "extraction_config": {
        "type": "basic|llm|cosine|json_css",
        "params": {}
    },
    "priority": 1-10,
    "ttl": 3600
}
```

### Get Task Status
```http
GET /task/{task_id}
```

For more details, visit the [official documentation](https://docs.crawl4ai.com/).
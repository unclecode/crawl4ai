# Crawl4AI Node Manager (cnode) - User Guide 🚀

Self-host your own Crawl4AI server cluster with one command. Scale from development to production effortlessly.

## Table of Contents
- [What is cnode?](#what-is-cnode)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Scaling & Production](#scaling--production)
- [Monitoring Dashboard](#monitoring-dashboard)
- [Using the API](#using-the-api)
- [Management Commands](#management-commands)
- [Troubleshooting](#troubleshooting)
- [Advanced Topics](#advanced-topics)

---

## What is cnode?

**cnode** (Crawl4AI Node Manager) is a CLI tool that manages Crawl4AI Docker server instances with automatic scaling and load balancing.

### Key Features

✅ **One-Command Deployment** - Start a server or cluster instantly
✅ **Automatic Scaling** - Single container or multi-replica cluster
✅ **Built-in Load Balancing** - Docker Swarm or Nginx (auto-detected)
✅ **Real-time Monitoring** - Beautiful web dashboard
✅ **Zero Configuration** - Works out of the box
✅ **Production Ready** - Auto-scaling, health checks, rolling updates

### Architecture Modes

| Replicas | Mode | Load Balancer | Use Case |
|----------|------|---------------|----------|
| 1 | Single Container | None | Development, testing |
| 2+ | Docker Swarm | Built-in | Production (if Swarm available) |
| 2+ | Docker Compose | Nginx | Production (fallback) |

---

## Quick Start

### 1. Install cnode

```bash
# One-line installation
curl -sSL https://crawl4ai.com/install-cnode.sh | bash
```

**Requirements:**
- Python 3.8+
- Docker
- Git

### 2. Start Your First Server

```bash
# Start single development server
cnode start

# Or start a production cluster with 5 replicas
cnode start --replicas 5
```

That's it! Your server is running at **http://localhost:11235** 🎉

---

## Installation

### Method 1: Quick Install (Recommended)

```bash
curl -sSL https://crawl4ai.com/install-cnode.sh | bash
```

### Method 2: From GitHub

```bash
# Clone the repository
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai/deploy/installer

# Run local installer
./install-cnode.sh
```

### Method 3: Custom Location

```bash
# Install to custom directory
INSTALL_DIR=$HOME/.local/bin curl -sSL https://crawl4ai.com/install-cnode.sh | bash

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

### Verify Installation

```bash
cnode --help
```

---

## Basic Usage

### Start Server

```bash
# Development server (1 replica)
cnode start

# Production cluster (5 replicas with auto-scaling)
cnode start --replicas 5

# Custom port
cnode start --port 8080

# Specific Docker image
cnode start --image unclecode/crawl4ai:0.7.0
```

### Check Status

```bash
cnode status
```

**Example Output:**
```
╭─────────────────── Crawl4AI Server Status ───────────────────╮
│ Status     │ 🟢 Running                                      │
│ Mode       │ swarm                                           │
│ Replicas   │ 5                                               │
│ Port       │ 11235                                           │
│ Image      │ unclecode/crawl4ai:latest                       │
│ Uptime     │ 2 hours 34 minutes                              │
│ Started    │ 2025-10-21 14:30:00                            │
╰─────────────────────────────────────────────────────────────╯

✓ Server is healthy
Access: http://localhost:11235
```

### View Logs

```bash
# Show last 100 lines
cnode logs

# Follow logs in real-time
cnode logs -f

# Show last 500 lines
cnode logs --tail 500
```

### Stop Server

```bash
# Stop server (keeps data)
cnode stop

# Stop and remove all data
cnode stop --remove-volumes
```

---

## Scaling & Production

### Scale Your Cluster

```bash
# Scale to 10 replicas (live, no downtime)
cnode scale 10

# Scale down to 2 replicas
cnode scale 2
```

**Note:** Scaling is live for Swarm/Compose modes. Single container mode requires restart.

### Production Deployment

```bash
# Start production cluster
cnode start --replicas 5 --port 11235

# Verify health
curl http://localhost:11235/health

# Monitor performance
cnode logs -f
```

### Restart Server

```bash
# Restart with same configuration
cnode restart

# Restart with new replica count
cnode restart --replicas 10
```

---

## Monitoring Dashboard

### Access the Dashboard

Once your server is running, access the real-time monitoring dashboard:

```bash
# Dashboard URL
http://localhost:11235/monitor
```

### Dashboard Features

📊 **Real-time Metrics**
- Requests per second
- Active connections
- Response times
- Error rates

📈 **Performance Graphs**
- CPU usage
- Memory consumption
- Request latency
- Throughput

🔍 **System Health**
- Container status
- Replica health
- Load distribution
- Resource utilization

![Monitor Dashboard](https://crawl4ai.com/images/monitor-dashboard.png)

### API Health Endpoint

```bash
# Quick health check
curl http://localhost:11235/health

# Response
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 9876,
  "containers": 5
}
```

---

## Using the API

### Interactive Playground

Test the API interactively:

```
http://localhost:11235/playground
```

### Basic Crawl Example

**Python:**

```python
import requests

# Simple crawl
response = requests.post(
    "http://localhost:11235/crawl",
    json={
        "urls": ["https://example.com"],
        "browser_config": {
            "type": "BrowserConfig",
            "params": {"headless": True}
        },
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {"cache_mode": "bypass"}
        }
    }
)

result = response.json()
print(f"Title: {result['result']['metadata']['title']}")
print(f"Content: {result['result']['markdown'][:200]}...")
```

**cURL:**

```bash
curl -X POST http://localhost:11235/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "browser_config": {
      "type": "BrowserConfig",
      "params": {"headless": true}
    },
    "crawler_config": {
      "type": "CrawlerRunConfig",
      "params": {"cache_mode": "bypass"}
    }
  }'
```

**JavaScript (Node.js):**

```javascript
const axios = require('axios');

async function crawl() {
  const response = await axios.post('http://localhost:11235/crawl', {
    urls: ['https://example.com'],
    browser_config: {
      type: 'BrowserConfig',
      params: { headless: true }
    },
    crawler_config: {
      type: 'CrawlerRunConfig',
      params: { cache_mode: 'bypass' }
    }
  });

  console.log('Title:', response.data.result.metadata.title);
  console.log('Content:', response.data.result.markdown.substring(0, 200));
}

crawl();
```

### Advanced Examples

**Extract with CSS Selectors:**

```python
import requests

response = requests.post(
    "http://localhost:11235/crawl",
    json={
        "urls": ["https://news.ycombinator.com"],
        "browser_config": {
            "type": "BrowserConfig",
            "params": {"headless": True}
        },
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {
                "extraction_strategy": {
                    "type": "JsonCssExtractionStrategy",
                    "params": {
                        "schema": {
                            "type": "dict",
                            "value": {
                                "baseSelector": ".athing",
                                "fields": [
                                    {"name": "title", "selector": ".titleline > a", "type": "text"},
                                    {"name": "url", "selector": ".titleline > a", "type": "attribute", "attribute": "href"},
                                    {"name": "points", "selector": ".score", "type": "text"}
                                ]
                            }
                        }
                    }
                }
            }
        }
    }
)

articles = response.json()['result']['extracted_content']
for article in articles:
    print(f"{article['title']} - {article['points']}")
```

**Streaming Multiple URLs:**

```python
import requests
import json

response = requests.post(
    "http://localhost:11235/crawl/stream",
    json={
        "urls": [
            "https://example.com",
            "https://httpbin.org/html",
            "https://python.org"
        ],
        "browser_config": {
            "type": "BrowserConfig",
            "params": {"headless": True}
        },
        "crawler_config": {
            "type": "CrawlerRunConfig",
            "params": {"stream": True}
        }
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line)
        if data.get("status") == "completed":
            break
        print(f"Crawled: {data['url']} - Success: {data['success']}")
```

### Additional Endpoints

**Screenshot:**
```bash
curl -X POST http://localhost:11235/screenshot \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}' \
  --output screenshot.png
```

**PDF Export:**
```bash
curl -X POST http://localhost:11235/pdf \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}' \
  --output page.pdf
```

**HTML Extraction:**
```bash
curl -X POST http://localhost:11235/html \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

---

## Management Commands

### All Available Commands

```bash
cnode --help              # Show help
cnode start [OPTIONS]     # Start server
cnode stop [OPTIONS]      # Stop server
cnode status              # Show status
cnode scale N             # Scale to N replicas
cnode logs [OPTIONS]      # View logs
cnode restart [OPTIONS]   # Restart server
cnode cleanup [--force]   # Clean up resources
```

### Command Options

**start:**
```bash
--replicas, -r N      # Number of replicas (default: 1)
--mode MODE           # Deployment mode: auto, single, swarm, compose
--port, -p PORT       # External port (default: 11235)
--env-file FILE       # Environment file path
--image IMAGE         # Docker image (default: unclecode/crawl4ai:latest)
```

**stop:**
```bash
--remove-volumes      # Remove persistent data (WARNING: deletes data)
```

**logs:**
```bash
--follow, -f          # Follow log output (like tail -f)
--tail N              # Number of lines to show (default: 100)
```

**scale:**
```bash
N                     # Target replica count (minimum: 1)
```

---

## Troubleshooting

### Server Won't Start

```bash
# Check Docker is running
docker ps

# Check port availability
lsof -i :11235

# Check logs for errors
cnode logs
```

### High Memory Usage

```bash
# Check current status
cnode status

# Restart to clear memory
cnode restart

# Scale down if needed
cnode scale 2
```

### Slow Response Times

```bash
# Scale up for better performance
cnode scale 10

# Check system resources
docker stats
```

### Cannot Connect to API

```bash
# Verify server is running
cnode status

# Check firewall
sudo ufw status

# Test locally
curl http://localhost:11235/health
```

### Clean Slate

```bash
# Complete cleanup and restart
cnode cleanup --force
cnode start --replicas 5
```

---

## Advanced Topics

### Environment Variables

Create `.env` file for API keys:

```bash
# .env file
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=your-key
```

Use with cnode:
```bash
cnode start --env-file .env --replicas 3
```

### Custom Docker Image

```bash
# Use specific version
cnode start --image unclecode/crawl4ai:0.7.0-r1

# Use custom registry
cnode start --image myregistry.com/crawl4ai:custom
```

### Production Best Practices

1. **Use Multiple Replicas**
   ```bash
   cnode start --replicas 5
   ```

2. **Monitor Regularly**
   ```bash
   # Set up monitoring cron
   */5 * * * * cnode status | mail -s "Crawl4AI Status" admin@example.com
   ```

3. **Regular Log Rotation**
   ```bash
   cnode logs --tail 1000 > crawl4ai.log
   cnode restart
   ```

4. **Resource Limits**
   - Ensure adequate RAM (2GB per replica minimum)
   - Monitor disk space for cached data
   - Use SSD for better performance

### Integration Examples

**With Python App:**
```python
from crawl4ai.docker_client import Crawl4aiDockerClient

async def main():
    async with Crawl4aiDockerClient(base_url="http://localhost:11235") as client:
        results = await client.crawl(["https://example.com"])
        print(results[0].markdown)
```

**With Node.js:**
```javascript
const Crawl4AI = require('crawl4ai-client');
const client = new Crawl4AI('http://localhost:11235');

client.crawl('https://example.com')
  .then(result => console.log(result.markdown));
```

**With REST API:**
Any language with HTTP client support can use the API!

---

## Getting Help

### Resources

- 📖 [Full Documentation](https://docs.crawl4ai.com)
- 🐛 [Report Issues](https://github.com/unclecode/crawl4ai/issues)
- 💬 [Discord Community](https://discord.gg/crawl4ai)
- 📺 [Video Tutorials](https://youtube.com/@crawl4ai)

### Common Questions

**Q: How many replicas should I use?**
A: Start with 1 for development. Use 3-5 for production. Scale based on load.

**Q: What's the difference between Swarm and Compose mode?**
A: Swarm has built-in load balancing (faster). Compose uses Nginx (fallback if Swarm unavailable).

**Q: Can I run multiple cnode instances?**
A: Yes! Use different ports: `cnode start --port 8080`

**Q: How do I update to the latest version?**
A: Pull new image: `cnode stop && docker pull unclecode/crawl4ai:latest && cnode start`

---

## Summary

You now know how to:
- ✅ Install cnode with one command
- ✅ Start and manage Crawl4AI servers
- ✅ Scale from 1 to 100+ replicas
- ✅ Monitor performance in real-time
- ✅ Use the API from any language
- ✅ Troubleshoot common issues

**Ready to crawl at scale!** 🚀

For detailed Docker configuration and advanced deployment options, see the [Docker Guide](../docker/README.md).

---

**Happy Crawling!** 🕷️

*Made with ❤️ by the Crawl4AI team*

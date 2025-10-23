# Crawl4AI cnode - Quick Start Cheat Sheet

Fast reference for getting started with cnode.

---

## 📥 Install

```bash
# Install cnode
curl -sSL https://raw.githubusercontent.com/unclecode/crawl4ai/main/deploy/installer/install-cnode.sh | bash
```

---

## 🚀 Launch Cluster

```bash
# Single server (development)
cnode start

# Production cluster with 5 replicas
cnode start --replicas 5

# Custom port
cnode start --replicas 3 --port 8080
```

---

## 📊 Check Status

```bash
# View server status
cnode status

# View logs
cnode logs -f
```

---

## ⚙️ Scale Cluster

```bash
# Scale to 10 replicas (live, no downtime)
cnode scale 10

# Scale down to 2
cnode scale 2
```

---

## 🔄 Restart/Stop

```bash
# Restart server
cnode restart

# Stop server
cnode stop
```

---

## 🌐 Test the API

```bash
# Simple test - crawl example.com
curl -X POST http://localhost:11235/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "priority": 10
  }'

# Pretty print with jq
curl -X POST http://localhost:11235/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "priority": 10
  }' | jq '.result.markdown' -r

# Health check
curl http://localhost:11235/health
```

---

## 📱 Monitor Dashboard

```bash
# Open in browser
open http://localhost:11235/monitor

# Or playground
open http://localhost:11235/playground
```

---

## 🐍 Python Example

```python
import requests

response = requests.post(
    "http://localhost:11235/crawl",
    json={
        "urls": ["https://example.com"],
        "priority": 10
    }
)

result = response.json()
print(result['result']['markdown'])
```

---

## 🎯 Common Commands

| Command | Description |
|---------|-------------|
| `cnode start` | Start server |
| `cnode start -r 5` | Start with 5 replicas |
| `cnode status` | Check status |
| `cnode scale 10` | Scale to 10 replicas |
| `cnode logs -f` | Follow logs |
| `cnode restart` | Restart server |
| `cnode stop` | Stop server |
| `cnode --help` | Show all commands |

---

## 📚 Full Documentation

- **User Guide:** `deploy/installer/USER_GUIDE.md`
- **Developer Docs:** `deploy/installer/README.md`
- **Docker Guide:** `deploy/docker/README.md`
- **Agent Context:** `deploy/docker/AGENT.md`

---

**That's it!** You're ready to crawl at scale 🚀

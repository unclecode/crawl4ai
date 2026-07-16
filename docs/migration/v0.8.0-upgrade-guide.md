# Migration Guide: Upgrading to Crawl4AI v0.8.0

This guide helps you upgrade from v0.7.x to v0.8.0, with special attention to breaking changes and security updates.

## Quick Summary

| Change | Impact | Action Required |
|--------|--------|-----------------|
| Hooks disabled by default | Docker API users with hooks | Set `CRAWL4AI_HOOKS_ENABLED=true` |
| file:// URLs blocked | Docker API users reading local files | Use Python library directly |
| Security fixes | All Docker API users | Update immediately |

---

## Step 1: Update the Package

### PyPI Installation

```bash
pip install --upgrade crawl4ai
```

### Docker Installation

```bash
docker pull unclecode/crawl4ai:latest
# or
docker pull unclecode/crawl4ai:0.8.0
```

### From Source

```bash
git pull origin main
pip install -e .
```

---

## Step 2: Check for Breaking Changes

### Are You Affected?

**You ARE affected if you:**
- Use the Docker API deployment
- Use the `hooks` parameter in `/crawl` requests
- Use `file://` URLs via API endpoints

**You are NOT affected if you:**
- Only use Crawl4AI as a Python library
- Don't use hooks in your API calls
- Don't use `file://` URLs via the API

---

## Step 3: Migrate Hooks Usage

### Before v0.8.0

Hooks worked by default:

```bash
# This worked without any configuration
curl -X POST http://localhost:11235/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "hooks": {
      "code": {
        "on_page_context_created": "async def hook(page, context, **kwargs):\n    await context.add_cookies([...])\n    return page"
      }
    }
  }'
```

### After v0.8.0

You must explicitly enable hooks:

**Option A: Environment Variable (Recommended)**
```bash
# In your Docker run command or docker-compose.yml
export CRAWL4AI_HOOKS_ENABLED=true
```

```yaml
# docker-compose.yml
services:
  crawl4ai:
    image: unclecode/crawl4ai:0.8.0
    environment:
      - CRAWL4AI_HOOKS_ENABLED=true
```

**Option B: For Kubernetes**
```yaml
env:
  - name: CRAWL4AI_HOOKS_ENABLED
    value: "true"
```

### Security Warning

Only enable hooks if:
- You trust all users who can access the API
- The API is not exposed to the public internet
- You have other authentication/authorization in place

---

## Step 4: Migrate file:// URL Usage

### Before v0.8.0

```bash
# This worked via API
curl -X POST http://localhost:11235/execute_js \
  -d '{"url": "file:///var/data/page.html", "scripts": ["document.title"]}'
```

### After v0.8.0

**Option A: Use the Python Library Directly**

```python
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

async def process_local_file():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="file:///var/data/page.html",
            config=CrawlerRunConfig(js_code=["document.title"])
        )
        return result
```

**Option B: Use raw: Protocol for HTML Content**

If you have the HTML content, you can still use the API:

```bash
# Read file content and send as raw:
HTML_CONTENT=$(cat /var/data/page.html)
curl -X POST http://localhost:11235/html \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"raw:$HTML_CONTENT\"}"
```

**Option C: Create a Preprocessing Service**

```python
# preprocessing_service.py
from fastapi import FastAPI
from crawl4ai import AsyncWebCrawler

app = FastAPI()

@app.post("/process-local")
async def process_local(file_path: str):
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=f"file://{file_path}")
        return result.model_dump()
```

---

## Step 5: Review Security Configuration

### Recommended Production Settings

```yaml
# config.yml
security:
  enabled: true
  jwt_enabled: true
  https_redirect: true  # If behind HTTPS proxy
  trusted_hosts:
    - "your-domain.com"
    - "api.your-domain.com"
```

### Environment Variables

```bash
# Required for JWT authentication
export SECRET_KEY="your-secure-random-key-minimum-32-characters"

# Only if you need hooks
export CRAWL4AI_HOOKS_ENABLED=true
```

### Generate a Secure Secret Key

```python
import secrets
print(secrets.token_urlsafe(32))
```

---

## Step 6: Test Your Integration

### Quick Validation Script

```python
import asyncio
import aiohttp

async def test_upgrade():
    base_url = "http://localhost:11235"

    # Test 1: Basic crawl should work
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/crawl",
            json={"urls": ["https://example.com"]}
        ) as resp:
            assert resp.status == 200, "Basic crawl failed"
            print("✓ Basic crawl works")

    # Test 2: Hooks should be blocked (unless enabled)
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/crawl",
            json={
                "urls": ["https://example.com"],
                "hooks": {"code": {"on_page_context_created": "async def hook(page, context, **kwargs): return page"}}
            }
        ) as resp:
            if resp.status == 403:
                print("✓ Hooks correctly blocked (default)")
            elif resp.status == 200:
                print("! Hooks enabled - ensure this is intentional")

    # Test 3: file:// should be blocked
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/execute_js",
            json={"url": "file:///etc/passwd", "scripts": ["1"]}
        ) as resp:
            assert resp.status == 400, "file:// should be blocked"
            print("✓ file:// URLs correctly blocked")

asyncio.run(test_upgrade())
```

---

## Troubleshooting

### "Hooks are disabled" Error

**Symptom**: API returns 403 with "Hooks are disabled"

**Solution**: Set `CRAWL4AI_HOOKS_ENABLED=true` if you need hooks

### "URL must start with http://, https://" Error

**Symptom**: API returns 400 when using `file://` URLs

**Solution**: Use Python library directly or `raw:` protocol

### Authentication Errors After Enabling JWT

**Symptom**: API returns 401 Unauthorized

**Solution**:
1. Get a token: `POST /token` with your email
2. Include token in requests: `Authorization: Bearer <token>`

---

## Rollback Plan

If you need to rollback:

```bash
# PyPI
pip install crawl4ai==0.7.6

# Docker
docker pull unclecode/crawl4ai:0.7.6
```

**Warning**: Rolling back re-exposes the security vulnerabilities. Only do this temporarily while fixing integration issues.

---

## Getting Help

- **GitHub Issues**: [github.com/unclecode/crawl4ai/issues](https://github.com/unclecode/crawl4ai/issues)
- **Security Issues**: See [SECURITY.md](../../SECURITY.md)
- **Documentation**: [docs.crawl4ai.com](https://docs.crawl4ai.com)

---

## Changelog Reference

For complete list of changes, see:
- [Release Notes v0.8.0](../RELEASE_NOTES_v0.8.0.md)
- [CHANGELOG.md](../../CHANGELOG.md)

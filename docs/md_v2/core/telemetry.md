# Telemetry

Crawl4AI includes **opt-in telemetry** to help improve stability by capturing anonymous crash reports. No personal data or crawled content is ever collected.

!!! info "Privacy First"
    Telemetry is completely optional and respects your privacy. Only exception information is collected - no URLs, no personal data, no crawled content.

## Overview

- **Privacy-first**: Only exceptions and crashes are reported
- **Opt-in by default**: You control when telemetry is enabled (except in Docker where it's on by default)
- **No PII**: No URLs, request data, or personal information is collected
- **Provider-agnostic**: Currently uses Sentry, but designed to support multiple backends

## Installation

Telemetry requires the optional Sentry SDK:

```bash
# Install with telemetry support
pip install crawl4ai[telemetry]

# Or install Sentry SDK separately
pip install sentry-sdk>=2.0.0
```

## Environments

### 1. Python Library & CLI

On first exception, you'll see an interactive prompt:

```
🚨 Crawl4AI Error Detection
==============================================================
We noticed an error occurred. Help improve Crawl4AI by
sending anonymous crash reports?

[1] Yes, send this error only
[2] Yes, always send errors
[3] No, don't send

Your choice (1/2/3): 
```

Control via CLI:
```bash
# Enable telemetry
crwl telemetry enable
crwl telemetry enable --email you@example.com

# Disable telemetry
crwl telemetry disable

# Check status
crwl telemetry status
```

### 2. Docker / API Server

!!! warning "Default Enabled in Docker"
    Telemetry is **enabled by default** in Docker environments to help identify container-specific issues. This is different from the CLI where it's opt-in.

To disable:
```bash
# Via environment variable
docker run -e CRAWL4AI_TELEMETRY=0 ...

# In docker-compose.yml
environment:
  - CRAWL4AI_TELEMETRY=0
```

### 3. Jupyter / Google Colab

In notebooks, you'll see an interactive widget (if available) or a code snippet:

```python
import crawl4ai

# Enable telemetry
crawl4ai.telemetry.enable(email="you@example.com", always=True)

# Send only next error
crawl4ai.telemetry.enable(once=True)

# Disable telemetry
crawl4ai.telemetry.disable()

# Check status
crawl4ai.telemetry.status()
```

## Python API

### Basic Usage

```python
from crawl4ai import telemetry

# Enable/disable telemetry
telemetry.enable(email="optional@email.com", always=True)
telemetry.disable()

# Check current status
status = telemetry.status()
print(f"Telemetry enabled: {status['enabled']}")
print(f"Consent: {status['consent']}")
```

### Manual Exception Capture

```python
from crawl4ai.telemetry import capture_exception

try:
    # Your code here
    risky_operation()
except Exception as e:
    # Manually capture exception with context
    capture_exception(e, {
        'operation': 'custom_crawler',
        'url': 'https://example.com'  # Will be sanitized
    })
    raise
```

### Decorator Pattern

```python
from crawl4ai.telemetry import telemetry_decorator

@telemetry_decorator
def my_crawler_function():
    # Exceptions will be automatically captured
    pass
```

### Context Manager

```python
from crawl4ai.telemetry import telemetry_context

with telemetry_context("data_extraction"):
    # Any exceptions in this block will be captured
    result = extract_data(html)
```

## Configuration

Settings are stored in `~/.crawl4ai/config.json`:

```json
{
  "telemetry": {
    "consent": "always",
    "email": "user@example.com"
  }
}
```

Consent levels:
- `"not_set"` - No decision made yet
- `"denied"` - Telemetry disabled
- `"once"` - Send current error only
- `"always"` - Always send errors

## Environment Variables

- `CRAWL4AI_TELEMETRY=0` - Disable telemetry (overrides config)
- `CRAWL4AI_TELEMETRY_EMAIL=email@example.com` - Set email for follow-up
- `CRAWL4AI_SENTRY_DSN=https://...` - Override default DSN (for maintainers)

## What's Collected

### Collected ✅
- Exception type and traceback
- Crawl4AI version
- Python version
- Operating system
- Environment type (CLI, Docker, Jupyter)
- Optional email (if provided)

### NOT Collected ❌
- URLs being crawled
- HTML content
- Request/response data
- Cookies or authentication tokens
- IP addresses
- Any personally identifiable information

## Provider Architecture

Telemetry is designed to be provider-agnostic:

```python
from crawl4ai.telemetry.base import TelemetryProvider

class CustomProvider(TelemetryProvider):
    def send_exception(self, exc, context=None):
        # Your implementation
        pass
```

## FAQ

### Q: Can I completely disable telemetry?
A: Yes! Use `crwl telemetry disable` or set `CRAWL4AI_TELEMETRY=0`

### Q: Is telemetry required?
A: No, it's completely optional (except enabled by default in Docker)

### Q: What if I don't install sentry-sdk?
A: Telemetry will gracefully degrade to a no-op state

### Q: Can I see what's being sent?
A: Yes, check the source code in `crawl4ai/telemetry/`

### Q: How do I remove my email?
A: Delete `~/.crawl4ai/config.json` or edit it to remove the email field

## Privacy Commitment

1. **Transparency**: All telemetry code is open source
2. **Control**: You can enable/disable at any time
3. **Minimal**: Only crash data, no user content
4. **Secure**: Data transmitted over HTTPS to Sentry
5. **Anonymous**: No tracking or user identification

## Contributing

Help improve telemetry:
- Report issues with telemetry itself
- Suggest privacy improvements
- Add new provider backends

## Support

If you have concerns about telemetry:
- Open an issue on GitHub
- Email the maintainers
- Review the code in `crawl4ai/telemetry/`
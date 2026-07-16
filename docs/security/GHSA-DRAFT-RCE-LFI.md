# GitHub Security Advisory Draft

> **Instructions**: Copy this content to create security advisories at:
> https://github.com/unclecode/crawl4ai/security/advisories/new

---

## Advisory 1: Remote Code Execution via Hooks Parameter

### Title
Remote Code Execution in Docker API via Hooks Parameter

### Severity
Critical

### CVSS Score
10.0 (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H)

### CWE
CWE-94 (Improper Control of Generation of Code)

### Package
crawl4ai (Docker API deployment)

### Affected Versions
< 0.8.0

### Patched Versions
0.8.0

### Description

A critical remote code execution vulnerability exists in the Crawl4AI Docker API deployment. The `/crawl` endpoint accepts a `hooks` parameter containing Python code that is executed using `exec()`. The `__import__` builtin was included in the allowed builtins, allowing attackers to import arbitrary modules and execute system commands.

**Attack Vector:**
```json
POST /crawl
{
  "urls": ["https://example.com"],
  "hooks": {
    "code": {
      "on_page_context_created": "async def hook(page, context, **kwargs):\n    __import__('os').system('malicious_command')\n    return page"
    }
  }
}
```

### Impact

An unauthenticated attacker can:
- Execute arbitrary system commands
- Read/write files on the server
- Exfiltrate sensitive data (environment variables, API keys)
- Pivot to internal network services
- Completely compromise the server

### Mitigation

1. **Upgrade to v0.8.0** (recommended)
2. If unable to upgrade immediately:
   - Disable the Docker API
   - Block `/crawl` endpoint at network level
   - Add authentication to the API

### Fix Details

1. Removed `__import__` from `allowed_builtins` in `hook_manager.py`
2. Hooks disabled by default (`CRAWL4AI_HOOKS_ENABLED=false`)
3. Users must explicitly opt-in to enable hooks

### Credits

Discovered by Neo by ProjectDiscovery (https://projectdiscovery.io)

### References

- [Release Notes v0.8.0](https://github.com/unclecode/crawl4ai/blob/main/docs/RELEASE_NOTES_v0.8.0.md)
- [Migration Guide](https://github.com/unclecode/crawl4ai/blob/main/docs/migration/v0.8.0-upgrade-guide.md)

---

## Advisory 2: Local File Inclusion via file:// URLs

### Title
Local File Inclusion in Docker API via file:// URLs

### Severity
High

### CVSS Score
8.6 (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:N/A:N)

### CWE
CWE-22 (Improper Limitation of a Pathname to a Restricted Directory)

### Package
crawl4ai (Docker API deployment)

### Affected Versions
< 0.8.0

### Patched Versions
0.8.0

### Description

A local file inclusion vulnerability exists in the Crawl4AI Docker API. The `/execute_js`, `/screenshot`, `/pdf`, and `/html` endpoints accept `file://` URLs, allowing attackers to read arbitrary files from the server filesystem.

**Attack Vector:**
```json
POST /execute_js
{
  "url": "file:///etc/passwd",
  "scripts": ["document.body.innerText"]
}
```

### Impact

An unauthenticated attacker can:
- Read sensitive files (`/etc/passwd`, `/etc/shadow`, application configs)
- Access environment variables via `/proc/self/environ`
- Discover internal application structure
- Potentially read credentials and API keys

### Mitigation

1. **Upgrade to v0.8.0** (recommended)
2. If unable to upgrade immediately:
   - Disable the Docker API
   - Add authentication to the API
   - Use network-level filtering

### Fix Details

Added URL scheme validation to block:
- `file://` URLs
- `javascript:` URLs
- `data:` URLs
- Other non-HTTP schemes

Only `http://`, `https://`, and `raw:` URLs are now allowed.

### Credits

Discovered by Neo by ProjectDiscovery (https://projectdiscovery.io)

### References

- [Release Notes v0.8.0](https://github.com/unclecode/crawl4ai/blob/main/docs/RELEASE_NOTES_v0.8.0.md)
- [Migration Guide](https://github.com/unclecode/crawl4ai/blob/main/docs/migration/v0.8.0-upgrade-guide.md)

---

## Creating the Advisories on GitHub

1. Go to: https://github.com/unclecode/crawl4ai/security/advisories/new

2. Fill in the form for each advisory:
   - **Ecosystem**: PyPI
   - **Package name**: crawl4ai
   - **Affected versions**: < 0.8.0
   - **Patched versions**: 0.8.0
   - **Severity**: Critical (for RCE), High (for LFI)

3. After creating, GitHub will:
   - Assign a GHSA ID
   - Optionally request a CVE
   - Notify users who have security alerts enabled

4. Coordinate disclosure timing with the fix release

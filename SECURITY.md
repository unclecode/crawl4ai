# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.8.x   | :white_check_mark: |
| 0.7.x   | :x: (upgrade recommended) |
| < 0.7   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please report via one of these methods:

1. **GitHub Security Advisories (Preferred)**
   - Go to [Security Advisories](https://github.com/unclecode/crawl4ai/security/advisories)
   - Click "New draft security advisory"
   - Fill in the details

2. **Email**
   - Send details to: security@crawl4ai.com
   - Use subject: `[SECURITY] Brief description`
   - Include:
     - Description of the vulnerability
     - Steps to reproduce
     - Potential impact
     - Any suggested fixes

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Resolution Timeline**: Depends on severity
  - Critical: 24-72 hours
  - High: 7 days
  - Medium: 30 days
  - Low: 90 days

### Disclosure Policy

- We follow responsible disclosure practices
- We will coordinate with you on disclosure timing
- Credit will be given to reporters (unless anonymity is requested)
- We may request CVE assignment for significant vulnerabilities

## Security Best Practices for Users

### Docker API Deployment

If you're running the Crawl4AI Docker API in production:

1. **Enable Authentication**
   ```yaml
   # config.yml
   security:
     enabled: true
     jwt_enabled: true
   ```
   ```bash
   # Set a strong secret key
   export SECRET_KEY="your-secure-random-key-here"
   ```

2. **Hooks are Disabled by Default** (v0.8.0+)
   - Only enable if you trust all API users
   - Set `CRAWL4AI_HOOKS_ENABLED=true` only when necessary

3. **Network Security**
   - Run behind a reverse proxy (nginx, traefik)
   - Use HTTPS in production
   - Restrict access to trusted IPs if possible

4. **Container Security**
   - Run as non-root user (default in our container)
   - Use read-only filesystem where possible
   - Limit container resources

### Library Usage

When using Crawl4AI as a Python library:

1. **Validate URLs** before crawling untrusted input
2. **Sanitize extracted content** before using in other systems
3. **Be cautious with hooks** - they execute arbitrary code

## Known Security Issues

### Fixed in v0.8.0

| ID | Severity | Description | Fix |
|----|----------|-------------|-----|
| CVE-pending-1 | CRITICAL | RCE via hooks `__import__` | Removed from allowed builtins |
| CVE-pending-2 | HIGH | LFI via `file://` URLs | URL scheme validation added |

See [Security Advisory](https://github.com/unclecode/crawl4ai/security/advisories) for details.

## Security Features

### v0.8.0+

- **URL Scheme Validation**: Blocks `file://`, `javascript:`, `data:` URLs on API
- **Hooks Disabled by Default**: Opt-in via `CRAWL4AI_HOOKS_ENABLED=true`
- **Restricted Hook Builtins**: No `__import__`, `eval`, `exec`, `open`
- **JWT Authentication**: Optional but recommended for production
- **Rate Limiting**: Configurable request limits
- **Security Headers**: X-Frame-Options, CSP, HSTS when enabled

## Acknowledgments

We thank the following security researchers for responsibly disclosing vulnerabilities:

- **[Neo by ProjectDiscovery](https://projectdiscovery.io/blog/introducing-neo)** - RCE and LFI vulnerabilities (December 2025)

---

*Last updated: January 2026*

"""
Anti-bot detection heuristics for crawl results.

Examines HTTP status codes and HTML content patterns to determine
if a crawl was blocked by anti-bot protection.

Detection philosophy: false positives are cheap (the fallback mechanism
rescues them), false negatives are catastrophic (user gets garbage).
Err on the side of detection.

Detection is layered:
- HTTP 403/503 with HTML content → always blocked (these are never desired content)
- Tier 1 patterns (structural markers) trigger on any page size
- Tier 2 patterns (generic terms) trigger on short pages or any error status
- Tier 3 structural integrity catches silent blocks and empty shells
"""

import re
from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# Tier 1: High-confidence structural markers (single signal sufficient)
# These are unique to block pages and virtually never appear in real content.
# ---------------------------------------------------------------------------
_TIER1_PATTERNS = [
    # Akamai — full reference pattern: Reference #18.2d351ab8.1557333295.a4e16ab
    (re.compile(r"Reference\s*#\s*[\d]+\.[0-9a-f]+\.\d+\.[0-9a-f]+", re.IGNORECASE),
     "Akamai block (Reference #)"),
    # Akamai — "Pardon Our Interruption" challenge page
    (re.compile(r"Pardon\s+Our\s+Interruption", re.IGNORECASE),
     "Akamai challenge (Pardon Our Interruption)"),
    # Cloudflare — challenge form with anti-bot token
    (re.compile(r'challenge-form.*?__cf_chl_f_tk=', re.IGNORECASE | re.DOTALL),
     "Cloudflare challenge form"),
    # Cloudflare — error code spans (1020 Access Denied, 1010, 1012, 1015)
    (re.compile(r'<span\s+class="cf-error-code">\d{4}</span>', re.IGNORECASE),
     "Cloudflare firewall block"),
    # Cloudflare — IUAM challenge script
    (re.compile(r'/cdn-cgi/challenge-platform/\S+orchestrate', re.IGNORECASE),
     "Cloudflare JS challenge"),
    # PerimeterX / HUMAN — block page with app ID assignment (not prose mentions)
    (re.compile(r"window\._pxAppId\s*=", re.IGNORECASE),
     "PerimeterX block"),
    # PerimeterX — captcha CDN
    (re.compile(r"captcha\.px-cdn\.net", re.IGNORECASE),
     "PerimeterX captcha"),
    # DataDome — captcha delivery domain (structural, not the word "datadome")
    (re.compile(r"captcha-delivery\.com", re.IGNORECASE),
     "DataDome captcha"),
    # Imperva/Incapsula — resource iframe
    (re.compile(r"_Incapsula_Resource", re.IGNORECASE),
     "Imperva/Incapsula block"),
    # Imperva/Incapsula — incident ID
    (re.compile(r"Incapsula\s+incident\s+ID", re.IGNORECASE),
     "Imperva/Incapsula incident"),
    # Sucuri firewall
    (re.compile(r"Sucuri\s+WebSite\s+Firewall", re.IGNORECASE),
     "Sucuri firewall block"),
    # Kasada
    (re.compile(r"KPSDK\.scriptStart\s*=\s*KPSDK\.now\(\)", re.IGNORECASE),
     "Kasada challenge"),
    # Network security block — Reddit and other platforms serve large SPA shells
    # with this message buried under 100KB+ of CSS/JS
    (re.compile(r"blocked\s+by\s+network\s+security", re.IGNORECASE),
     "Network security block"),
]

# ---------------------------------------------------------------------------
# Tier 2: Medium-confidence patterns — only match on SHORT pages (< 10KB)
# These terms appear in real content (articles, login forms, security blogs)
# so we require the page to be small to avoid false positives.
# ---------------------------------------------------------------------------
_TIER2_PATTERNS = [
    # Akamai / generic — "Access Denied" (extremely common on legit 403s too)
    (re.compile(r"Access\s+Denied", re.IGNORECASE),
     "Access Denied on short page"),
    # Cloudflare — "Just a moment" / "Checking your browser"
    (re.compile(r"Checking\s+your\s+browser", re.IGNORECASE),
     "Cloudflare browser check"),
    (re.compile(r"<title>\s*Just\s+a\s+moment", re.IGNORECASE),
     "Cloudflare interstitial"),
    # CAPTCHA on a block page (not a login form — login forms are big pages)
    (re.compile(r'class=["\']g-recaptcha["\']', re.IGNORECASE),
     "reCAPTCHA on block page"),
    (re.compile(r'class=["\']h-captcha["\']', re.IGNORECASE),
     "hCaptcha on block page"),
    # PerimeterX block page title
    (re.compile(r"Access\s+to\s+This\s+Page\s+Has\s+Been\s+Blocked", re.IGNORECASE),
     "PerimeterX block page"),
    # Generic block phrases (only on short pages to avoid matching articles)
    (re.compile(r"blocked\s+by\s+security", re.IGNORECASE),
     "Blocked by security"),
    (re.compile(r"Request\s+unsuccessful", re.IGNORECASE),
     "Request unsuccessful (Imperva)"),
]

_TIER2_MAX_SIZE = 10000  # Only check tier 2 patterns on pages under 10KB

# ---------------------------------------------------------------------------
# Tier 3: Structural integrity — catches silent blocks, anti-bot redirects,
# incomplete renders that pass pattern detection but are structurally broken
# ---------------------------------------------------------------------------
_STRUCTURAL_MAX_SIZE = 50000  # Only check pages under 50KB
_CONTENT_ELEMENTS_RE = re.compile(
    r'<(?:p|h[1-6]|article|section|li|td|a|pre)\b', re.IGNORECASE
)
_SCRIPT_TAG_RE = re.compile(r'<script\b', re.IGNORECASE)
_STYLE_TAG_RE = re.compile(r'<style\b[\s\S]*?</style>', re.IGNORECASE)
_SCRIPT_BLOCK_RE = re.compile(r'<script\b[\s\S]*?</script>', re.IGNORECASE)
_TAG_RE = re.compile(r'<[^>]+>')
_BODY_RE = re.compile(r'<body\b', re.IGNORECASE)

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------
_BLOCK_PAGE_MAX_SIZE = 5000   # 403 + short page = likely block
_EMPTY_CONTENT_THRESHOLD = 100  # 200 + near-empty = JS-blocked render


def _looks_like_data(html: str) -> bool:
    """Check if content looks like a JSON/XML API response (not an HTML block page)."""
    stripped = html.strip()
    if not stripped:
        return False
    # Raw JSON/XML (not wrapped in HTML)
    if stripped[0] in ('{', '['):
        return True
    # Browser-rendered JSON: browsers wrap raw JSON in <html><body><pre>{...}</pre>
    if stripped[:10].lower().startswith(('<html', '<!')):
        if re.search(r'<body[^>]*>\s*<pre[^>]*>\s*[{\[]', stripped[:500], re.IGNORECASE):
            return True
        return False
    # Other XML-like content
    return stripped[0] == '<'


def _structural_integrity_check(html: str) -> Tuple[bool, str]:
    """
    Tier 3: Structural integrity check for pages that pass pattern detection
    but are structurally broken — incomplete renders, anti-bot redirects, empty shells.

    Only applies to pages < 50KB that aren't JSON/XML.

    Returns:
        Tuple of (is_blocked, reason).
    """
    html_len = len(html)

    # Skip large pages (unlikely to be block pages) and data responses
    if html_len > _STRUCTURAL_MAX_SIZE or _looks_like_data(html):
        return False, ""

    signals = []

    # Signal 1: No <body> tag — definitive structural failure
    if not _BODY_RE.search(html):
        return True, f"Structural: no <body> tag ({html_len} bytes)"

    # Signal 2: Minimal visible text after stripping scripts/styles/tags
    body_match = re.search(r'<body\b[^>]*>([\s\S]*)</body>', html, re.IGNORECASE)
    body_content = body_match.group(1) if body_match else html
    stripped = _SCRIPT_BLOCK_RE.sub('', body_content)
    stripped = _STYLE_TAG_RE.sub('', stripped)
    visible_text = _TAG_RE.sub('', stripped).strip()
    visible_len = len(visible_text)
    if visible_len < 50:
        signals.append("minimal_text")

    # Signal 3: No content elements (semantic HTML)
    content_elements = len(_CONTENT_ELEMENTS_RE.findall(html))
    if content_elements == 0:
        signals.append("no_content_elements")

    # Signal 4: Script-heavy shell — scripts present but no content
    script_count = len(_SCRIPT_TAG_RE.findall(html))
    if script_count > 0 and content_elements == 0 and visible_len < 100:
        signals.append("script_heavy_shell")

    # Scoring
    signal_count = len(signals)
    if signal_count >= 2:
        return True, f"Structural: {', '.join(signals)} ({html_len} bytes, {visible_len} chars visible)"

    if signal_count == 1 and html_len < 5000:
        return True, f"Structural: {signals[0]} on small page ({html_len} bytes, {visible_len} chars visible)"

    return False, ""


def is_blocked(
    status_code: Optional[int],
    html: str,
    error_message: Optional[str] = None,
) -> Tuple[bool, str]:
    """
    Detect if a crawl result indicates anti-bot blocking.

    Uses layered detection to maximize coverage while minimizing false positives:
    - Tier 1 patterns (structural markers) trigger on any page size
    - Tier 2 patterns (generic terms) only trigger on short pages (< 10KB)
    - Tier 3 structural integrity catches silent blocks and empty shells
    - Status-code checks require corroborating content signals

    Args:
        status_code: HTTP status code from the response.
        html: Raw HTML content from the response.
        error_message: Error message from the crawl result, if any.

    Returns:
        Tuple of (is_blocked, reason). reason is empty string when not blocked.
    """
    html = html or ""
    html_len = len(html)

    # --- HTTP 429 is always rate limiting ---
    if status_code == 429:
        return True, "HTTP 429 Too Many Requests"

    # --- Check for tier 1 patterns (high confidence, any page size) ---
    # First check the raw start of the page (fast path for small pages).
    # Then, for large pages, also check a stripped version (scripts/styles
    # removed) because modern block pages bury text under 100KB+ of CSS/JS.
    snippet = html[:15000]
    if snippet:
        for pattern, reason in _TIER1_PATTERNS:
            if pattern.search(snippet):
                return True, reason

    # Large-page deep scan: strip scripts/styles and re-check tier 1
    if html_len > 15000:
        _stripped_for_t1 = _SCRIPT_BLOCK_RE.sub('', html[:500000])
        _stripped_for_t1 = _STYLE_TAG_RE.sub('', _stripped_for_t1)
        _deep_snippet = _stripped_for_t1[:30000]
        for pattern, reason in _TIER1_PATTERNS:
            if pattern.search(_deep_snippet):
                return True, reason

    # --- HTTP 403/503 — always blocked for non-data HTML responses ---
    # Rationale: 403/503 are never the content the user wants. Modern block pages
    # (Reddit, LinkedIn, etc.) serve full SPA shells that exceed 100KB, so
    # size-based filtering misses them. Even for a legitimate auth error, the
    # fallback (Web Unlocker) will also get 403 and we correctly report failure.
    # False positives are cheap — the fallback mechanism rescues them.
    if status_code in (403, 503) and not _looks_like_data(html):
        if html_len < _EMPTY_CONTENT_THRESHOLD:
            return True, f"HTTP {status_code} with near-empty response ({html_len} bytes)"
        # For large pages, strip scripts/styles to find block text in the
        # actual content (Reddit hides it under 180KB of inline CSS).
        # Check tier 2 patterns regardless of page size.
        if html_len > _TIER2_MAX_SIZE:
            _stripped = _SCRIPT_BLOCK_RE.sub('', html[:500000])
            _stripped = _STYLE_TAG_RE.sub('', _stripped)
            _check_snippet = _stripped[:30000]
        else:
            _check_snippet = snippet
        for pattern, reason in _TIER2_PATTERNS:
            if pattern.search(_check_snippet):
                return True, f"{reason} (HTTP {status_code}, {html_len} bytes)"
        # Even without a pattern match, a non-data 403/503 HTML page is
        # almost certainly a block. Flag it so the fallback gets a chance.
        return True, f"HTTP {status_code} with HTML content ({html_len} bytes)"

    # --- Tier 2 patterns on other 4xx/5xx + short page ---
    if status_code and status_code >= 400 and html_len < _TIER2_MAX_SIZE:
        for pattern, reason in _TIER2_PATTERNS:
            if pattern.search(snippet):
                return True, f"{reason} (HTTP {status_code}, {html_len} bytes)"

    # --- HTTP 200 + near-empty content (JS-rendered empty page) ---
    if status_code == 200:
        stripped = html.strip()
        if len(stripped) < _EMPTY_CONTENT_THRESHOLD and not _looks_like_data(html):
            return True, f"Near-empty content ({len(stripped)} bytes) with HTTP 200"

    # --- Tier 3: Structural integrity (catches silent blocks, redirects, incomplete renders) ---
    _blocked, _reason = _structural_integrity_check(html)
    if _blocked:
        return True, _reason

    return False, ""

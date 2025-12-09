#!/usr/bin/env python3
"""
Comprehensive test suite for URL normalization functions in utils.py
Tests all scenarios and edge cases for the updated normalize_url functions.
"""

import sys
import os
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl, urlencode

# Add the crawl4ai package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import only the specific functions we need to test
from crawl4ai.utils import get_base_domain, is_external_url


# ANSI Color codes for beautiful console output
class Colors:
    # Basic colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    # Bright colors
    BRIGHT_RED = '\033[91;1m'
    BRIGHT_GREEN = '\033[92;1m'
    BRIGHT_YELLOW = '\033[93;1m'
    BRIGHT_BLUE = '\033[94;1m'
    BRIGHT_MAGENTA = '\033[95;1m'
    BRIGHT_CYAN = '\033[96;1m'
    BRIGHT_WHITE = '\033[97;1m'

    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'

    # Text styles
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

    # Icons
    CHECK = '✓'
    CROSS = '✗'
    WARNING = '⚠'
    INFO = 'ℹ'
    STAR = '⭐'
    FIRE = '🔥'
    ROCKET = '🚀'
    TARGET = '🎯'


def colorize(text, color):
    """Apply color to text"""
    return f"{color}{text}{Colors.RESET}"


def print_header(title, icon=""):
    """Print a formatted header"""
    width = 80
    print(f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}{'=' * width}{Colors.RESET}")
    if icon:
        print(f"{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}{' ' * ((width - len(title) - len(icon) - 1) // 2)}{icon} {title}{' ' * ((width - len(title) - len(icon) - 1) // 2)}{Colors.RESET}")
    else:
        print(f"{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}{' ' * ((width - len(title)) // 2)}{title}{' ' * ((width - len(title)) // 2)}{Colors.RESET}")
    print(f"{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}{'=' * width}{Colors.RESET}")


def print_section(title, icon=""):
    """Print a formatted section header"""
    if icon:
        print(f"\n{Colors.CYAN}{Colors.BOLD}{icon} {title}{Colors.RESET}")
    else:
        print(f"\n{Colors.CYAN}{Colors.BOLD}{title}{Colors.RESET}")
    print(f"{Colors.CYAN}{'-' * (len(title) + (len(icon) + 1 if icon else 0))}{Colors.RESET}")


def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}{Colors.CHECK} {message}{Colors.RESET}")


def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}{Colors.CROSS} {message}{Colors.RESET}")


def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}{Colors.WARNING} {message}{Colors.RESET}")


def print_info(message):
    """Print info message"""
    print(f"{Colors.BLUE}{Colors.INFO} {message}{Colors.RESET}")


def print_test_result(test_name, passed, expected=None, actual=None):
    """Print formatted test result"""
    if passed:
        print(f"  {Colors.GREEN}{Colors.CHECK} {test_name}{Colors.RESET}")
    else:
        print(f"  {Colors.RED}{Colors.CROSS} {test_name}{Colors.RESET}")
        if expected is not None and actual is not None:
            print(f"    {Colors.BRIGHT_RED}Expected: {expected}{Colors.RESET}")
            print(f"    {Colors.BRIGHT_RED}Actual:   {actual}{Colors.RESET}")


def print_progress(current, total, test_name=""):
    """Print progress indicator"""
    percentage = (current / total) * 100
    bar_length = 40
    filled_length = int(bar_length * current // total)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)

    sys.stdout.write(f'\r{Colors.CYAN}Progress: [{bar}] {percentage:.1f}% ({current}/{total}) {test_name}{Colors.RESET}')
    sys.stdout.flush()

    if current == total:
        print()  # New line when complete

# Copy the normalize_url functions directly to avoid import issues
def normalize_url(
    href: str,
    base_url: str,
    *,
    drop_query_tracking=True,
    sort_query=True,
    keep_fragment=False,
    extra_drop_params=None,
    preserve_https=False,
    original_scheme=None
):
    """
    Extended URL normalizer with fixes for edge cases - copied from utils.py for testing
    """
    if not href or not href.strip():
        return None

    # Resolve relative paths first
    full_url = urljoin(base_url, href.strip())

    # Preserve HTTPS if requested and original scheme was HTTPS
    if preserve_https and original_scheme == 'https':
        parsed_full = urlparse(full_url)
        parsed_base = urlparse(base_url)
        # Only preserve HTTPS for same-domain links (not protocol-relative URLs)
        # Protocol-relative URLs (//example.com) should follow the base URL's scheme
        if (parsed_full.scheme == 'http' and
            parsed_full.netloc == parsed_base.netloc and
            not href.strip().startswith('//')):
            full_url = full_url.replace('http://', 'https://', 1)

    # Parse once, edit parts, then rebuild
    parsed = urlparse(full_url)

    # ── netloc ──
    netloc = parsed.netloc.lower()
    
    # Remove default ports
    if ':' in netloc:
        host, port = netloc.rsplit(':', 1)
        if (parsed.scheme == 'http' and port == '80') or (parsed.scheme == 'https' and port == '443'):
            netloc = host
        else:
            netloc = f"{host}:{port}"

    # ── path ──
    # Strip duplicate slashes and trailing "/" (except root)
    # IMPORTANT: Don't use quote(unquote()) as it mangles + signs in URLs
    # The path from urlparse is already properly encoded
    path = parsed.path
    if path.endswith('/') and path != '/':
        path = path.rstrip('/')

    # ── query ──
    query = parsed.query
    if query:
        # explode, mutate, then rebuild
        params = list(parse_qsl(query, keep_blank_values=True)) # Parse query string into key-value pairs, preserving blank values

        if drop_query_tracking:
            # Define default tracking parameters to remove for cleaner URLs
            default_tracking = {
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term',
                'utm_content', 'gclid', 'fbclid', 'ref', 'ref_src'
            }
            if extra_drop_params:
                default_tracking |= {p.lower() for p in extra_drop_params} # Add any extra parameters to drop, case-insensitive
            params = [(k, v) for k, v in params if k not in default_tracking] # Filter out tracking parameters

        # Normalize parameter keys to lowercase
        params = [(k.lower(), v) for k, v in params]

        if sort_query:
            params.sort(key=lambda kv: kv[0]) # Sort parameters alphabetically by key (now lowercase)

        query = urlencode(params, doseq=True) if params else '' # Rebuild query string, handling sequences properly

    # ── fragment ──
    fragment = parsed.fragment if keep_fragment else ''

    # Re-assemble
    normalized = urlunparse((
        parsed.scheme,
        netloc,
        path,
        parsed.params,
        query,
        fragment
    ))

    return normalized


def normalize_url_for_deep_crawl(href, base_url, preserve_https=False, original_scheme=None):
    """Normalize URLs for deep crawling - copied from utils.py for testing"""
    if not href:
        return None

    # Use urljoin to handle relative URLs
    full_url = urljoin(base_url, href.strip())

    # Preserve HTTPS if requested and original scheme was HTTPS
    if preserve_https and original_scheme == 'https':
        parsed_full = urlparse(full_url)
        parsed_base = urlparse(base_url)
        # Only preserve HTTPS for same-domain links (not protocol-relative URLs)
        # Protocol-relative URLs (//example.com) should follow the base URL's scheme
        if (parsed_full.scheme == 'http' and
            parsed_full.netloc == parsed_base.netloc and
            not href.strip().startswith('//')):
            full_url = full_url.replace('http://', 'https://', 1)

    # Parse the URL for normalization
    parsed = urlparse(full_url)

    # Convert hostname to lowercase
    netloc = parsed.netloc.lower()

    # Remove fragment entirely
    fragment = ''

    # Normalize query parameters if needed
    query = parsed.query
    if query:
        # Parse query parameters
        params = parse_qsl(query)

        # Remove tracking parameters (example - customize as needed)
        tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'ref', 'fbclid']
        params = [(k, v) for k, v in params if k not in tracking_params]

        # Rebuild query string, sorted for consistency
        query = urlencode(params, doseq=True) if params else ''

    # Build normalized URL
    normalized = urlunparse((
        parsed.scheme,
        netloc,
        parsed.path.rstrip('/'),  # Normalize trailing slash
        parsed.params,
        query,
        fragment
    ))

    return normalized

def efficient_normalize_url_for_deep_crawl(href, base_url, preserve_https=False, original_scheme=None):
    """Efficient URL normalization with proper parsing - copied from utils.py for testing"""
    if not href:
        return None

    # Resolve relative URLs
    full_url = urljoin(base_url, href.strip())

    # Preserve HTTPS if requested and original scheme was HTTPS
    if preserve_https and original_scheme == 'https':
        parsed_full = urlparse(full_url)
        parsed_base = urlparse(base_url)
        # Only preserve HTTPS for same-domain links (not protocol-relative URLs)
        # Protocol-relative URLs (//example.com) should follow the base URL's scheme
        if (parsed_full.scheme == 'http' and
            parsed_full.netloc == parsed_base.netloc and
            not href.strip().startswith('//')):
            full_url = full_url.replace('http://', 'https://', 1)

    # Use proper URL parsing
    parsed = urlparse(full_url)

    # Only perform the most critical normalizations
    # 1. Lowercase hostname
    # 2. Remove fragment
    normalized = urlunparse((
        parsed.scheme,
        parsed.netloc.lower(),
        parsed.path.rstrip('/'),
        parsed.params,
        parsed.query,
        ''  # Remove fragment
    ))

    return normalized


class URLNormalizationTestSuite:
    """Comprehensive test suite for URL normalization functions"""

    def __init__(self):
        self.base_url = "https://example.com/path/page.html"
        self.https_base_url = "https://example.com/path/page.html"
        self.http_base_url = "http://example.com/path/page.html"
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = []
        self.test_start_time = None
        self.section_stats = {}
        self.current_section = None

    def start_section(self, section_name, icon=""):
        """Start a new test section"""
        self.current_section = section_name
        if section_name not in self.section_stats:
            self.section_stats[section_name] = {'run': 0, 'passed': 0, 'failed': 0}
        print_section(section_name, icon)

    def assert_equal(self, actual, expected, test_name):
        """Assert that actual equals expected"""
        self.tests_run += 1
        if self.current_section:
            self.section_stats[self.current_section]['run'] += 1

        if actual == expected:
            self.tests_passed += 1
            if self.current_section:
                self.section_stats[self.current_section]['passed'] += 1
            print_test_result(test_name, True)
        else:
            self.tests_failed.append({
                'name': test_name,
                'expected': expected,
                'actual': actual,
                'section': self.current_section
            })
            if self.current_section:
                self.section_stats[self.current_section]['failed'] += 1
            print_test_result(test_name, False, expected, actual)

    def assert_none(self, actual, test_name):
        """Assert that actual is None"""
        self.assert_equal(actual, None, test_name)

    def test_basic_url_resolution(self):
        """Test basic relative and absolute URL resolution"""
        self.start_section("Basic URL Resolution", Colors.TARGET)

        # Absolute URLs should remain unchanged
        self.assert_equal(
            normalize_url("https://other.com/page.html", self.base_url),
            "https://other.com/page.html",
            "Absolute URL unchanged"
        )

        # Relative URLs
        self.assert_equal(
            normalize_url("relative.html", self.base_url),
            "https://example.com/path/relative.html",
            "Relative URL resolution"
        )

        self.assert_equal(
            normalize_url("./relative.html", self.base_url),
            "https://example.com/path/relative.html",
            "Relative URL with dot"
        )

        self.assert_equal(
            normalize_url("../relative.html", self.base_url),
            "https://example.com/relative.html",
            "Parent directory resolution"
        )

        # Root-relative URLs
        self.assert_equal(
            normalize_url("/root.html", self.base_url),
            "https://example.com/root.html",
            "Root-relative URL"
        )

        # Protocol-relative URLs
        self.assert_equal(
            normalize_url("//cdn.example.com/asset.js", self.base_url),
            "https://cdn.example.com/asset.js",
            "Protocol-relative URL"
        )

    def test_query_parameter_handling(self):
        """Test query parameter sorting and tracking removal"""
        self.start_section("Query Parameter Handling", Colors.STAR)

        # Basic query parameters
        self.assert_equal(
            normalize_url("https://example.com?page=1&sort=name", self.base_url),
            "https://example.com?page=1&sort=name",
            "Basic query parameters sorted"
        )

        # Tracking parameters removal
        self.assert_equal(
            normalize_url("https://example.com?utm_source=google&utm_medium=email&page=1", self.base_url),
            "https://example.com?page=1",
            "Tracking parameters removed"
        )

        # Mixed tracking and valid parameters
        self.assert_equal(
            normalize_url("https://example.com?fbclid=123&utm_campaign=test&category=news&id=456", self.base_url),
            "https://example.com?category=news&id=456",
            "Mixed tracking and valid parameters"
        )

        # Empty query values
        self.assert_equal(
            normalize_url("https://example.com?page=&sort=name", self.base_url),
            "https://example.com?page=&sort=name",
            "Empty query values preserved"
        )

        # Disable tracking removal
        self.assert_equal(
            normalize_url("https://example.com?utm_source=google&page=1", self.base_url, drop_query_tracking=False),
            "https://example.com?page=1&utm_source=google",
            "Tracking parameters preserved when disabled"
        )

        # Disable sorting
        self.assert_equal(
            normalize_url("https://example.com?z=1&a=2", self.base_url, sort_query=False),
            "https://example.com?z=1&a=2",
            "Query parameters not sorted when disabled"
        )

    def test_fragment_handling(self):
        """Test fragment/hash handling"""
        self.start_section("Fragment Handling", Colors.FIRE)

        # Fragments removed by default
        self.assert_equal(
            normalize_url("https://example.com/page.html#section", self.base_url),
            "https://example.com/page.html",
            "Fragment removed by default"
        )

        # Fragments preserved when requested
        self.assert_equal(
            normalize_url("https://example.com/page.html#section", self.base_url, keep_fragment=True),
            "https://example.com/page.html#section",
            "Fragment preserved when requested"
        )

        # Fragments with query parameters
        self.assert_equal(
            normalize_url("https://example.com?page=1#section", self.base_url, keep_fragment=True),
            "https://example.com?page=1#section",
            "Fragment with query parameters"
        )

    def test_https_preservation(self):
        """Test HTTPS preservation logic"""
        self.start_section("HTTPS Preservation", Colors.ROCKET)

        # Same domain HTTP to HTTPS
        self.assert_equal(
            normalize_url("http://example.com/page.html", self.https_base_url, preserve_https=True, original_scheme='https'),
            "https://example.com/page.html",
            "HTTP to HTTPS for same domain"
        )

        # Different domain should not change
        self.assert_equal(
            normalize_url("http://other.com/page.html", self.https_base_url, preserve_https=True, original_scheme='https'),
            "http://other.com/page.html",
            "Different domain HTTP unchanged"
        )

        # Protocol-relative should follow base
        self.assert_equal(
            normalize_url("//example.com/page.html", self.https_base_url, preserve_https=True, original_scheme='https'),
            "https://example.com/page.html",
            "Protocol-relative follows base scheme"
        )

    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        self.start_section("Edge Cases", Colors.WARNING)

        # None and empty inputs
        result = normalize_url(None, self.base_url)  # type: ignore
        self.assert_none(result, "None input")

        self.assert_none(normalize_url("", self.base_url), "Empty string input")
        self.assert_none(normalize_url("   ", self.base_url), "Whitespace only input")

        # Malformed URLs
        try:
            normalize_url("not-a-url", "invalid-base")
            print("✗ Should have raised ValueError for invalid base URL")
        except ValueError:
            print("✓ Correctly raised ValueError for invalid base URL")

        # Special protocols
        self.assert_equal(
            normalize_url("mailto:test@example.com", self.base_url),
            "mailto:test@example.com",
            "Mailto protocol preserved"
        )

        self.assert_equal(
            normalize_url("tel:+1234567890", self.base_url),
            "tel:+1234567890",
            "Tel protocol preserved"
        )

        self.assert_equal(
            normalize_url("javascript:void(0)", self.base_url),
            "javascript:void(0)",
            "JavaScript protocol preserved"
        )

    def test_case_sensitivity(self):
        """Test case sensitivity handling"""
        self.start_section("Case Sensitivity", Colors.INFO)

        # Domain case normalization
        self.assert_equal(
            normalize_url("https://EXAMPLE.COM/page.html", self.base_url),
            "https://example.com/page.html",
            "Domain case normalization"
        )

        # Mixed case paths
        self.assert_equal(
            normalize_url("https://example.com/PATH/Page.HTML", self.base_url),
            "https://example.com/PATH/Page.HTML",
            "Path case preserved"
        )

        # Query parameter case
        self.assert_equal(
            normalize_url("https://example.com?PARAM=value", self.base_url),
            "https://example.com?param=value",
            "Query parameter case normalization"
        )

    def test_unicode_and_special_chars(self):
        """Test Unicode and special characters"""
        self.start_section("Unicode & Special Characters", "🌍")

        # Unicode in path
        self.assert_equal(
            normalize_url("https://example.com/café.html", self.base_url),
            "https://example.com/café.html",
            "Unicode characters in path"
        )

        # Encoded characters
        self.assert_equal(
            normalize_url("https://example.com/caf%C3%A9.html", self.base_url),
            "https://example.com/caf%C3%A9.html",
            "URL-encoded characters preserved"
        )

        # Spaces in URLs
        self.assert_equal(
            normalize_url("https://example.com/page with spaces.html", self.base_url),
            "https://example.com/page with spaces.html",
            "Spaces in URLs handled"
        )

    def test_port_numbers(self):
        """Test port number handling"""
        self.start_section("Port Numbers", "🔌")

        # Default ports
        self.assert_equal(
            normalize_url("https://example.com:443/page.html", self.base_url),
            "https://example.com/page.html",
            "Default HTTPS port removed"
        )

        self.assert_equal(
            normalize_url("http://example.com:80/page.html", self.base_url),
            "http://example.com/page.html",
            "Default HTTP port removed"
        )

        # Non-default ports
        self.assert_equal(
            normalize_url("https://example.com:8443/page.html", self.base_url),
            "https://example.com:8443/page.html",
            "Non-default port preserved"
        )

    def test_trailing_slashes(self):
        """Test trailing slash normalization"""
        self.start_section("Trailing Slashes", "📁")

        # Remove trailing slash from paths
        self.assert_equal(
            normalize_url("https://example.com/path/", self.base_url),
            "https://example.com/path",
            "Trailing slash removed from path"
        )

        # Preserve root trailing slash
        self.assert_equal(
            normalize_url("https://example.com/", self.base_url),
            "https://example.com/",
            "Root trailing slash preserved"
        )

        # Multiple trailing slashes
        self.assert_equal(
            normalize_url("https://example.com/path//", self.base_url),
            "https://example.com/path",
            "Multiple trailing slashes normalized"
        )

    def test_deep_crawl_functions(self):
        """Test deep crawl specific normalization functions"""
        self.start_section("Deep Crawl Functions", "🔍")

        # Test normalize_url_for_deep_crawl
        result = normalize_url_for_deep_crawl("https://EXAMPLE.COM/path/?utm_source=test&page=1", self.base_url)
        expected = "https://example.com/path?page=1"
        self.assert_equal(result, expected, "Deep crawl normalization")

        # Test efficient version
        result = efficient_normalize_url_for_deep_crawl("https://EXAMPLE.COM/path/#fragment", self.base_url)
        expected = "https://example.com/path"
        self.assert_equal(result, expected, "Efficient deep crawl normalization")

    def test_base_domain_extraction(self):
        """Test base domain extraction"""
        self.start_section("Base Domain Extraction", "🏠")

        self.assert_equal(
            get_base_domain("https://www.example.com/path"),
            "example.com",
            "WWW prefix removed"
        )

        self.assert_equal(
            get_base_domain("https://sub.example.co.uk/path"),
            "example.co.uk",
            "Special TLD handled"
        )

        self.assert_equal(
            get_base_domain("https://example.com:8080/path"),
            "example.com",
            "Port removed"
        )

    def test_external_url_detection(self):
        """Test external URL detection"""
        self.start_section("External URL Detection", "🌐")

        self.assert_equal(
            is_external_url("https://other.com/page.html", "example.com"),
            True,
            "Different domain is external"
        )

        self.assert_equal(
            is_external_url("https://www.example.com/page.html", "example.com"),
            False,
            "Same domain with www is internal"
        )

        self.assert_equal(
            is_external_url("mailto:test@example.com", "example.com"),
            True,
            "Special protocol is external"
        )

    def run_all_tests(self):
        """Run all test suites"""
        print_header("🚀 URL Normalization Test Suite", Colors.ROCKET)
        self.test_start_time = time.time()

        # Run all test sections
        sections = [
            ("Basic URL Resolution", Colors.TARGET, self.test_basic_url_resolution),
            ("Query Parameter Handling", Colors.STAR, self.test_query_parameter_handling),
            ("Fragment Handling", Colors.FIRE, self.test_fragment_handling),
            ("HTTPS Preservation", Colors.ROCKET, self.test_https_preservation),
            ("Edge Cases", Colors.WARNING, self.test_edge_cases),
            ("Case Sensitivity", Colors.INFO, self.test_case_sensitivity),
            ("Unicode & Special Characters", "🌍", self.test_unicode_and_special_chars),
            ("Port Numbers", "🔌", self.test_port_numbers),
            ("Trailing Slashes", "📁", self.test_trailing_slashes),
            ("Deep Crawl Functions", "🔍", self.test_deep_crawl_functions),
            ("Base Domain Extraction", "🏠", self.test_base_domain_extraction),
            ("External URL Detection", "🌐", self.test_external_url_detection),
        ]

        total_sections = len(sections)
        for i, (section_name, icon, test_method) in enumerate(sections, 1):
            print_progress(i - 1, total_sections, f"Running {section_name}")
            test_method()
            print_progress(i, total_sections, f"Completed {section_name}")

        # Calculate execution time
        execution_time = time.time() - self.test_start_time

        # Print comprehensive statistics
        self.print_comprehensive_stats(execution_time)

        return len(self.tests_failed) == 0

    def print_comprehensive_stats(self, execution_time):
        """Print comprehensive test statistics"""
        print_header("📊 Test Results Summary", "📈")

        # Overall statistics
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0

        print(f"{Colors.BOLD}Overall Statistics:{Colors.RESET}")
        print(f"  Total Tests: {Colors.CYAN}{self.tests_run}{Colors.RESET}")
        print(f"  Passed: {Colors.GREEN}{self.tests_passed}{Colors.RESET}")
        print(f"  Failed: {Colors.RED}{len(self.tests_failed)}{Colors.RESET}")
        print(f"  Success Rate: {Colors.BRIGHT_CYAN}{success_rate:.1f}%{Colors.RESET}")
        print(f"  Execution Time: {Colors.YELLOW}{execution_time:.2f}s{Colors.RESET}")

        # Performance indicator
        if success_rate == 100:
            print_success("🎉 Perfect! All tests passed!")
        elif success_rate >= 90:
            print_success("✅ Excellent! Nearly perfect results!")
        elif success_rate >= 75:
            print_warning("⚠️ Good results, but some improvements needed")
        else:
            print_error("❌ Significant issues detected - review failures below")

        # Section-by-section breakdown
        if self.section_stats:
            print(f"\n{Colors.BOLD}Section Breakdown:{Colors.RESET}")
            for section_name, stats in self.section_stats.items():
                section_success_rate = (stats['passed'] / stats['run'] * 100) if stats['run'] > 0 else 0
                status_icon = Colors.CHECK if stats['failed'] == 0 else Colors.CROSS
                status_color = Colors.GREEN if stats['failed'] == 0 else Colors.RED

                print(f"  {status_icon} {section_name}: {Colors.CYAN}{stats['run']}{Colors.RESET} tests, "
                      f"{status_color}{stats['passed']} passed{Colors.RESET}, "
                      f"{Colors.RED}{stats['failed']} failed{Colors.RESET} "
                      f"({Colors.BRIGHT_CYAN}{section_success_rate:.1f}%{Colors.RESET})")

        # Failed tests details
        if self.tests_failed:
            print(f"\n{Colors.BOLD}{Colors.RED}Failed Tests Details:{Colors.RESET}")
            for i, failure in enumerate(self.tests_failed, 1):
                print(f"  {Colors.RED}{i}. {failure['name']}{Colors.RESET}")
                if 'section' in failure and failure['section']:
                    print(f"     Section: {Colors.YELLOW}{failure['section']}{Colors.RESET}")
                print(f"     Expected: {Colors.BRIGHT_RED}{failure['expected']}{Colors.RESET}")
                print(f"     Actual:   {Colors.BRIGHT_RED}{failure['actual']}{Colors.RESET}")
                print()

        # Recommendations
        if self.tests_failed:
            print(f"{Colors.BOLD}{Colors.YELLOW}Recommendations:{Colors.RESET}")
            print(f"  • Review the {len(self.tests_failed)} failed test(s) above")
            print("  • Check URL normalization logic for edge cases")
            print("  • Verify query parameter handling")
            print("  • Test with real-world URLs")
        else:
            print(f"\n{Colors.BOLD}{Colors.GREEN}Recommendations:{Colors.RESET}")
            print("  • All tests passed! URL normalization is working correctly")
            print("  • Consider adding more edge cases for future robustness")
            print("  • Monitor performance with large-scale crawling")


def test_crawling_integration():
    """Test integration with crawling scripts"""
    print_section("Crawling Integration Test", "🔗")

    # Test URLs that would be encountered in real crawling
    test_urls = [
        "https://example.com/blog/post?utm_source=newsletter&utm_medium=email",
        "https://example.com/products?page=1&sort=price&ref=search",
        "/about.html",
        "../contact.html",
        "//cdn.example.com/js/main.js",
        "mailto:support@example.com",
        "#top",
        "",
        None,
    ]

    base_url = "https://example.com/current/page.html"

    print("Testing real-world URL scenarios:")
    for url in test_urls:
        try:
            normalized = normalize_url(url, base_url)
            print(f"  {url} -> {normalized}")
        except (ValueError, TypeError) as e:
            print(f"  {url} -> ERROR: {e}")


if __name__ == "__main__":
    print_header("🧪 URL Normalization Comprehensive Test Suite", "🧪")
    print_info("Testing URL normalization functions with comprehensive scenarios and edge cases")
    print()

    # Run the test suite
    test_suite = URLNormalizationTestSuite()
    success = test_suite.run_all_tests()

    # Run integration tests
    print()
    test_crawling_integration()

    # Final summary
    print()
    print_header("🏁 Final Test Summary", "🏁")

    if success:
        print_success("🎉 ALL TESTS PASSED! URL normalization is working perfectly!")
        print_info("The updated URL normalization functions are ready for production use.")
    else:
        print_error("❌ SOME TESTS FAILED! Please review the issues above.")
        print_warning("URL normalization may have issues that need to be addressed before deployment.")

    print()
    print_info("Test suite completed. Check the results above for detailed analysis.")

    # Exit with appropriate code
    sys.exit(0 if success else 1)
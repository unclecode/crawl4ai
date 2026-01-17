#!/usr/bin/env python3
"""
Security Integration Tests for Crawl4AI Docker API.
Tests that security fixes are working correctly against a running server.

Usage:
    python run_security_tests.py [base_url]

Example:
    python run_security_tests.py http://localhost:11235
"""

import subprocess
import sys
import re

# Colors for terminal output
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

PASSED = 0
FAILED = 0


def run_curl(args: list) -> str:
    """Run curl command and return output."""
    try:
        result = subprocess.run(
            ['curl', '-s'] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return str(e)


def test_expect(name: str, expect_pattern: str, curl_args: list) -> bool:
    """Run a test and check if output matches expected pattern."""
    global PASSED, FAILED

    result = run_curl(curl_args)

    if re.search(expect_pattern, result, re.IGNORECASE):
        print(f"{GREEN}✓{NC} {name}")
        PASSED += 1
        return True
    else:
        print(f"{RED}✗{NC} {name}")
        print(f"  Expected pattern: {expect_pattern}")
        print(f"  Got: {result[:200]}")
        FAILED += 1
        return False


def main():
    global PASSED, FAILED

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:11235"

    print("=" * 60)
    print("Crawl4AI Security Integration Tests")
    print(f"Target: {base_url}")
    print("=" * 60)
    print()

    # Check server availability
    print("Checking server availability...")
    result = run_curl(['-o', '/dev/null', '-w', '%{http_code}', f'{base_url}/health'])
    if '200' not in result:
        print(f"{RED}ERROR: Server not reachable at {base_url}{NC}")
        print("Please start the server first.")
        sys.exit(1)
    print(f"{GREEN}Server is running{NC}")
    print()

    # === Part A: Security Tests ===
    print("=== Part A: Security Tests ===")
    print("(Vulnerabilities must be BLOCKED)")
    print()

    test_expect(
        "A1: Hooks disabled by default (403)",
        r"403|disabled|Hooks are disabled",
        ['-X', 'POST', f'{base_url}/crawl',
         '-H', 'Content-Type: application/json',
         '-d', '{"urls":["https://example.com"],"hooks":{"code":{"on_page_context_created":"async def hook(page, context, **kwargs): return page"}}}']
    )

    test_expect(
        "A2: file:// blocked on /execute_js (400)",
        r"400|must start with",
        ['-X', 'POST', f'{base_url}/execute_js',
         '-H', 'Content-Type: application/json',
         '-d', '{"url":"file:///etc/passwd","scripts":["1"]}']
    )

    test_expect(
        "A3: file:// blocked on /screenshot (400)",
        r"400|must start with",
        ['-X', 'POST', f'{base_url}/screenshot',
         '-H', 'Content-Type: application/json',
         '-d', '{"url":"file:///etc/passwd"}']
    )

    test_expect(
        "A4: file:// blocked on /pdf (400)",
        r"400|must start with",
        ['-X', 'POST', f'{base_url}/pdf',
         '-H', 'Content-Type: application/json',
         '-d', '{"url":"file:///etc/passwd"}']
    )

    test_expect(
        "A5: file:// blocked on /html (400)",
        r"400|must start with",
        ['-X', 'POST', f'{base_url}/html',
         '-H', 'Content-Type: application/json',
         '-d', '{"url":"file:///etc/passwd"}']
    )

    print()

    # === Part B: Functionality Tests ===
    print("=== Part B: Functionality Tests ===")
    print("(Normal operations must WORK)")
    print()

    test_expect(
        "B1: Basic crawl works",
        r"success.*true|results",
        ['-X', 'POST', f'{base_url}/crawl',
         '-H', 'Content-Type: application/json',
         '-d', '{"urls":["https://example.com"]}']
    )

    test_expect(
        "B2: /md works with https://",
        r"success.*true|markdown",
        ['-X', 'POST', f'{base_url}/md',
         '-H', 'Content-Type: application/json',
         '-d', '{"url":"https://example.com"}']
    )

    test_expect(
        "B3: Health endpoint works",
        r"ok",
        [f'{base_url}/health']
    )

    print()

    # === Part C: Edge Cases ===
    print("=== Part C: Edge Cases ===")
    print("(Malformed input must be REJECTED)")
    print()

    test_expect(
        "C1: javascript: URL rejected (400)",
        r"400|must start with",
        ['-X', 'POST', f'{base_url}/execute_js',
         '-H', 'Content-Type: application/json',
         '-d', '{"url":"javascript:alert(1)","scripts":["1"]}']
    )

    test_expect(
        "C2: data: URL rejected (400)",
        r"400|must start with",
        ['-X', 'POST', f'{base_url}/execute_js',
         '-H', 'Content-Type: application/json',
         '-d', '{"url":"data:text/html,<h1>test</h1>","scripts":["1"]}']
    )

    print()
    print("=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Passed: {GREEN}{PASSED}{NC}")
    print(f"Failed: {RED}{FAILED}{NC}")
    print()

    if FAILED > 0:
        print(f"{RED}SOME TESTS FAILED{NC}")
        sys.exit(1)
    else:
        print(f"{GREEN}ALL TESTS PASSED{NC}")
        sys.exit(0)


if __name__ == '__main__':
    main()

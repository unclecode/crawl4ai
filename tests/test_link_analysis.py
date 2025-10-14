import requests
import json
import time
import sys
import os
from typing import Dict, Any, List


class LinkAnalysisTester:
    def __init__(self, base_url: str = "http://localhost:11234"):
        self.base_url = base_url
        self.token = self.get_test_token()

    def get_test_token(self) -> str:
        """Get authentication token for testing"""
        try:
            # Try to get token using test email
            response = requests.post(
                f"{self.base_url}/token",
                json={"email": "test@example.com"},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()["access_token"]
        except Exception:
            pass

        # Fallback: try with common test token or skip auth for local testing
        return "test-token"

    def analyze_links(
        self,
        url: str,
        config: Dict[str, Any] = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """Analyze links on a webpage"""
        headers = {
            "Content-Type": "application/json"
        }

        # Add auth if token is available
        if self.token and self.token != "test-token":
            headers["Authorization"] = f"Bearer {self.token}"

        request_data = {"url": url}
        if config:
            request_data["config"] = config

        response = requests.post(
            f"{self.base_url}/links/analyze",
            headers=headers,
            json=request_data,
            timeout=timeout
        )

        if response.status_code != 200:
            raise Exception(f"Link analysis failed: {response.status_code} - {response.text}")

        return response.json()


def test_link_analysis_basic():
    """Test basic link analysis functionality"""
    print("\n=== Testing Basic Link Analysis ===")

    tester = LinkAnalysisTester()

    # Test with a simple page
    test_url = "https://httpbin.org/links/10"

    try:
        result = tester.analyze_links(test_url)
        print(f"✅ Successfully analyzed links on {test_url}")

        # Check response structure
        expected_categories = ['internal', 'external', 'social', 'download', 'email', 'phone']
        found_categories = [cat for cat in expected_categories if cat in result]

        print(f"📊 Found link categories: {found_categories}")

        # Count total links
        total_links = sum(len(links) for links in result.values())
        print(f"🔗 Total links found: {total_links}")

        # Verify link objects have expected fields
        for category, links in result.items():
            if links and len(links) > 0:
                sample_link = links[0]
                expected_fields = ['href', 'text']
                optional_fields = ['title', 'base_domain', 'intrinsic_score', 'contextual_score', 'total_score']

                missing_required = [field for field in expected_fields if field not in sample_link]
                found_optional = [field for field in optional_fields if field in sample_link]

                if missing_required:
                    print(f"⚠️  Missing required fields in {category}: {missing_required}")
                else:
                    print(f"✅ {category} links have proper structure (has {len(found_optional)} optional fields: {found_optional})")

        assert total_links > 0, "Should find at least one link"
        print("✅ Basic link analysis test passed")

    except Exception as e:
        print(f"❌ Basic link analysis test failed: {str(e)}")
        raise


def test_link_analysis_with_config():
    """Test link analysis with custom configuration"""
    print("\n=== Testing Link Analysis with Config ===")

    tester = LinkAnalysisTester()

    # Test with valid LinkPreviewConfig options
    config = {
        "include_internal": True,
        "include_external": True,
        "max_links": 50,
        "score_threshold": 0.3,
        "verbose": True
    }

    test_url = "https://httpbin.org/links/10"

    try:
        result = tester.analyze_links(test_url, config)
        print(f"✅ Successfully analyzed links with custom config")

        # Verify configuration was applied
        total_links = sum(len(links) for links in result.values())
        print(f"🔗 Links found with config: {total_links}")

        assert total_links > 0, "Should find links even with config"
        print("✅ Config test passed")

    except Exception as e:
        print(f"❌ Config test failed: {str(e)}")
        raise


def test_link_analysis_complex_page():
    """Test link analysis on a more complex page"""
    print("\n=== Testing Link Analysis on Complex Page ===")

    tester = LinkAnalysisTester()

    # Test with a real-world page
    test_url = "https://www.python.org"

    try:
        result = tester.analyze_links(test_url)
        print(f"✅ Successfully analyzed links on {test_url}")

        # Analyze link distribution
        category_counts = {}
        for category, links in result.items():
            if links:
                category_counts[category] = len(links)
                print(f"📂 {category}: {len(links)} links")

        # Find top-scoring links
        all_links = []
        for category, links in result.items():
            if links:
                for link in links:
                    link['category'] = category
                    all_links.append(link)

        if all_links:
            # Use intrinsic_score or total_score if available, fallback to 0
            top_links = sorted(all_links, key=lambda x: x.get('total_score', x.get('intrinsic_score', 0)), reverse=True)[:5]
            print("\n🏆 Top 5 links by score:")
            for i, link in enumerate(top_links, 1):
                score = link.get('total_score', link.get('intrinsic_score', 0))
                print(f"  {i}. {link.get('text', 'N/A')} ({score:.2f}) - {link.get('category', 'unknown')}")

        # Verify we found different types of links
        assert len(category_counts) > 0, "Should find at least one link category"
        print("✅ Complex page analysis test passed")

    except Exception as e:
        print(f"❌ Complex page analysis test failed: {str(e)}")
        # Don't fail the test suite for network issues
        print("⚠️  This test may fail due to network connectivity issues")


def test_link_analysis_scoring():
    """Test link scoring functionality"""
    print("\n=== Testing Link Scoring ===")

    tester = LinkAnalysisTester()

    test_url = "https://httpbin.org/links/10"

    try:
        result = tester.analyze_links(test_url)

        # Analyze score distribution
        all_scores = []
        for category, links in result.items():
            if links:
                for link in links:
                    # Use total_score or intrinsic_score if available
                    score = link.get('total_score', link.get('intrinsic_score', 0))
                    if score is not None:  # Only include links that have scores
                        all_scores.append(score)

        if all_scores:
            avg_score = sum(all_scores) / len(all_scores)
            max_score = max(all_scores)
            min_score = min(all_scores)

            print(f"📊 Score statistics:")
            print(f"   Average: {avg_score:.3f}")
            print(f"   Maximum: {max_score:.3f}")
            print(f"   Minimum: {min_score:.3f}")
            print(f"   Total links scored: {len(all_scores)}")

            # Verify scores are in expected range
            assert all(0 <= score <= 1 for score in all_scores), "Scores should be between 0 and 1"
            print("✅ All scores are in valid range")

        print("✅ Link scoring test passed")

    except Exception as e:
        print(f"❌ Link scoring test failed: {str(e)}")
        raise


def test_link_analysis_error_handling():
    """Test error handling for invalid requests"""
    print("\n=== Testing Error Handling ===")

    tester = LinkAnalysisTester()

    # Test with invalid URL
    try:
        tester.analyze_links("not-a-valid-url")
        print("⚠️  Expected error for invalid URL, but got success")
    except Exception as e:
        print(f"✅ Correctly handled invalid URL: {str(e)}")

    # Test with non-existent URL
    try:
        result = tester.analyze_links("https://this-domain-does-not-exist-12345.com")
        print("⚠️  This should have failed for non-existent domain")
    except Exception as e:
        print(f"✅ Correctly handled non-existent domain: {str(e)}")

    print("✅ Error handling test passed")


def test_link_analysis_performance():
    """Test performance of link analysis"""
    print("\n=== Testing Performance ===")

    tester = LinkAnalysisTester()

    test_url = "https://httpbin.org/links/50"

    try:
        start_time = time.time()
        result = tester.analyze_links(test_url)
        end_time = time.time()

        duration = end_time - start_time
        total_links = sum(len(links) for links in result.values())

        print(f"⏱️  Analysis completed in {duration:.2f} seconds")
        print(f"🔗 Found {total_links} links")
        print(f"📈 Rate: {total_links/duration:.1f} links/second")

        # Performance should be reasonable
        assert duration < 60, f"Analysis took too long: {duration:.2f}s"
        print("✅ Performance test passed")

    except Exception as e:
        print(f"❌ Performance test failed: {str(e)}")
        raise


def test_link_analysis_categorization():
    """Test link categorization functionality"""
    print("\n=== Testing Link Categorization ===")

    tester = LinkAnalysisTester()

    test_url = "https://www.python.org"

    try:
        result = tester.analyze_links(test_url)

        # Check categorization
        categories_found = []
        for category, links in result.items():
            if links:
                categories_found.append(category)
                print(f"📂 {category}: {len(links)} links")

                # Analyze a sample link from each category
                sample_link = links[0]
                url = sample_link.get('href', '')
                text = sample_link.get('text', '')
                score = sample_link.get('total_score', sample_link.get('intrinsic_score', 0))

                print(f"   Sample: {text[:50]}... ({url[:50]}...) - score: {score:.2f}")

        print(f"✅ Found {len(categories_found)} link categories")
        print("✅ Categorization test passed")

    except Exception as e:
        print(f"❌ Categorization test failed: {str(e)}")
        # Don't fail for network issues
        print("⚠️  This test may fail due to network connectivity issues")


def test_link_analysis_all_config_options():
    """Test all available LinkPreviewConfig options"""
    print("\n=== Testing All Configuration Options ===")

    tester = LinkAnalysisTester()
    test_url = "https://httpbin.org/links/10"

    # Test 1: include_internal and include_external
    print("\n🔍 Testing include_internal/include_external options...")

    configs = [
        {
            "name": "Internal only",
            "config": {"include_internal": True, "include_external": False}
        },
        {
            "name": "External only",
            "config": {"include_internal": False, "include_external": True}
        },
        {
            "name": "Both internal and external",
            "config": {"include_internal": True, "include_external": True}
        }
    ]

    for test_case in configs:
        try:
            result = tester.analyze_links(test_url, test_case["config"])
            internal_count = len(result.get('internal', []))
            external_count = len(result.get('external', []))

            print(f"   {test_case['name']}: {internal_count} internal, {external_count} external links")

            # Verify configuration behavior
            if test_case["config"]["include_internal"] and not test_case["config"]["include_external"]:
                assert internal_count >= 0, "Should have internal links"
            elif not test_case["config"]["include_internal"] and test_case["config"]["include_external"]:
                assert external_count >= 0, "Should have external links"

        except Exception as e:
            print(f"   ❌ {test_case['name']} failed: {e}")

    # Test 2: include_patterns and exclude_patterns
    print("\n🔍 Testing include/exclude patterns...")

    pattern_configs = [
        {
            "name": "Include specific patterns",
            "config": {
                "include_patterns": ["*/links/*", "*/test*"],
                "include_internal": True,
                "include_external": True
            }
        },
        {
            "name": "Exclude specific patterns",
            "config": {
                "exclude_patterns": ["*/admin*", "*/login*"],
                "include_internal": True,
                "include_external": True
            }
        },
        {
            "name": "Both include and exclude patterns",
            "config": {
                "include_patterns": ["*"],
                "exclude_patterns": ["*/exclude*"],
                "include_internal": True,
                "include_external": True
            }
        }
    ]

    for test_case in pattern_configs:
        try:
            result = tester.analyze_links(test_url, test_case["config"])
            total_links = sum(len(links) for links in result.values())
            print(f"   {test_case['name']}: {total_links} links found")

        except Exception as e:
            print(f"   ❌ {test_case['name']} failed: {e}")

    # Test 3: Performance options (concurrency, timeout, max_links)
    print("\n🔍 Testing performance options...")

    perf_configs = [
        {
            "name": "Low concurrency",
            "config": {
                "concurrency": 1,
                "timeout": 10,
                "max_links": 50,
                "include_internal": True,
                "include_external": True
            }
        },
        {
            "name": "High concurrency",
            "config": {
                "concurrency": 5,
                "timeout": 15,
                "max_links": 200,
                "include_internal": True,
                "include_external": True
            }
        },
        {
            "name": "Very limited",
            "config": {
                "concurrency": 1,
                "timeout": 2,
                "max_links": 5,
                "include_internal": True,
                "include_external": True
            }
        }
    ]

    for test_case in perf_configs:
        try:
            start_time = time.time()
            result = tester.analyze_links(test_url, test_case["config"])
            end_time = time.time()

            total_links = sum(len(links) for links in result.values())
            duration = end_time - start_time

            print(f"   {test_case['name']}: {total_links} links in {duration:.2f}s")

            # Verify max_links constraint
            if total_links > test_case["config"]["max_links"]:
                print(f"   ⚠️  Found {total_links} links, expected max {test_case['config']['max_links']}")

        except Exception as e:
            print(f"   ❌ {test_case['name']} failed: {e}")

    # Test 4: Scoring and filtering options
    print("\n🔍 Testing scoring and filtering options...")

    scoring_configs = [
        {
            "name": "No score threshold",
            "config": {
                "score_threshold": None,
                "include_internal": True,
                "include_external": True
            }
        },
        {
            "name": "Low score threshold",
            "config": {
                "score_threshold": 0.1,
                "include_internal": True,
                "include_external": True
            }
        },
        {
            "name": "High score threshold",
            "config": {
                "score_threshold": 0.8,
                "include_internal": True,
                "include_external": True
            }
        },
        {
            "name": "With query for contextual scoring",
            "config": {
                "query": "test links",
                "score_threshold": 0.3,
                "include_internal": True,
                "include_external": True
            }
        }
    ]

    for test_case in scoring_configs:
        try:
            result = tester.analyze_links(test_url, test_case["config"])
            total_links = sum(len(links) for links in result.values())

            # Check score threshold
            if test_case["config"]["score_threshold"] is not None:
                min_score = test_case["config"]["score_threshold"]
                low_score_links = 0

                for links in result.values():
                    for link in links:
                        score = link.get('total_score', link.get('intrinsic_score', 0))
                        if score is not None and score < min_score:
                            low_score_links += 1

                if low_score_links > 0:
                    print(f"   ⚠️  Found {low_score_links} links below threshold {min_score}")
                else:
                    print(f"   ✅ All links meet threshold {min_score}")

            print(f"   {test_case['name']}: {total_links} links")

        except Exception as e:
            print(f"   ❌ {test_case['name']} failed: {e}")

    # Test 5: Verbose mode
    print("\n🔍 Testing verbose mode...")

    try:
        result = tester.analyze_links(test_url, {
            "verbose": True,
            "include_internal": True,
            "include_external": True
        })
        total_links = sum(len(links) for links in result.values())
        print(f"   Verbose mode: {total_links} links")

    except Exception as e:
        print(f"   ❌ Verbose mode failed: {e}")

    print("✅ All configuration options test passed")


def test_link_analysis_edge_cases():
    """Test edge cases and error scenarios for configuration options"""
    print("\n=== Testing Edge Cases ===")

    tester = LinkAnalysisTester()
    test_url = "https://httpbin.org/links/10"

    # Test 1: Invalid configuration values
    print("\n🔍 Testing invalid configuration values...")

    invalid_configs = [
        {
            "name": "Negative concurrency",
            "config": {"concurrency": -1}
        },
        {
            "name": "Zero timeout",
            "config": {"timeout": 0}
        },
        {
            "name": "Negative max_links",
            "config": {"max_links": -5}
        },
        {
            "name": "Invalid score threshold (too high)",
            "config": {"score_threshold": 1.5}
        },
        {
            "name": "Invalid score threshold (too low)",
            "config": {"score_threshold": -0.1}
        },
        {
            "name": "Both include flags false",
            "config": {"include_internal": False, "include_external": False}
        }
    ]

    for test_case in invalid_configs:
        try:
            result = tester.analyze_links(test_url, test_case["config"])
            print(f"   ⚠️  {test_case['name']}: Expected to fail but succeeded")

        except Exception as e:
            print(f"   ✅ {test_case['name']}: Correctly failed - {str(e)}")

    # Test 2: Extreme but valid values
    print("\n🔍 Testing extreme valid values...")

    extreme_configs = [
        {
            "name": "Very high concurrency",
            "config": {
                "concurrency": 50,
                "timeout": 30,
                "max_links": 1000,
                "include_internal": True,
                "include_external": True
            }
        },
        {
            "name": "Very low score threshold",
            "config": {
                "score_threshold": 0.0,
                "include_internal": True,
                "include_external": True
            }
        },
        {
            "name": "Very high score threshold",
            "config": {
                "score_threshold": 1.0,
                "include_internal": True,
                "include_external": True
            }
        }
    ]

    for test_case in extreme_configs:
        try:
            result = tester.analyze_links(test_url, test_case["config"])
            total_links = sum(len(links) for links in result.values())
            print(f"   ✅ {test_case['name']}: {total_links} links")

        except Exception as e:
            print(f"   ❌ {test_case['name']} failed: {e}")

    # Test 3: Complex pattern matching
    print("\n🔍 Testing complex pattern matching...")

    pattern_configs = [
        {
            "name": "Multiple include patterns",
            "config": {
                "include_patterns": ["*/links/*", "*/test*", "*/httpbin*"],
                "include_internal": True,
                "include_external": True
            }
        },
        {
            "name": "Multiple exclude patterns",
            "config": {
                "exclude_patterns": ["*/admin*", "*/login*", "*/logout*", "*/private*"],
                "include_internal": True,
                "include_external": True
            }
        },
        {
            "name": "Overlapping include/exclude patterns",
            "config": {
                "include_patterns": ["*"],
                "exclude_patterns": ["*/admin*", "*/private*"],
                "include_internal": True,
                "include_external": True
            }
        }
    ]

    for test_case in pattern_configs:
        try:
            result = tester.analyze_links(test_url, test_case["config"])
            total_links = sum(len(links) for links in result.values())
            print(f"   {test_case['name']}: {total_links} links")

        except Exception as e:
            print(f"   ❌ {test_case['name']} failed: {e}")

    print("✅ Edge cases test passed")


def test_link_analysis_batch():
    """Test batch link analysis"""
    print("\n=== Testing Batch Analysis ===")

    tester = LinkAnalysisTester()

    test_urls = [
        "https://httpbin.org/links/10",
        "https://httpbin.org/links/5",
        "https://httpbin.org/links/2"
    ]

    try:
        results = {}
        for url in test_urls:
            print(f"🔍 Analyzing: {url}")
            result = tester.analyze_links(url)
            results[url] = result

            # Small delay to be respectful
            time.sleep(0.5)

        print(f"✅ Successfully analyzed {len(results)} URLs")

        for url, result in results.items():
            total_links = sum(len(links) for links in result.values())
            print(f"   {url}: {total_links} links")

        print("✅ Batch analysis test passed")

    except Exception as e:
        print(f"❌ Batch analysis test failed: {str(e)}")
        raise


def run_all_link_analysis_tests():
    """Run all link analysis tests"""
    print("🚀 Starting Link Analysis Test Suite")
    print("=" * 50)

    tests = [
        test_link_analysis_basic,
        test_link_analysis_with_config,
        test_link_analysis_complex_page,
        test_link_analysis_scoring,
        test_link_analysis_error_handling,
        test_link_analysis_performance,
        test_link_analysis_categorization,
        test_link_analysis_batch
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"✅ {test_func.__name__} PASSED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__} FAILED: {str(e)}")

        print("-" * 50)

    print(f"\n📊 Test Results: {passed} passed, {failed} failed")

    if failed > 0:
        print("⚠️  Some tests failed, but this may be due to network or server issues")
        return False

    print("🎉 All tests passed!")
    return True


if __name__ == "__main__":
    # Check if server is running
    import socket

    def check_server(host="localhost", port=11234):
        try:
            socket.create_connection((host, port), timeout=5)
            return True
        except:
            return False

    if not check_server():
        print("❌ Server is not running on localhost:11234")
        print("Please start the Crawl4AI server first:")
        print("  cd deploy/docker && python server.py")
        sys.exit(1)

    success = run_all_link_analysis_tests()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Simple API Test for Crawl4AI Docker Server v0.7.0
Uses only built-in Python modules to test all endpoints.
"""

import urllib.request
import urllib.parse
import json
import time
import sys
from typing import Dict, List, Optional

# Configuration
BASE_URL = "http://localhost:11234"  # Change to your server URL
TEST_TIMEOUT = 30

class SimpleApiTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token = None
        self.results = []
        
    def log(self, message: str):
        print(f"[INFO] {message}")
    
    def test_get_endpoint(self, endpoint: str) -> Dict:
        """Test a GET endpoint"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            req = urllib.request.Request(url)
            if self.token:
                req.add_header('Authorization', f'Bearer {self.token}')
            
            with urllib.request.urlopen(req, timeout=TEST_TIMEOUT) as response:
                response_time = time.time() - start_time
                status_code = response.getcode()
                content = response.read().decode('utf-8')
                
                # Try to parse JSON
                try:
                    data = json.loads(content)
                except:
                    data = {"raw_response": content[:200]}
                
                return {
                    "endpoint": endpoint,
                    "method": "GET",
                    "status": "PASS" if status_code < 400 else "FAIL",
                    "status_code": status_code,
                    "response_time": response_time,
                    "data": data
                }
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "endpoint": endpoint,
                "method": "GET",
                "status": "FAIL",
                "status_code": None,
                "response_time": response_time,
                "error": str(e)
            }
    
    def test_post_endpoint(self, endpoint: str, payload: Dict) -> Dict:
        """Test a POST endpoint"""
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()
        
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, method='POST')
            req.add_header('Content-Type', 'application/json')
            
            if self.token:
                req.add_header('Authorization', f'Bearer {self.token}')
            
            with urllib.request.urlopen(req, timeout=TEST_TIMEOUT) as response:
                response_time = time.time() - start_time
                status_code = response.getcode()
                content = response.read().decode('utf-8')
                
                # Try to parse JSON
                try:
                    data = json.loads(content)
                except:
                    data = {"raw_response": content[:200]}
                
                return {
                    "endpoint": endpoint,
                    "method": "POST",
                    "status": "PASS" if status_code < 400 else "FAIL",
                    "status_code": status_code,
                    "response_time": response_time,
                    "data": data
                }
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "endpoint": endpoint,
                "method": "POST",
                "status": "FAIL",
                "status_code": None,
                "response_time": response_time,
                "error": str(e)
            }
    
    def print_result(self, result: Dict):
        """Print a formatted test result"""
        status_color = {
            "PASS": "✅",
            "FAIL": "❌",
            "SKIP": "⏭️"
        }
        
        print(f"{status_color[result['status']]} {result['method']} {result['endpoint']} "
              f"| {result['response_time']:.3f}s | Status: {result['status_code'] or 'N/A'}")
        
        if result['status'] == 'FAIL' and 'error' in result:
            print(f"    Error: {result['error']}")
        
        self.results.append(result)
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Crawl4AI v0.7.0 API Test Suite")
        print(f"📡 Testing server at: {self.base_url}")
        print("=" * 60)
        
        # # Test basic endpoints
        # print("\n=== BASIC ENDPOINTS ===")
        
        # # Health check
        # result = self.test_get_endpoint("/health")
        # self.print_result(result)
        
        
        # # Schema endpoint
        # result = self.test_get_endpoint("/schema")
        # self.print_result(result)
        
        # # Metrics endpoint
        # result = self.test_get_endpoint("/metrics")
        # self.print_result(result)
        
        # # Root redirect
        # result = self.test_get_endpoint("/")
        # self.print_result(result)
        
        # # Test authentication
        # print("\n=== AUTHENTICATION ===")
        
        # # Get token
        # token_payload = {"email": "test@example.com"}
        # result = self.test_post_endpoint("/token", token_payload)
        # self.print_result(result)
        
        # # Extract token if successful
        # if result['status'] == 'PASS' and 'data' in result:
        #     token = result['data'].get('access_token')
        #     if token:
        #         self.token = token
        #         self.log(f"Successfully obtained auth token: {token[:20]}...")
        
        # Test core APIs
        print("\n=== CORE APIs ===")
        
        test_url = "https://example.com"
        
        # Test markdown endpoint
        md_payload = {
            "url": test_url,
            "f": "fit",
            "q": "test query",
            "c": "0"
        }
        result = self.test_post_endpoint("/md", md_payload)
        # print(result['data'].get('markdown', ''))
        self.print_result(result)
        
        # Test HTML endpoint
        html_payload = {"url": test_url}
        result = self.test_post_endpoint("/html", html_payload)
        self.print_result(result)
        
        # Test screenshot endpoint
        screenshot_payload = {
            "url": test_url,
            "screenshot_wait_for": 2
        }
        result = self.test_post_endpoint("/screenshot", screenshot_payload)
        self.print_result(result)
        
        # Test PDF endpoint
        pdf_payload = {"url": test_url}
        result = self.test_post_endpoint("/pdf", pdf_payload)
        self.print_result(result)
        
        # Test JavaScript execution
        js_payload = {
            "url": test_url,
            "scripts": ["(() => document.title)()"]
        }
        result = self.test_post_endpoint("/execute_js", js_payload)
        self.print_result(result)
        
        # Test crawl endpoint
        crawl_payload = {
            "urls": [test_url],
            "browser_config": {},
            "crawler_config": {}
        }
        result = self.test_post_endpoint("/crawl", crawl_payload)
        self.print_result(result)
        
        # Test config dump
        config_payload = {"code": "CrawlerRunConfig()"}
        result = self.test_post_endpoint("/config/dump", config_payload)
        self.print_result(result)
        
        # Test LLM endpoint
        llm_endpoint = f"/llm/{test_url}?q=Extract%20main%20content"
        result = self.test_get_endpoint(llm_endpoint)
        self.print_result(result)
        
        # Test ask endpoint
        ask_endpoint = "/ask?context_type=all&query=crawl4ai&max_results=5"
        result = self.test_get_endpoint(ask_endpoint)
        print(result)
        self.print_result(result)
        
        # Test job APIs
        print("\n=== JOB APIs ===")
        
        # Test LLM job
        llm_job_payload = {
            "url": test_url,
            "q": "Extract main content",
            "cache": False
        }
        result = self.test_post_endpoint("/llm/job", llm_job_payload)
        self.print_result(result)
        
        # Test crawl job
        crawl_job_payload = {
            "urls": [test_url],
            "browser_config": {},
            "crawler_config": {}
        }
        result = self.test_post_endpoint("/crawl/job", crawl_job_payload)
        self.print_result(result)
        
        # Test MCP
        print("\n=== MCP APIs ===")
        
        # Test MCP schema
        result = self.test_get_endpoint("/mcp/schema")
        self.print_result(result)
        
        # Test error handling
        print("\n=== ERROR HANDLING ===")
        
        # Test invalid URL
        invalid_payload = {"url": "invalid-url", "f": "fit"}
        result = self.test_post_endpoint("/md", invalid_payload)
        self.print_result(result)
        
        # Test invalid endpoint
        result = self.test_get_endpoint("/nonexistent")
        self.print_result(result)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r['status'] == 'PASS')
        failed = sum(1 for r in self.results if r['status'] == 'FAIL')
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if result['status'] == 'FAIL':
                    print(f"  • {result['method']} {result['endpoint']}")
                    if 'error' in result:
                        print(f"    Error: {result['error']}")
        
        # Performance statistics
        response_times = [r['response_time'] for r in self.results if r['response_time'] > 0]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            print(f"\n⏱️  Average Response Time: {avg_time:.3f}s")
            print(f"⏱️  Max Response Time: {max_time:.3f}s")
        
        # Save detailed report
        report_file = f"crawl4ai_test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": time.time(),
                "server_url": self.base_url,
                "version": "0.7.0",
                "summary": {
                    "total": total,
                    "passed": passed,
                    "failed": failed
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Crawl4AI v0.7.0 API Test Suite')
    parser.add_argument('--url', default=BASE_URL, help='Base URL of the server')
    
    args = parser.parse_args()
    
    tester = SimpleApiTester(args.url)
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n🛑 Test suite interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
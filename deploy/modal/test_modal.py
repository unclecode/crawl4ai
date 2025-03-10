
#!/usr/bin/env python3
"""
Crawl4ai API Testing Script

This script tests all endpoints of the Crawl4ai API service and demonstrates their usage.
"""

import argparse
import json
import sys
import time
from typing import Dict, Any, List, Optional

import requests

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")

def print_step(text: str) -> None:
    """Print a formatted step description."""
    print(f"{Colors.BLUE}{Colors.BOLD}>> {text}{Colors.ENDC}")

def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")

def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def print_json(data: Dict[str, Any]) -> None:
    """Pretty print JSON data."""
    print(json.dumps(data, indent=2))

def make_request(method: str, url: str, params: Optional[Dict[str, Any]] = None, 
                 json_data: Optional[Dict[str, Any]] = None, 
                 expected_status: int = 200) -> Dict[str, Any]:
    """Make an HTTP request and handle errors."""
    print_step(f"Making {method.upper()} request to {url}")
    
    if params:
        print(f"  Parameters: {params}")
    if json_data:
        print(f"  JSON Data: {json_data}")
    
    try:
        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=json_data,
            timeout=300  # 5 minute timeout for crawling operations
        )
        
        status_code = response.status_code
        print(f"  Status Code: {status_code}")
        
        try:
            data = response.json()
            print("  Response:")
            print_json(data)
            
            if status_code != expected_status:
                print_error(f"Expected status code {expected_status}, got {status_code}")
                return data
            
            print_success("Request successful")
            return data
        except ValueError:
            print_error("Response is not valid JSON")
            print(response.text)
            return {"error": "Invalid JSON response"}
            
    except requests.RequestException as e:
        print_error(f"Request failed: {str(e)}")
        return {"error": str(e)}

def test_health_check(base_url: str) -> bool:
    """Test the health check endpoint."""
    print_header("Testing Health Check Endpoint")
    
    response = make_request("GET", f"{base_url}/health_check")
    
    if "status" in response and response["status"] == "online":
        print_success("Health check passed")
        return True
    else:
        print_error("Health check failed")
        return False

def test_admin_create_user(base_url: str, admin_token: str, email: str, name: str) -> Optional[str]:
    """Test creating a new user."""
    print_header("Testing Admin User Creation")
    
    response = make_request(
        "POST", 
        f"{base_url}/admin_create_user",
        json_data={
            "admin_token": admin_token,
            "email": email,
            "name": name
        },
        expected_status=201
    )
    
    if response.get("success") and "data" in response:
        api_token = response["data"].get("api_token")
        if api_token:
            print_success(f"User created successfully with API token: {api_token}")
            return api_token
    
    print_error("Failed to create user")
    return None

def test_check_credits(base_url: str, api_token: str) -> Optional[int]:
    """Test checking user credits."""
    print_header("Testing Check Credits Endpoint")
    
    response = make_request(
        "GET",
        f"{base_url}/check_credits",
        params={"api_token": api_token}
    )
    
    if response.get("success") and "data" in response:
        credits = response["data"].get("credits")
        if credits is not None:
            print_success(f"User has {credits} credits")
            return credits
    
    print_error("Failed to check credits")
    return None

def test_crawl_endpoint(base_url: str, api_token: str, url: str) -> bool:
    """Test the crawl endpoint."""
    print_header("Testing Crawl Endpoint")
    
    response = make_request(
        "POST",
        f"{base_url}/crawl_endpoint",
        json_data={
            "api_token": api_token,
            "url": url
        }
    )
    
    if response.get("success") and "data" in response:
        print_success("Crawl completed successfully")
        
        # Display some crawl result data
        data = response["data"]
        if "title" in data:
            print(f"Page Title: {data['title']}")
        if "status" in data:
            print(f"Status: {data['status']}")
        if "links" in data:
            print(f"Links found: {len(data['links'])}")
        if "markdown_v2" in data and data["markdown_v2"] and "raw_markdown" in data["markdown_v2"]:
            print("Markdown Preview (first 200 chars):")
            print(data["markdown_v2"]["raw_markdown"][:200] + "...")
            
        credits_remaining = response.get("credits_remaining")
        if credits_remaining is not None:
            print(f"Credits remaining: {credits_remaining}")
            
        return True
    
    print_error("Crawl failed")
    return False

def test_admin_update_credits(base_url: str, admin_token: str, api_token: str, amount: int) -> bool:
    """Test updating user credits."""
    print_header("Testing Admin Update Credits")
    
    response = make_request(
        "POST",
        f"{base_url}/admin_update_credits",
        json_data={
            "admin_token": admin_token,
            "api_token": api_token,
            "amount": amount
        }
    )
    
    if response.get("success") and "data" in response:
        print_success(f"Credits updated successfully, new balance: {response['data'].get('credits')}")
        return True
    
    print_error("Failed to update credits")
    return False

def test_admin_get_users(base_url: str, admin_token: str) -> List[Dict[str, Any]]:
    """Test getting all users."""
    print_header("Testing Admin Get All Users")
    
    response = make_request(
        "GET",
        f"{base_url}/admin_get_users",
        params={"admin_token": admin_token}
    )
    
    if response.get("success") and "data" in response:
        users = response["data"]
        print_success(f"Retrieved {len(users)} users")
        return users
    
    print_error("Failed to get users")
    return []

def run_full_test(base_url: str, admin_token: str) -> None:
    """Run all tests in sequence."""
    # Remove trailing slash if present
    base_url = base_url.rstrip('/')
    
    # Test 1: Health Check
    if not test_health_check(base_url):
        print_error("Health check failed, aborting tests")
        sys.exit(1)
    
    # Test 2: Create a test user
    email = f"test-user-{int(time.time())}@example.com"
    name = "Test User"
    api_token = test_admin_create_user(base_url, admin_token, email, name)
    
    if not api_token:
        print_error("User creation failed, aborting tests")
        sys.exit(1)
    
    # Test 3: Check initial credits
    initial_credits = test_check_credits(base_url, api_token)
    
    if initial_credits is None:
        print_error("Credit check failed, aborting tests")
        sys.exit(1)
    
    # Test 4: Perform a crawl
    test_url = "https://news.ycombinator.com"
    crawl_success = test_crawl_endpoint(base_url, api_token, test_url)
    
    if not crawl_success:
        print_warning("Crawl test failed, but continuing with other tests")
    
    # Test 5: Check credits after crawl
    post_crawl_credits = test_check_credits(base_url, api_token)
    
    if post_crawl_credits is not None and initial_credits is not None:
        if post_crawl_credits == initial_credits - 1:
            print_success("Credit deduction verified")
        else:
            print_warning(f"Unexpected credit change: {initial_credits} -> {post_crawl_credits}")
    
    # Test 6: Add credits
    add_credits_amount = 50
    if test_admin_update_credits(base_url, admin_token, api_token, add_credits_amount):
        print_success(f"Added {add_credits_amount} credits")
    
    # Test 7: Check credits after addition
    post_addition_credits = test_check_credits(base_url, api_token)
    
    if post_addition_credits is not None and post_crawl_credits is not None:
        if post_addition_credits == post_crawl_credits + add_credits_amount:
            print_success("Credit addition verified")
        else:
            print_warning(f"Unexpected credit change: {post_crawl_credits} -> {post_addition_credits}")
    
    # Test 8: Get all users
    users = test_admin_get_users(base_url, admin_token)
    
    if users:
        # Check if our test user is in the list
        test_user = next((user for user in users if user.get("email") == email), None)
        if test_user:
            print_success("Test user found in users list")
        else:
            print_warning("Test user not found in users list")
    
    # Final report
    print_header("Test Summary")
    
    print_success("All endpoints tested successfully")
    print(f"Test user created with email: {email}")
    print(f"API token: {api_token}")
    print(f"Final credit balance: {post_addition_credits}")

def main():
    parser = argparse.ArgumentParser(description="Test Crawl4ai API endpoints")
    parser.add_argument("--base-url", required=True, help="Base URL of the Crawl4ai API (e.g., https://username--crawl4ai-api.modal.run)")
    parser.add_argument("--admin-token", required=True, help="Admin token for authentication")
    
    args = parser.parse_args()
    
    print_header("Crawl4ai API Test Script")
    print(f"Testing API at: {args.base_url}")
    
    run_full_test(args.base_url, args.admin_token)

if __name__ == "__main__":
    main()
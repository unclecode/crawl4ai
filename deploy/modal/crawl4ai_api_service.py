import os
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

import modal
from modal import Image, App, Volume, Secret, web_endpoint, function

# Configuration
APP_NAME = "crawl4ai-api"
CRAWL4AI_VERSION = "next"  # Using the 'next' branch
PYTHON_VERSION = "3.10"  # Compatible with playwright
DEFAULT_CREDITS = 1000

# Create a custom image with Crawl4ai and its dependencies
image = Image.debian_slim(python_version=PYTHON_VERSION).pip_install(
    ["fastapi[standard]", "pymongo", "pydantic"]
).run_commands(
    "apt-get update",
    "apt-get install -y software-properties-common",
    "apt-get install -y git",
    "apt-add-repository non-free",
    "apt-add-repository contrib",
    # Install crawl4ai from the next branch
    f"pip install -U git+https://github.com/unclecode/crawl4ai.git@{CRAWL4AI_VERSION}",
    "pip install -U fastapi[standard]",
    "pip install -U pydantic",
    # Install playwright and browsers
    "crawl4ai-setup",
)

# Create persistent volume for user database
user_db = Volume.from_name("crawl4ai-users", create_if_missing=True)

# Create admin secret for secure operations
admin_secret = Secret.from_name("admin-secret", create_if_missing=True)

# Define the app
app = App(APP_NAME, image=image)

# Default configurations
DEFAULT_BROWSER_CONFIG = {
    "headless": True,
    "verbose": False,
}

DEFAULT_CRAWLER_CONFIG = {
    "crawler_config": {
        "type": "CrawlerRunConfig",
        "params": {
            "markdown_generator": {
                "type": "DefaultMarkdownGenerator",
                "params": {
                    "content_filter": {
                        "type": "PruningContentFilter",
                        "params": {
                            "threshold": 0.48,
                            "threshold_type": "fixed"
                        }
                    }
                }
            }
        }
    }
}

# Database operations
@app.function(volumes={"/data": user_db})
def init_db() -> None:
    """Initialize database with indexes."""
    from pymongo import MongoClient, ASCENDING
    
    client = MongoClient("mongodb://localhost:27017")
    db = client.crawl4ai_db
    
    # Ensure indexes for faster lookups
    db.users.create_index([("api_token", ASCENDING)], unique=True)
    db.users.create_index([("email", ASCENDING)], unique=True)
    
    # Create usage stats collection
    db.usage_stats.create_index([("user_id", ASCENDING), ("timestamp", ASCENDING)])
    
    print("Database initialized with required indexes")

@app.function(volumes={"/data": user_db})
def get_user_by_token(api_token: str) -> Optional[Dict[str, Any]]:
    """Get user by API token."""
    from pymongo import MongoClient
    from bson.objectid import ObjectId
    
    client = MongoClient("mongodb://localhost:27017")
    db = client.crawl4ai_db
    
    user = db.users.find_one({"api_token": api_token})
    if not user:
        return None
    
    # Convert ObjectId to string for serialization
    user["_id"] = str(user["_id"])
    return user

@app.function(volumes={"/data": user_db})
def create_user(email: str, name: str) -> Dict[str, Any]:
    """Create a new user with initial credits."""
    from pymongo import MongoClient
    from bson.objectid import ObjectId
    
    client = MongoClient("mongodb://localhost:27017")
    db = client.crawl4ai_db
    
    # Generate API token
    api_token = str(uuid.uuid4())
    
    user = {
        "email": email,
        "name": name,
        "api_token": api_token,
        "credits": DEFAULT_CREDITS,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True
    }
    
    try:
        result = db.users.insert_one(user)
        user["_id"] = str(result.inserted_id)
        return user
    except Exception as e:
        if "duplicate key error" in str(e):
            return {"error": "User with this email already exists"}
        raise

@app.function(volumes={"/data": user_db})
def update_user_credits(api_token: str, amount: int) -> Dict[str, Any]:
    """Update user credits (add or subtract)."""
    from pymongo import MongoClient
    
    client = MongoClient("mongodb://localhost:27017")
    db = client.crawl4ai_db
    
    # First get current user to check credits
    user = db.users.find_one({"api_token": api_token})
    if not user:
        return {"success": False, "error": "User not found"}
    
    # For deductions, ensure sufficient credits
    if amount < 0 and user["credits"] + amount < 0:
        return {"success": False, "error": "Insufficient credits"}
    
    # Update credits
    result = db.users.update_one(
        {"api_token": api_token},
        {
            "$inc": {"credits": amount},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    if result.modified_count == 1:
        # Get updated user
        updated_user = db.users.find_one({"api_token": api_token})
        return {
            "success": True, 
            "credits": updated_user["credits"]
        }
    else:
        return {"success": False, "error": "Failed to update credits"}

@app.function(volumes={"/data": user_db})
def log_usage(user_id: str, url: str, success: bool, error: Optional[str] = None) -> None:
    """Log usage statistics."""
    from pymongo import MongoClient
    from bson.objectid import ObjectId
    
    client = MongoClient("mongodb://localhost:27017")
    db = client.crawl4ai_db
    
    log_entry = {
        "user_id": user_id,
        "url": url,
        "timestamp": datetime.utcnow(),
        "success": success,
        "error": error
    }
    
    db.usage_stats.insert_one(log_entry)

# Main crawling function
@app.function(timeout=300)  # 5 minute timeout
async def crawl(
    url: str,
    browser_config: Optional[Dict[str, Any]] = None,
    crawler_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Crawl a given URL using Crawl4ai.
    
    Args:
        url: The URL to crawl
        browser_config: Optional browser configuration to override defaults
        crawler_config: Optional crawler configuration to override defaults
        
    Returns:
        A dictionary containing the crawl results
    """
    from crawl4ai import (
        AsyncWebCrawler,
        BrowserConfig,
        CrawlerRunConfig,
        CrawlResult
    )

    # Prepare browser config using the loader method
    if browser_config is None:
        browser_config = DEFAULT_BROWSER_CONFIG
    browser_config_obj = BrowserConfig.load(browser_config)
    
    # Prepare crawler config using the loader method
    if crawler_config is None:
        crawler_config = DEFAULT_CRAWLER_CONFIG
    crawler_config_obj = CrawlerRunConfig.load(crawler_config)    
    
    # Perform the crawl
    async with AsyncWebCrawler(config=browser_config_obj) as crawler:
        result: CrawlResult = await crawler.arun(url=url, config=crawler_config_obj)
        
        # Return serializable results
        try:
            # Try newer Pydantic v2 method
            return result.model_dump()
        except AttributeError:
            try:
                # Try older Pydantic v1 method
                return result.dict()
            except AttributeError:
                # Fallback to manual conversion
                return {
                    "url": result.url,
                    "title": result.title,
                    "status": result.status,
                    "content": str(result.content) if hasattr(result, "content") else None,
                    "links": [{"url": link.url, "text": link.text} for link in result.links] if hasattr(result, "links") else [],
                    "markdown_v2": {
                        "raw_markdown": result.markdown_v2.raw_markdown if hasattr(result, "markdown_v2") else None
                    }
                }

# API endpoints
@app.function()
@web_endpoint(method="POST")
def crawl_endpoint(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Web endpoint that accepts POST requests with JSON data containing:
    - api_token: User's API token
    - url: The URL to crawl
    - browser_config: Optional browser configuration
    - crawler_config: Optional crawler configuration
    
    Returns the crawl results and remaining credits.
    """
    # Extract and validate API token
    api_token = data.get("api_token")
    if not api_token:
        return {
            "success": False,
            "error": "API token is required",
            "status_code": 401
        }
    
    # Verify user
    user = get_user_by_token.remote(api_token)
    if not user:
        return {
            "success": False,
            "error": "Invalid API token",
            "status_code": 401
        }
    
    if not user.get("is_active", False):
        return {
            "success": False,
            "error": "Account is inactive",
            "status_code": 403
        }
    
    # Validate URL
    url = data.get("url")
    if not url:
        return {
            "success": False,
            "error": "URL is required",
            "status_code": 400
        }
    
    # Check credits
    if user.get("credits", 0) <= 0:
        return {
            "success": False,
            "error": "Insufficient credits",
            "status_code": 403
        }
    
    # Deduct credit first (1 credit per call)
    credit_result = update_user_credits.remote(api_token, -1)
    if not credit_result.get("success", False):
        return {
            "success": False,
            "error": credit_result.get("error", "Failed to process credits"),
            "status_code": 500
        }
    
    # Extract configs
    browser_config = data.get("browser_config")
    crawler_config = data.get("crawler_config")
    
    # Perform crawl
    try:
        start_time = time.time()
        result = crawl.remote(url, browser_config, crawler_config)
        execution_time = time.time() - start_time
        
        # Log successful usage
        log_usage.spawn(user["_id"], url, True)
        
        return {
            "success": True,
            "data": result,
            "credits_remaining": credit_result.get("credits"),
            "execution_time_seconds": round(execution_time, 2),
            "status_code": 200
        }
    except Exception as e:
        # Log failed usage
        log_usage.spawn(user["_id"], url, False, str(e))
        
        # Return error
        return {
            "success": False,
            "error": f"Crawling error: {str(e)}",
            "credits_remaining": credit_result.get("credits"),
            "status_code": 500
        }

# Admin endpoints
@app.function(secrets=[admin_secret])
@web_endpoint(method="POST")
def admin_create_user(data: Dict[str, Any]) -> Dict[str, Any]:
    """Admin endpoint to create new users."""
    # Validate admin token
    admin_token = data.get("admin_token")
    if admin_token != os.environ.get("ADMIN_TOKEN"):
        return {
            "success": False,
            "error": "Invalid admin token",
            "status_code": 401
        }
    
    # Validate input
    email = data.get("email")
    name = data.get("name")
    
    if not email or not name:
        return {
            "success": False,
            "error": "Email and name are required",
            "status_code": 400
        }
    
    # Create user
    user = create_user.remote(email, name)
    
    if "error" in user:
        return {
            "success": False,
            "error": user["error"],
            "status_code": 400
        }
    
    return {
        "success": True,
        "data": {
            "user_id": user["_id"],
            "email": user["email"],
            "name": user["name"],
            "api_token": user["api_token"],
            "credits": user["credits"],
            "created_at": user["created_at"].isoformat() if isinstance(user["created_at"], datetime) else user["created_at"]
        },
        "status_code": 201
    }

@app.function(secrets=[admin_secret])
@web_endpoint(method="POST")
def admin_update_credits(data: Dict[str, Any]) -> Dict[str, Any]:
    """Admin endpoint to update user credits."""
    # Validate admin token
    admin_token = data.get("admin_token")
    if admin_token != os.environ.get("ADMIN_TOKEN"):
        return {
            "success": False,
            "error": "Invalid admin token",
            "status_code": 401
        }
    
    # Validate input
    api_token = data.get("api_token")
    amount = data.get("amount")
    
    if not api_token:
        return {
            "success": False,
            "error": "API token is required",
            "status_code": 400
        }
    
    if not isinstance(amount, int):
        return {
            "success": False,
            "error": "Amount must be an integer",
            "status_code": 400
        }
    
    # Update credits
    result = update_user_credits.remote(api_token, amount)
    
    if not result.get("success", False):
        return {
            "success": False,
            "error": result.get("error", "Failed to update credits"),
            "status_code": 400
        }
    
    return {
        "success": True,
        "data": {
            "credits": result["credits"]
        },
        "status_code": 200
    }

@app.function(secrets=[admin_secret])
@web_endpoint(method="GET")
def admin_get_users(admin_token: str) -> Dict[str, Any]:
    """Admin endpoint to list all users."""
    # Validate admin token
    if admin_token != os.environ.get("ADMIN_TOKEN"):
        return {
            "success": False,
            "error": "Invalid admin token",
            "status_code": 401
        }
    
    users = get_all_users.remote()
    
    return {
        "success": True,
        "data": users,
        "status_code": 200
    }

@app.function(volumes={"/data": user_db})
def get_all_users() -> List[Dict[str, Any]]:
    """Get all users (for admin)."""
    from pymongo import MongoClient
    
    client = MongoClient("mongodb://localhost:27017")
    db = client.crawl4ai_db
    
    users = []
    for user in db.users.find():
        # Convert ObjectId to string
        user["_id"] = str(user["_id"])
        # Convert datetime to ISO format
        for field in ["created_at", "updated_at"]:
            if field in user and isinstance(user[field], datetime):
                user[field] = user[field].isoformat()
        users.append(user)
    
    return users

# Public endpoints
@app.function()
@web_endpoint(method="GET")
def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "online",
        "service": APP_NAME,
        "version": CRAWL4AI_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.function()
@web_endpoint(method="GET")
def check_credits(api_token: str) -> Dict[str, Any]:
    """Check user credits."""
    if not api_token:
        return {
            "success": False,
            "error": "API token is required",
            "status_code": 401
        }
    
    user = get_user_by_token.remote(api_token)
    if not user:
        return {
            "success": False,
            "error": "Invalid API token",
            "status_code": 401
        }
    
    return {
        "success": True,
        "data": {
            "credits": user["credits"],
            "email": user["email"],
            "name": user["name"]
        },
        "status_code": 200
    }

# Local entrypoint for testing
@app.local_entrypoint()
def main(url: str = "https://www.modal.com"):
    """Command line entrypoint for local testing."""
    print("Initializing database...")
    init_db.remote()
    
    print(f"Testing crawl on URL: {url}")
    result = crawl.remote(url)
    
    # Print sample of result
    print("\nCrawl Result Sample:")
    if "title" in result:
        print(f"Title: {result['title']}")
    if "status" in result:
        print(f"Status: {result['status']}")
    if "links" in result:
        print(f"Links found: {len(result['links'])}")
    if "markdown_v2" in result and result["markdown_v2"] and "raw_markdown" in result["markdown_v2"]:
        print("\nMarkdown Preview (first 300 chars):")
        print(result["markdown_v2"]["raw_markdown"][:300] + "...")
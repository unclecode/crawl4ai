"""
Marketplace Configuration - Loads from .env file
"""
import os
import sys
import hashlib
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / '.env'
if not env_path.exists():
    print("\n❌ ERROR: No .env file found!")
    print("Please copy .env.example to .env and update with your values:")
    print(f"  cp {Path(__file__).parent}/.env.example {Path(__file__).parent}/.env")
    print("\nThen edit .env with your secure values.")
    sys.exit(1)

load_dotenv(env_path)

# Required environment variables
required_vars = ['MARKETPLACE_ADMIN_PASSWORD', 'MARKETPLACE_JWT_SECRET']
missing_vars = [var for var in required_vars if not os.getenv(var)]

if missing_vars:
    print(f"\n❌ ERROR: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please check your .env file and ensure all required variables are set.")
    sys.exit(1)

class Config:
    """Configuration loaded from environment variables"""

    # Admin authentication - hashed from password in .env
    ADMIN_PASSWORD_HASH = hashlib.sha256(
        os.getenv('MARKETPLACE_ADMIN_PASSWORD').encode()
    ).hexdigest()

    # JWT secret for token generation
    JWT_SECRET_KEY = os.getenv('MARKETPLACE_JWT_SECRET')

    # Database path
    DATABASE_PATH = os.getenv('MARKETPLACE_DB_PATH', './marketplace.db')

    # Token expiry in hours
    TOKEN_EXPIRY_HOURS = int(os.getenv('MARKETPLACE_TOKEN_EXPIRY', '4'))

    # CORS origins - hardcoded as they don't contain secrets
    ALLOWED_ORIGINS = [
        "http://localhost:8000",
        "http://localhost:8080",
        "http://localhost:8100",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8100",
        "https://crawl4ai.com",
        "https://www.crawl4ai.com",
        "https://docs.crawl4ai.com",
        "https://market.crawl4ai.com"
    ]
#!/usr/bin/env python3
"""
Startup script for the Web Scraper API with frontend interface.
"""

import os
import sys
import uvicorn
from pathlib import Path

def main():
    # Check if static directory exists
    static_dir = Path("static")
    if not static_dir.exists():
        print("❌ Static directory not found!")
        print("Please make sure the 'static' directory exists with the frontend files.")
        sys.exit(1)
    
    # Check if required frontend files exist
    required_files = ["index.html", "styles.css", "script.js"]
    missing_files = []
    
    for file in required_files:
        if not (static_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing frontend files: {', '.join(missing_files)}")
        print("Please make sure all frontend files are present in the static directory.")
        sys.exit(1)
    
    print("🚀 Starting Web Scraper API with Frontend Interface")
    print("=" * 50)
    print("📁 Static files found and ready to serve")
    print("🌐 Frontend will be available at: http://localhost:8000")
    print("🔌 API endpoints available at: http://localhost:8000/docs")
    print("=" * 50)
    
    # Start the server
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main() 
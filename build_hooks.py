import os
import shutil
from pathlib import Path
import subprocess
import sys
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
PLUGIN = "CustomBuildHook" 

class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        # Create the .crawl4ai folder structure
        base_dir = os.getenv("CRAWL4_AI_BASE_DIRECTORY")
        crawl4ai_folder = Path(base_dir) if base_dir else Path.home()
        crawl4ai_folder = crawl4ai_folder / ".crawl4ai"
        cache_folder = crawl4ai_folder / "cache"
        content_folders = [
            "html_content",
            "cleaned_html",
            "markdown_content",
            "extracted_content",
            "screenshots",
        ]

        # Clean up old cache if exists
        if cache_folder.exists():
            shutil.rmtree(cache_folder)

        # Create new folder structure
        crawl4ai_folder.mkdir(exist_ok=True)
        cache_folder.mkdir(exist_ok=True)
        for folder in content_folders:
            (crawl4ai_folder / folder).mkdir(exist_ok=True)

        # Install Playwright browsers
        try:
            subprocess.check_call([sys.executable, "-m", "playwright", "install"])
        except Exception as e:
            print(f"Warning: Playwright installation failed: {e}")
            print("Please run 'python -m playwright install' manually after installation")

        # Initialize database
        try:
            from crawl4ai.async_database import async_db_manager
            import asyncio
            asyncio.run(async_db_manager.initialize())
        except Exception as e:
            print(f"Warning: Database initialization failed: {e}")
            print("Database will be initialized on first use")
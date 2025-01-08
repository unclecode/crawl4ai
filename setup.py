from setuptools import setup, find_packages
import os
from pathlib import Path
import shutil

# Note: Most configuration is now in pyproject.toml
# This setup.py is kept for backwards compatibility

# Create the .crawl4ai folder in the user's home directory if it doesn't exist
# If the folder already exists, remove the cache folder
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

version = "0.0.0"  # This will be overridden by pyproject.toml's dynamic version
try:
    with open("crawl4ai/__version__.py") as f:
        for line in f:
            if line.startswith("__version__"):
                version = line.split("=")[1].strip().strip('"')
                break
except Exception:
    pass  # Let pyproject.toml handle version

ssetup(
    name="your_package_name",  # Replace with your package's name
    version="0.1",  # Adjust the version number
    license="MIT",
    packages=find_packages(),
    package_data={
        'crawl4ai': [
            'js_snippet/*.js',
            'py.typed',  # Include the py.typed file
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",  # Fixed license information
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.9",
)


from setuptools import setup, find_packages
from setuptools.command.install import install
import os
from pathlib import Path
import shutil
import subprocess
import sys
import asyncio

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

# Read requirements and version
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
with open(os.path.join(__location__, "requirements.txt")) as f:
    requirements = f.read().splitlines()

with open("crawl4ai/__version__.py") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"')
            break

# Define requirements
default_requirements = requirements
torch_requirements = ["torch", "nltk", "scikit-learn"]
transformer_requirements = ["transformers", "tokenizers"]
cosine_similarity_requirements = ["torch", "transformers", "nltk"]
sync_requirements = ["selenium"]


def install_playwright():
    print("Installing Playwright browsers...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])
        print("Playwright installation completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during Playwright installation: {e}")
        print(
            "Please run 'python -m playwright install' manually after the installation."
        )
    except Exception as e:
        print(f"Unexpected error during Playwright installation: {e}")
        print(
            "Please run 'python -m playwright install' manually after the installation."
        )


def run_migration():
    """Initialize database during installation"""
    try:
        print("Starting database initialization...")
        from crawl4ai.async_database import async_db_manager

        asyncio.run(async_db_manager.initialize())
        print("Database initialization completed successfully.")
    except ImportError:
        print("Warning: Database module not found. Will initialize on first use.")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("Database will be initialized on first use")


class PostInstallCommand(install):
    def run(self):
        install.run(self)
        install_playwright()
        # run_migration()


setup(
    name="Crawl4AI",
    version=version,
    description="🔥🕷️ Crawl4AI: Open-source LLM Friendly Web Crawler & scraper",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/unclecode/crawl4ai",
    author="Unclecode",
    author_email="unclecode@kidocode.com",
    license="MIT",
    packages=find_packages(),
    install_requires=default_requirements
    + ["playwright", "aiofiles"],  # Added aiofiles
    extras_require={
        "torch": torch_requirements,
        "transformer": transformer_requirements,
        "cosine": cosine_similarity_requirements,
        "sync": sync_requirements,
        "all": default_requirements
        + torch_requirements
        + transformer_requirements
        + cosine_similarity_requirements
        + sync_requirements,
    },
    entry_points={
        "console_scripts": [
            "crawl4ai-download-models=crawl4ai.model_loader:main",
            "crawl4ai-migrate=crawl4ai.migrations:main",  # Added migration command
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
    cmdclass={
        "install": PostInstallCommand,
    },
)

from setuptools import setup, find_packages
import os
from pathlib import Path
import shutil
import subprocess

# Create the .crawl4ai folder in the user's home directory if it doesn't exist
# If the folder already exists, remove the cache folder
crawl4ai_folder = Path.home() / ".crawl4ai"
cache_folder = crawl4ai_folder / "cache"

if cache_folder.exists():
    shutil.rmtree(cache_folder)

crawl4ai_folder.mkdir(exist_ok=True)
cache_folder.mkdir(exist_ok=True)

# Read the requirements from requirements.txt
with open("requirements.txt") as f:
    requirements = f.read().splitlines()
    
# Read version from __init__.py
with open("crawl4ai/__init__.py") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"')
            break

# Define the requirements for different environments
default_requirements = [req for req in requirements if not req.startswith(("torch", "transformers", "onnxruntime", "nltk", "spacy", "tokenizers", "scikit-learn", "selenium"))]
torch_requirements = [req for req in requirements if req.startswith(("torch", "nltk", "spacy", "scikit-learn", "numpy"))]
transformer_requirements = [req for req in requirements if req.startswith(("transformers", "tokenizers", "onnxruntime"))]
sync_requirements = ["selenium"]
cosine_similarity_requirements = ["torch", "transformers", "nltk", "spacy"]

def post_install():
    print("Running post-installation setup...")
    try:
        subprocess.check_call(["playwright", "install"])
        print("Playwright installation completed successfully.")
    except subprocess.CalledProcessError:
        print("Error during Playwright installation. Please run 'playwright install' manually.")
    except FileNotFoundError:
        print("Playwright not found. Please ensure it's installed and run 'playwright install' manually.")

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
    install_requires=default_requirements,
    extras_require={
        "torch": torch_requirements,
        "transformer": transformer_requirements,
        "sync": sync_requirements,
        "cosine": cosine_similarity_requirements,
        "all": requirements + sync_requirements + cosine_similarity_requirements,
    },
    entry_points={
        'console_scripts': [
            'crawl4ai-download-models=crawl4ai.model_loader:main',
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
        'install': post_install,
    },
)
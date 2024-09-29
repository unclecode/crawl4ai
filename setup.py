from setuptools import setup, find_packages
from setuptools.command.install import install
import os
from pathlib import Path
import shutil
import subprocess
import sys

# Create the .crawl4ai folder in the user's home directory if it doesn't exist
# If the folder already exists, remove the cache folder
crawl4ai_folder = Path.home() / ".crawl4ai"
cache_folder = crawl4ai_folder / "cache"

if cache_folder.exists():
    shutil.rmtree(cache_folder)

crawl4ai_folder.mkdir(exist_ok=True)
cache_folder.mkdir(exist_ok=True)

# Read the requirements from requirements.txt
__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
with open(os.path.join(__location__, "requirements.txt")) as f:
    requirements = f.read().splitlines()
    
# Read version from __init__.py
with open("crawl4ai/__init__.py") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"')
            break

# Define the requirements for different environments
default_requirements = requirements
torch_requirements = ["torch", "nltk", "spacy", "scikit-learn"]
transformer_requirements = ["transformers", "tokenizers", "onnxruntime"]
cosine_similarity_requirements = ["torch", "transformers", "nltk", "spacy"]
sync_requirements = ["selenium"]

def install_playwright():
    print("Installing Playwright browsers...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install"])
        print("Playwright installation completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during Playwright installation: {e}")
        print("Please run 'python -m playwright install' manually after the installation.")
    except Exception as e:
        print(f"Unexpected error during Playwright installation: {e}")
        print("Please run 'python -m playwright install' manually after the installation.")

class PostInstallCommand(install):
    def run(self):
        install.run(self)
        install_playwright()

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
    install_requires=default_requirements + ["playwright"],  # Add playwright to default requirements
    extras_require={
        "torch": torch_requirements,
        "transformer": transformer_requirements,
        "cosine": cosine_similarity_requirements,
        "sync": sync_requirements,
        "all": default_requirements + torch_requirements + transformer_requirements + cosine_similarity_requirements + sync_requirements,
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
        'install': PostInstallCommand,
    },
)
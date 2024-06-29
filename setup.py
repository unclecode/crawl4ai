from setuptools import setup, find_packages
import os
from pathlib import Path
import subprocess
from setuptools.command.install import install

# Create the .crawl4ai folder in the user's home directory if it doesn't exist
crawl4ai_folder = os.path.join(Path.home(), ".crawl4ai")
os.makedirs(crawl4ai_folder, exist_ok=True)
os.makedirs(f"{crawl4ai_folder}/cache", exist_ok=True)

# Read the requirements from requirements.txt
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

# Define the requirements for different environments
default_requirements = [req for req in requirements if not req.startswith(("torch", "transformers", "onnxruntime", "nltk", "spacy", "tokenizers", "scikit-learn", "numpy"))]
torch_requirements = [req for req in requirements if req.startswith(("torch", "nltk", "spacy", "scikit-learn", "numpy"))]
transformer_requirements = [req for req in requirements if req.startswith(("transformers", "tokenizers", "onnxruntime"))]

class CustomInstallCommand(install):
    """Customized setuptools install command to install spacy without dependencies."""
    def run(self):
        install.run(self)
        subprocess.check_call([os.sys.executable, '-m', 'pip', 'install', 'spacy', '--no-deps'])

setup(
    name="Crawl4AI",
    version="0.2.72",
    description="🔥🕷️ Crawl4AI: Open-source LLM Friendly Web Crawler & Scrapper",
    long_description=open("README.md", encoding='utf-8').read(),
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
        "all": requirements,
    },
    cmdclass={
        'install': CustomInstallCommand,
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
)

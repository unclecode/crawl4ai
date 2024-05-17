from setuptools import setup, find_packages

# Read the requirements from requirements.txt
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

# Define the requirements for different environments
requirements_without_torch = [req for req in requirements if not req.startswith("torch")]
requirements_without_transformers = [req for req in requirements if not req.startswith("transformers")]
requirements_without_nltk = [req for req in requirements if not req.startswith("nltk")]
requirements_without_torch_transformers_nlkt = [req for req in requirements if not req.startswith("torch") and not req.startswith("transformers") and not req.startswith("nltk")]

setup(
    name="Crawl4AI",
    version="0.2.0",
    description="🔥🕷️ Crawl4AI: Open-source LLM Friendly Web Crawler & Scrapper",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/unclecode/crawl4ai",
    author="Unclecode",
    author_email="unclecode@kidocode.com",
    license="MIT",
    packages=find_packages(),
    install_requires=requirements_without_torch_transformers_nlkt,
    extras_require={
        "all": requirements,  # Include all requirements
        "colab": requirements_without_torch,  # Exclude torch for Colab
        "crawl": requirements_without_torch_transformers_nlkt
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

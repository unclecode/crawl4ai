from setuptools import setup, find_packages

# Read the requirements from requirements.txt
with open("requirements.txt") as f:
    requirements = f.read().splitlines()
    
setup(
    name="Crawl4AI",
    version="0.1.0",
    description="🔥🕷️ Crawl4AI: Open-source LLM Friendly Web Crawler & Scrapper",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/unclecode/crawl4ai",
    author="Unclecode",
    author_email="unclecode@kidocode.com",
    license="MIT",
    packages=find_packages(),
    install_requires=requirements,
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
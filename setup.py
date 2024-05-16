from setuptools import setup, find_packages
from setuptools.command.install import install as _install
import subprocess

class InstallCommand(_install):
    def run(self):
        # Run the standard install first
        _install.run(self)
        # Now handle the dependencies manually
        self.manual_dependencies_install()

    def manual_dependencies_install(self):
        with open('requirements.txt') as f:
            dependencies = f.read().splitlines()
        for dependency in dependencies:
            subprocess.check_call([self.executable, '-m', 'pip', 'install', dependency])

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
    install_requires=[],  # Leave this empty to avoid default dependency resolution
    cmdclass={
        'install': InstallCommand,
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

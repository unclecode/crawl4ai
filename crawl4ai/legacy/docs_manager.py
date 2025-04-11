import shutil
from pathlib import Path
from typing import Final

import requests

from crawl4ai.async_logger import AsyncLogger
from .llmtxt import AsyncLLMTextManager

GIT_DOCS: Final = "https://api.github.com/repos/unclecode/crawl4ai/contents/docs"


class DocsManager:
    def __init__(self, logger=None):
        self.docs_dir = Path.home() / ".crawl4ai" / "docs"
        self.local_docs = Path(__file__).parent.parent.parent / "docs"
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or AsyncLogger(verbose=True)
        self.llm_text = AsyncLLMTextManager(self.docs_dir, self.logger)

    async def ensure_docs_exist(self):
        """Fetch docs if not present"""
        if not any(self.docs_dir.iterdir()):
            await self.fetch_docs()

    async def fetch_docs(self) -> bool:
        """Copy from local docs or download from GitHub"""
        try:
            # Remove existing markdown files.
            dirs: set[Path] = set()
            for file_path in self.docs_dir.glob("**/*.md"):
                dirs.add(file_path.parent)
                file_path.unlink()

            # Remove empty directories.
            for dir_path in sorted(dirs, reverse=True):
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()

            if self.local_docs.exists() and (any(self.local_docs.glob("**/*.md"))):
                # Copy from local docs.
                for file_path in self.local_docs.glob("**/*.md"):
                    rel_path = file_path.relative_to(self.local_docs)
                    dest_path = self.docs_dir / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest_path)
            else:
                # Download from GitHub.
                self.download_docs(GIT_DOCS)

            return True
        except Exception as e:
            self.logger.error(f"Failed to fetch docs: {str(e)}")
            raise

    def download_docs(self, url: str):
        """Download docs from GitHub"""

        response = requests.get(
            url,
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        response.raise_for_status()

        for item in response.json():
            if item["type"] == "dir":
                self.download_docs(item["url"])
            elif item["type"] == "file" and item["name"].endswith(".md"):
                path: str = item["path"]
                dest_path: Path = self.docs_dir / path.removeprefix("docs/")
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                content = requests.get(item["download_url"]).text
                with open(dest_path, "w", encoding="utf-8") as f:
                    f.write(content)

    def list(self) -> list[str]:
        """List available topics"""
        names = [file_path.stem for file_path in self.docs_dir.glob("*.md")]
        # Remove [0-9]+_ prefix
        names = [name.split("_", 1)[1] if name[0].isdigit() else name for name in names]
        # Exclude those end with .xs.md and .q.md
        names = [
            name
            for name in names
            if not name.endswith(".xs") and not name.endswith(".q")
        ]
        return names

    def generate(self, sections, mode="extended"):
        return self.llm_text.generate(sections, mode)

    def search(self, query: str, top_k: int = 5):
        return self.llm_text.search(query, top_k)

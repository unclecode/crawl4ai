import os
import requests
from pathlib import Path
from typing import Optional, List
from .async_logger import AsyncLogger
from .llmtxt import LLMTextManager

class DocsManager:
    BASE_URL = "https://raw.githubusercontent.com/unclecode/crawl4ai/main/docs/llm.txt"
    
    def __init__(self, logger: Optional[AsyncLogger] = None):
        self.docs_dir = Path.home() / ".crawl4ai" / "docs"
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger or AsyncLogger(verbose=True)
        self.llm_text = LLMTextManager(self.docs_dir, self.logger)
    
    async def ensure_docs_exist(self):
        """Ensure docs are downloaded, fetch if not present"""
        if not any(self.docs_dir.iterdir()):
            self.logger.info("Documentation not found, downloading...", tag="DOCS")
            await self.update_docs()
    
    async def update_docs(self) -> bool:
        """Always fetch latest docs"""
        try:
            self.logger.info("Fetching documentation files...", tag="DOCS")
            
            # Get file list
            response = requests.get(f"{self.BASE_URL}/files.json")
            response.raise_for_status()
            files = response.json()["files"]
            
            # Download each file
            for file in files:
                response = requests.get(f"{self.BASE_URL}/{file}")
                response.raise_for_status()
                
                file_path = self.docs_dir / file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                
                self.logger.debug(f"Downloaded {file}", tag="DOCS")
            
            self.logger.success("Documentation updated successfully", tag="DOCS")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update documentation: {str(e)}", tag="ERROR")
            raise
    
    # Delegate LLM text operations to LLMTextManager
    def get_file_map(self) -> dict:
        return self.llm_text.get_file_map()
    
    def concatenate_docs(self, sections: List[str], mode: str) -> str:
        return self.llm_text.concatenate_docs(sections, mode)
    
    def search_questions(self, query: str, top_k: int = 5) -> str:
        return self.llm_text.search_questions(query, top_k)

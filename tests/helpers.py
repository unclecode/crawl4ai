import os
import shutil
import tempfile
import time

from crawl4ai.cache_client import CacheClient

EXAMPLE_URL = "https://www.example.com"
EXAMPLE_RAW_HTML = """<!DOCTYPE html><html lang="en"><head><title>Example Domain</title><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#eee;width:60vw;margin:15vh auto;font-family:system-ui,sans-serif}h1{font-size:1.5em}div{opacity:0.8}a:link,a:visited{color:#348}</style></head><body><div><h1>Example Domain</h1><p>This domain is for use in documentation examples without needing permission. Avoid use in operations.</p><p><a href="https://iana.org/domains/example">Learn more</a></p></div>\n</body></html>"""

class TestCacheClient(CacheClient):
    """
    A simple local file-based cache client.
    File content format: <expiration_timestamp>\n---CACHE_DELIMITER---\n<content>
    """
    CACHE_DELIMITER = "\n---CACHE_DELIMITER---\n"
    
    def __init__(self):
        self.base_directory = tempfile.mkdtemp(prefix="crawl4ai_test_cache_")

    def _get_file_path(self, key: str) -> str:
        safe_key = key.replace(":", "_").replace("/", "_")
        return os.path.join(self.base_directory, safe_key)

    def get(self, key: str) -> str | None:
        file_path = self._get_file_path(key)
        if not os.path.exists(file_path):
            return None
        
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        
        cached = content.split(self.CACHE_DELIMITER, 1)
        expiration_time = float(cached[0])
        
        if time.time() > expiration_time:
            os.remove(file_path)
            return None
        
        return cached[1]

    def set(self, key: str, value: str, ttl_seconds: int) -> None:
        file_path = self._get_file_path(key)
        expiration_time = time.time() + ttl_seconds
        content = f"{expiration_time}{self.CACHE_DELIMITER}{value}"
        with open(file_path, "w+", encoding="utf-8") as f:
            f.write(content)

    def clear(self, prefix: str) -> None:
        for filename in os.listdir(self.base_directory):
            if filename.startswith(prefix.replace(":", "_")):
                file_path = os.path.join(self.base_directory, filename)
                os.remove(file_path)
    
    # === UTILITY METHODS FOR TESTING ===
    
    def count(self) -> int:
        return len(os.listdir(self.base_directory))

    def cleanup(self):
        shutil.rmtree(self.base_directory)


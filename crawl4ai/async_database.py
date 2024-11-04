import os
from pathlib import Path
import aiosqlite
import asyncio
from typing import Optional, Tuple, Dict
from contextlib import asynccontextmanager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(Path.home(), ".crawl4ai")
os.makedirs(DB_PATH, exist_ok=True)
DB_PATH = os.path.join(DB_PATH, "crawl4ai.db")

class AsyncDatabaseManager:
    def __init__(self, pool_size: int = 10, max_retries: int = 3):
        self.db_path = DB_PATH
        self.pool_size = pool_size
        self.max_retries = max_retries
        self.connection_pool: Dict[int, aiosqlite.Connection] = {}
        self.pool_lock = asyncio.Lock()
        self.connection_semaphore = asyncio.Semaphore(pool_size)
        
    async def initialize(self):
        """Initialize the database and connection pool"""
        await self.ainit_db()
        
    async def cleanup(self):
        """Cleanup connections when shutting down"""
        async with self.pool_lock:
            for conn in self.connection_pool.values():
                await conn.close()
            self.connection_pool.clear()

    @asynccontextmanager
    async def get_connection(self):
        """Connection pool manager"""
        async with self.connection_semaphore:
            task_id = id(asyncio.current_task())
            try:
                async with self.pool_lock:
                    if task_id not in self.connection_pool:
                        conn = await aiosqlite.connect(
                            self.db_path,
                            timeout=30.0
                        )
                        await conn.execute('PRAGMA journal_mode = WAL')
                        await conn.execute('PRAGMA busy_timeout = 5000')
                        self.connection_pool[task_id] = conn
                    
                yield self.connection_pool[task_id]
                
            except Exception as e:
                logger.error(f"Connection error: {e}")
                raise
            finally:
                async with self.pool_lock:
                    if task_id in self.connection_pool:
                        await self.connection_pool[task_id].close()
                        del self.connection_pool[task_id]

    async def execute_with_retry(self, operation, *args):
        """Execute database operations with retry logic"""
        for attempt in range(self.max_retries):
            try:
                async with self.get_connection() as db:
                    result = await operation(db, *args)
                    await db.commit()
                    return result
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Operation failed after {self.max_retries} attempts: {e}")
                    raise
                await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff

    async def ainit_db(self):
        """Initialize database schema"""
        async def _init(db):
            await db.execute('''
                CREATE TABLE IF NOT EXISTS crawled_data (
                    url TEXT PRIMARY KEY,
                    html TEXT,
                    cleaned_html TEXT,
                    markdown TEXT,
                    extracted_content TEXT,
                    success BOOLEAN,
                    media TEXT DEFAULT "{}",
                    links TEXT DEFAULT "{}",
                    metadata TEXT DEFAULT "{}",
                    screenshot TEXT DEFAULT ""
                )
            ''')
        
        await self.execute_with_retry(_init)
        await self.update_db_schema()

    async def update_db_schema(self):
        """Update database schema if needed"""
        async def _check_columns(db):
            cursor = await db.execute("PRAGMA table_info(crawled_data)")
            columns = await cursor.fetchall()
            return [column[1] for column in columns]

        column_names = await self.execute_with_retry(_check_columns)
        
        for column in ['media', 'links', 'metadata', 'screenshot']:
            if column not in column_names:
                await self.aalter_db_add_column(column)

    async def aalter_db_add_column(self, new_column: str):
        """Add new column to the database"""
        async def _alter(db):
            await db.execute(f'ALTER TABLE crawled_data ADD COLUMN {new_column} TEXT DEFAULT ""')
            logger.info(f"Added column '{new_column}' to the database.")

        await self.execute_with_retry(_alter)

    async def aget_cached_url(self, url: str) -> Optional[Tuple[str, str, str, str, str, str, str, bool, str]]:
        """Retrieve cached URL data"""
        async def _get(db):
            async with db.execute(
                'SELECT url, html, cleaned_html, markdown, extracted_content, success, media, links, metadata, screenshot FROM crawled_data WHERE url = ?',
                (url,)
            ) as cursor:
                return await cursor.fetchone()

        try:
            return await self.execute_with_retry(_get)
        except Exception as e:
            logger.error(f"Error retrieving cached URL: {e}")
            return None

    async def acache_url(self, url: str, html: str, cleaned_html: str, markdown: str, extracted_content: str, success: bool, media: str = "{}", links: str = "{}", metadata: str = "{}", screenshot: str = ""):
        """Cache URL data with retry logic"""
        async def _cache(db):
            await db.execute('''
                INSERT INTO crawled_data (url, html, cleaned_html, markdown, extracted_content, success, media, links, metadata, screenshot)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    html = excluded.html,
                    cleaned_html = excluded.cleaned_html,
                    markdown = excluded.markdown,
                    extracted_content = excluded.extracted_content,
                    success = excluded.success,
                    media = excluded.media,      
                    links = excluded.links,    
                    metadata = excluded.metadata,      
                    screenshot = excluded.screenshot
            ''', (url, html, cleaned_html, markdown, extracted_content, success, media, links, metadata, screenshot))

        try:
            await self.execute_with_retry(_cache)
        except Exception as e:
            logger.error(f"Error caching URL: {e}")

    async def aget_total_count(self) -> int:
        """Get total number of cached URLs"""
        async def _count(db):
            async with db.execute('SELECT COUNT(*) FROM crawled_data') as cursor:
                result = await cursor.fetchone()
                return result[0] if result else 0

        try:
            return await self.execute_with_retry(_count)
        except Exception as e:
            logger.error(f"Error getting total count: {e}")
            return 0

    async def aclear_db(self):
        """Clear all data from the database"""
        async def _clear(db):
            await db.execute('DELETE FROM crawled_data')

        try:
            await self.execute_with_retry(_clear)
        except Exception as e:
            logger.error(f"Error clearing database: {e}")

    async def aflush_db(self):
        """Drop the entire table"""
        async def _flush(db):
            await db.execute('DROP TABLE IF EXISTS crawled_data')

        try:
            await self.execute_with_retry(_flush)
        except Exception as e:
            logger.error(f"Error flushing database: {e}")

# Create a singleton instance
async_db_manager = AsyncDatabaseManager()
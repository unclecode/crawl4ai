import os
from pathlib import Path
import aiosqlite
import asyncio
from typing import Optional, Tuple, Dict
from contextlib import asynccontextmanager
import logging
import json  # Added for serialization/deserialization
from .utils import ensure_content_dirs, generate_content_hash
from .models import CrawlResult
import xxhash
import aiofiles
from .config import NEED_MIGRATION
from .version_manager import VersionManager
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(Path.home(), ".crawl4ai")
os.makedirs(DB_PATH, exist_ok=True)
DB_PATH = os.path.join(DB_PATH, "crawl4ai.db")

class AsyncDatabaseManager:
    def __init__(self, pool_size: int = 10, max_retries: int = 3):
        self.db_path = DB_PATH
        self.content_paths = ensure_content_dirs(os.path.dirname(DB_PATH))
        self.pool_size = pool_size
        self.max_retries = max_retries
        self.connection_pool: Dict[int, aiosqlite.Connection] = {}
        self.pool_lock = asyncio.Lock()
        self.connection_semaphore = asyncio.Semaphore(pool_size)
        self._initialized = False  
        self.version_manager = VersionManager()
        
        
    async def initialize(self):
        """Initialize the database and connection pool"""
        try:
            logger.info("Initializing database...")
            # Ensure the database file exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            # Check if version update is needed
            needs_update = self.version_manager.needs_update()
            
            # Always ensure base table exists
            await self.ainit_db()
            
            # Verify the table exists
            async def verify_table(db):
                async with db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='crawled_data'"
                ) as cursor:
                    result = await cursor.fetchone()
                    if not result:
                        raise Exception("crawled_data table was not created")
                    
            await self.execute_with_retry(verify_table)
            
            # If version changed or fresh install, run updates
            if needs_update:
                logger.info("New version detected, running updates...")
                await self.update_db_schema()
                from .migrations import run_migration  # Import here to avoid circular imports
                await run_migration()
                self.version_manager.update_version()  # Update stored version after successful migration
                logger.info("Version update completed successfully")
            else:
                logger.info("Database initialization completed successfully")
                
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            logger.info("Database will be initialized on first use")
            raise
            
    async def cleanup(self):
        """Cleanup connections when shutting down"""
        async with self.pool_lock:
            for conn in self.connection_pool.values():
                await conn.close()
            self.connection_pool.clear()

    @asynccontextmanager
    async def get_connection(self):
        """Connection pool manager"""
        if not self._initialized:
            async with self.pool_lock:  # Prevent multiple simultaneous initializations
                if not self._initialized:  # Double-check after acquiring lock
                    await self.initialize()
                    self._initialized = True

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
                    screenshot TEXT DEFAULT "",
                    response_headers TEXT DEFAULT "{}",
                    downloaded_files TEXT DEFAULT "{}"  -- New column added
                )
            ''')
        
        await self.execute_with_retry(_init)
        

    async def update_db_schema(self):
        """Update database schema if needed"""
        async def _check_columns(db):
            cursor = await db.execute("PRAGMA table_info(crawled_data)")
            columns = await cursor.fetchall()
            return [column[1] for column in columns]

        column_names = await self.execute_with_retry(_check_columns)
        
        # List of new columns to add
        new_columns = ['media', 'links', 'metadata', 'screenshot', 'response_headers', 'downloaded_files']
        
        for column in new_columns:
            if column not in column_names:
                await self.aalter_db_add_column(column)

    async def aalter_db_add_column(self, new_column: str):
        """Add new column to the database"""
        async def _alter(db):
            if new_column == 'response_headers':
                await db.execute(f'ALTER TABLE crawled_data ADD COLUMN {new_column} TEXT DEFAULT "{{}}"')
            else:
                await db.execute(f'ALTER TABLE crawled_data ADD COLUMN {new_column} TEXT DEFAULT ""')
            logger.info(f"Added column '{new_column}' to the database.")

        await self.execute_with_retry(_alter)

    async def aget_cached_url(self, url: str) -> Optional[CrawlResult]:
        """Retrieve cached URL data as CrawlResult"""
        async def _get(db):
            async with db.execute(
                'SELECT * FROM crawled_data WHERE url = ?', (url,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                    
                # Get column names
                columns = [description[0] for description in cursor.description]
                # Create dict from row data
                row_dict = dict(zip(columns, row))
                
                # Load content from files using stored hashes
                content_fields = {
                    'html': row_dict['html'],
                    'cleaned_html': row_dict['cleaned_html'],
                    'markdown': row_dict['markdown'],
                    'extracted_content': row_dict['extracted_content'],
                    'screenshot': row_dict['screenshot']
                }
                
                for field, hash_value in content_fields.items():
                    if hash_value:
                        content = await self._load_content(
                            hash_value, 
                            field.split('_')[0]  # Get content type from field name
                        )
                        row_dict[field] = content or ""
                    else:
                        row_dict[field] = ""

                # Parse JSON fields
                json_fields = ['media', 'links', 'metadata', 'response_headers']
                for field in json_fields:
                    try:
                        row_dict[field] = json.loads(row_dict[field]) if row_dict[field] else {}
                    except json.JSONDecodeError:
                        row_dict[field] = {}

                # Parse downloaded_files
                try:
                    row_dict['downloaded_files'] = json.loads(row_dict['downloaded_files']) if row_dict['downloaded_files'] else []
                except json.JSONDecodeError:
                    row_dict['downloaded_files'] = []

                # Remove any fields not in CrawlResult model
                valid_fields = CrawlResult.__annotations__.keys()
                filtered_dict = {k: v for k, v in row_dict.items() if k in valid_fields}
                
                return CrawlResult(**filtered_dict)

        try:
            return await self.execute_with_retry(_get)
        except Exception as e:
            logger.error(f"Error retrieving cached URL: {e}")
            return None

    async def acache_url(self, result: CrawlResult):
        """Cache CrawlResult data"""
        # Store content files and get hashes
        content_map = {
            'html': (result.html, 'html'),
            'cleaned_html': (result.cleaned_html or "", 'cleaned'),
            'markdown': (result.markdown or "", 'markdown'),
            'extracted_content': (result.extracted_content or "", 'extracted'),
            'screenshot': (result.screenshot or "", 'screenshots')
        }
        
        content_hashes = {}
        for field, (content, content_type) in content_map.items():
            content_hashes[field] = await self._store_content(content, content_type)

        async def _cache(db):
            await db.execute('''
                INSERT INTO crawled_data (
                    url, html, cleaned_html, markdown,
                    extracted_content, success, media, links, metadata,
                    screenshot, response_headers, downloaded_files
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    html = excluded.html,
                    cleaned_html = excluded.cleaned_html,
                    markdown = excluded.markdown,
                    extracted_content = excluded.extracted_content,
                    success = excluded.success,
                    media = excluded.media,
                    links = excluded.links,
                    metadata = excluded.metadata,
                    screenshot = excluded.screenshot,
                    response_headers = excluded.response_headers,
                    downloaded_files = excluded.downloaded_files
            ''', (
                result.url,
                content_hashes['html'],
                content_hashes['cleaned_html'],
                content_hashes['markdown'],
                content_hashes['extracted_content'],
                result.success,
                json.dumps(result.media),
                json.dumps(result.links),
                json.dumps(result.metadata or {}),
                content_hashes['screenshot'],
                json.dumps(result.response_headers or {}),
                json.dumps(result.downloaded_files or [])
            ))

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
            
                
    async def _store_content(self, content: str, content_type: str) -> str:
        """Store content in filesystem and return hash"""
        if not content:
            return ""
            
        content_hash = generate_content_hash(content)
        file_path = os.path.join(self.content_paths[content_type], content_hash)
        
        # Only write if file doesn't exist
        if not os.path.exists(file_path):
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
                
        return content_hash

    async def _load_content(self, content_hash: str, content_type: str) -> Optional[str]:
        """Load content from filesystem by hash"""
        if not content_hash:
            return None
            
        file_path = os.path.join(self.content_paths[content_type], content_hash)
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                return await f.read()
        except:
            logger.error(f"Failed to load content: {file_path}")
            return None

# Create a singleton instance
async_db_manager = AsyncDatabaseManager()

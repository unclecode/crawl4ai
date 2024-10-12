import os
from pathlib import Path
import aiosqlite
import asyncio
from typing import Optional, Tuple

DB_PATH = os.path.join(Path.home(), ".crawl4ai")
os.makedirs(DB_PATH, exist_ok=True)
DB_PATH = os.path.join(DB_PATH, "crawl4ai.db")

class AsyncDatabaseManager:
    def __init__(self):
        self.db_path = DB_PATH

    async def ainit_db(self):
        async with aiosqlite.connect(self.db_path) as db:
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
            await db.commit()
        await self.update_db_schema()

    async def update_db_schema(self):
        async with aiosqlite.connect(self.db_path) as db:
            # Check if the 'media' column exists
            cursor = await db.execute("PRAGMA table_info(crawled_data)")
            columns = await cursor.fetchall()
            column_names = [column[1] for column in columns]
            
            if 'media' not in column_names:
                await self.aalter_db_add_column('media')
            
            # Check for other missing columns and add them if necessary
            for column in ['links', 'metadata', 'screenshot']:
                if column not in column_names:
                    await self.aalter_db_add_column(column)

    async def aalter_db_add_column(self, new_column: str):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(f'ALTER TABLE crawled_data ADD COLUMN {new_column} TEXT DEFAULT ""')
                await db.commit()
            print(f"Added column '{new_column}' to the database.")
        except Exception as e:
            print(f"Error altering database to add {new_column} column: {e}")

    async def aget_cached_url(self, url: str) -> Optional[Tuple[str, str, str, str, str, str, str, bool, str]]:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('SELECT url, html, cleaned_html, markdown, extracted_content, success, media, links, metadata, screenshot FROM crawled_data WHERE url = ?', (url,)) as cursor:
                    return await cursor.fetchone()
        except Exception as e:
            print(f"Error retrieving cached URL: {e}")
            return None

    async def acache_url(self, url: str, html: str, cleaned_html: str, markdown: str, extracted_content: str, success: bool, media: str = "{}", links: str = "{}", metadata: str = "{}", screenshot: str = ""):
        try:
            async with aiosqlite.connect(self.db_path) as db:
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
                await db.commit()
        except Exception as e:
            print(f"Error caching URL: {e}")

    async def aget_total_count(self) -> int:
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute('SELECT COUNT(*) FROM crawled_data') as cursor:
                    result = await cursor.fetchone()
                    return result[0] if result else 0
        except Exception as e:
            print(f"Error getting total count: {e}")
            return 0

    async def aclear_db(self):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('DELETE FROM crawled_data')
                await db.commit()
        except Exception as e:
            print(f"Error clearing database: {e}")

    async def aflush_db(self):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('DROP TABLE IF EXISTS crawled_data')
                await db.commit()
        except Exception as e:
            print(f"Error flushing database: {e}")

async_db_manager = AsyncDatabaseManager()
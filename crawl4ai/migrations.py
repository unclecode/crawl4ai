import os
import asyncio
from pathlib import Path
import aiosqlite
from typing import Optional
import xxhash
import aiofiles
import shutil
from datetime import datetime
from .async_logger import AsyncLogger, LogLevel

# Initialize logger
logger = AsyncLogger(log_level=LogLevel.DEBUG, verbose=True)

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


class DatabaseMigration:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.content_paths = self._ensure_content_dirs(os.path.dirname(db_path))

    def _ensure_content_dirs(self, base_path: str) -> dict:
        dirs = {
            "html": "html_content",
            "cleaned": "cleaned_html",
            "markdown": "markdown_content",
            "extracted": "extracted_content",
            "screenshots": "screenshots",
        }
        content_paths = {}
        for key, dirname in dirs.items():
            path = os.path.join(base_path, dirname)
            os.makedirs(path, exist_ok=True)
            content_paths[key] = path
        return content_paths

    def _generate_content_hash(self, content: str) -> str:
        x = xxhash.xxh64()
        x.update(content.encode())
        content_hash = x.hexdigest()
        return content_hash
        # return hashlib.sha256(content.encode()).hexdigest()

    async def _store_content(self, content: str, content_type: str) -> str:
        if not content:
            return ""

        content_hash = self._generate_content_hash(content)
        file_path = os.path.join(self.content_paths[content_type], content_hash)

        if not os.path.exists(file_path):
            async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                await f.write(content)

        return content_hash

    async def migrate_database(self):
        """Migrate existing database to file-based storage"""
        # logger.info("Starting database migration...")
        logger.info("Starting database migration...", tag="INIT")

        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get all rows
                async with db.execute(
                    """SELECT url, html, cleaned_html, markdown, 
                       extracted_content, screenshot FROM crawled_data"""
                ) as cursor:
                    rows = await cursor.fetchall()

                migrated_count = 0
                for row in rows:
                    (
                        url,
                        html,
                        cleaned_html,
                        markdown,
                        extracted_content,
                        screenshot,
                    ) = row

                    # Store content in files and get hashes
                    html_hash = await self._store_content(html, "html")
                    cleaned_hash = await self._store_content(cleaned_html, "cleaned")
                    markdown_hash = await self._store_content(markdown, "markdown")
                    extracted_hash = await self._store_content(
                        extracted_content, "extracted"
                    )
                    screenshot_hash = await self._store_content(
                        screenshot, "screenshots"
                    )

                    # Update database with hashes
                    await db.execute(
                        """
                        UPDATE crawled_data 
                        SET html = ?, 
                            cleaned_html = ?,
                            markdown = ?,
                            extracted_content = ?,
                            screenshot = ?
                        WHERE url = ?
                    """,
                        (
                            html_hash,
                            cleaned_hash,
                            markdown_hash,
                            extracted_hash,
                            screenshot_hash,
                            url,
                        ),
                    )

                    migrated_count += 1
                    if migrated_count % 100 == 0:
                        logger.info(f"Migrated {migrated_count} records...", tag="INIT")

                await db.commit()
                logger.success(
                    f"Migration completed. {migrated_count} records processed.",
                    tag="COMPLETE",
                )

        except Exception as e:
            # logger.error(f"Migration failed: {e}")
            logger.error(
                message="Migration failed: {error}",
                tag="ERROR",
                params={"error": str(e)},
            )
            raise e


async def backup_database(db_path: str) -> str:
    """Create backup of existing database"""
    if not os.path.exists(db_path):
        logger.info("No existing database found. Skipping backup.", tag="INIT")
        return None

    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"

    try:
        # Wait for any potential write operations to finish
        await asyncio.sleep(1)

        # Create backup
        shutil.copy2(db_path, backup_path)
        logger.info(f"Database backup created at: {backup_path}", tag="COMPLETE")
        return backup_path
    except Exception as e:
        # logger.error(f"Backup failed: {e}")
        logger.error(
            message="Migration failed: {error}", tag="ERROR", params={"error": str(e)}
        )
        raise e


async def run_migration(db_path: Optional[str] = None):
    """Run database migration"""
    if db_path is None:
        db_path = os.path.join(Path.home(), ".crawl4ai", "crawl4ai.db")

    if not os.path.exists(db_path):
        logger.info("No existing database found. Skipping migration.", tag="INIT")
        return

    # Create backup first
    backup_path = await backup_database(db_path)
    if not backup_path:
        return

    migration = DatabaseMigration(db_path)
    await migration.migrate_database()


def main():
    """CLI entry point for migration"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Migrate Crawl4AI database to file-based storage"
    )
    parser.add_argument("--db-path", help="Custom database path")
    args = parser.parse_args()

    asyncio.run(run_migration(args.db_path))


if __name__ == "__main__":
    main()

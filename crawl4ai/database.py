import os
from pathlib import Path
import sqlite3
from typing import Optional
from typing import Optional, Tuple

DB_PATH = os.path.join(Path.home(), ".crawl4ai")
os.makedirs(DB_PATH, exist_ok=True)
DB_PATH = os.path.join(DB_PATH, "crawl4ai.db")
        
def init_db(db_path: str):
    global DB_PATH
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawled_data (
            url TEXT PRIMARY KEY,
            html TEXT,
            cleaned_html TEXT,
            markdown TEXT,
            parsed_json TEXT,
            success BOOLEAN
        )
    ''')
    conn.commit()
    conn.close()
    DB_PATH = db_path

def check_db_path():
    if not DB_PATH:
        raise ValueError("Database path is not set or is empty.")

def get_cached_url(url: str) -> Optional[Tuple[str, str, str, str, str, bool]]:
    check_db_path()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT url, html, cleaned_html, markdown, parsed_json, success FROM crawled_data WHERE url = ?', (url,))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        print(f"Error retrieving cached URL: {e}")
        return None

def cache_url(url: str, html: str, cleaned_html: str, markdown: str, parsed_json: str, success: bool):
    check_db_path()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO crawled_data (url, html, cleaned_html, markdown, parsed_json, success)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                html = excluded.html,
                cleaned_html = excluded.cleaned_html,
                markdown = excluded.markdown,
                parsed_json = excluded.parsed_json,
                success = excluded.success
        ''', (url, html, cleaned_html, markdown, parsed_json, success))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error caching URL: {e}")

def get_total_count() -> int:
    check_db_path()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM crawled_data')
        result = cursor.fetchone()
        conn.close()
        return result[0]
    except Exception as e:
        print(f"Error getting total count: {e}")
        return 0

def clear_db():
    check_db_path()
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM crawled_data')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error clearing database: {e}")
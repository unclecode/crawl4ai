import sqlite3
from typing import Optional

def init_db(db_path: str):
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

def get_cached_url(db_path: str, url: str) -> Optional[tuple]:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT url, html, cleaned_html, markdown, parsed_json, success FROM crawled_data WHERE url = ?', (url,))
    result = cursor.fetchone()
    conn.close()
    return result

def cache_url(db_path: str, url: str, html: str, cleaned_html: str, markdown: str, parsed_json: str, success: bool):
    conn = sqlite3.connect(db_path)
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
    ''', (str(url), html, cleaned_html, markdown, parsed_json, success))
    conn.commit()
    conn.close()
    
def get_total_count(db_path: str) -> int:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM crawled_data')
        result = cursor.fetchone()
        conn.close()
        return result[0]
    except Exception as e:
        return 0
    
# Crete function to cler the database
def clear_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM crawled_data')
    conn.commit()
    conn.close()
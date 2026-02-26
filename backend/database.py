"""SQLite database setup and initialization."""

import sqlite3
import os
from pathlib import Path
from passlib.context import CryptContext

DB_PATH = Path(__file__).parent / "intellifetch.db"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SUPER_ADMIN_USERNAME = os.environ.get("SUPER_ADMIN_USERNAME", "superadmin")
SUPER_ADMIN_PASSWORD = os.environ.get("SUPER_ADMIN_PASSWORD", "superadmin123")


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('super_admin', 'admin', 'user')),
            created_by INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (created_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now')),
            started_at TEXT,
            finished_at TEXT,
            article_count INTEGER DEFAULT 0,
            error TEXT,
            output_dir TEXT,
            config TEXT,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_name TEXT NOT NULL,
            url TEXT NOT NULL,
            cron TEXT NOT NULL,
            recipients TEXT,
            enabled INTEGER DEFAULT 1,
            last_run TEXT,
            next_run TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()

    # Seed default settings if not present
    defaults = {
        "groq_api_key": "",
        "llm_provider": "groq/llama-3.3-70b-versatile",
        "smtp_host": "",
        "smtp_port": "587",
        "smtp_user": "",
        "smtp_password": "",
        "default_max_scrolls": "3",
        "default_max_inner_pages": "5",
        "default_content_limit": "10000",
    }
    for key, value in defaults.items():
        cursor.execute(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value)
        )
    conn.commit()

    # Seed super admin if not present
    existing = cursor.execute(
        "SELECT id FROM users WHERE role = 'super_admin'"
    ).fetchone()
    if not existing:
        hashed = pwd_context.hash(SUPER_ADMIN_PASSWORD)
        cursor.execute(
            """INSERT OR IGNORE INTO users (username, email, hashed_password, role, created_by)
               VALUES (?, ?, ?, 'super_admin', NULL)""",
            (SUPER_ADMIN_USERNAME, f"{SUPER_ADMIN_USERNAME}@intellifetch.local", hashed),
        )
        conn.commit()

    conn.close()

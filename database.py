# database.py - all SQLite operations for storing baselines and changes

import os
import sqlite3
from datetime import datetime, timezone


def connect(db_path):
    """Open a connection to the SQLite database. Create tables if needed."""

    # make sure the folder exists
    folder = os.path.dirname(db_path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # create tables if this is a fresh database
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS baselines (
            file_path   TEXT PRIMARY KEY,
            hash        TEXT NOT NULL,
            size        INTEGER,
            modified_at TEXT,
            owner       TEXT,
            permissions TEXT,
            created_at  TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS changes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path   TEXT NOT NULL,
            change_type TEXT NOT NULL,
            old_hash    TEXT,
            new_hash    TEXT,
            timestamp   TEXT NOT NULL,
            hostname    TEXT
        )
    """)

    conn.commit()
    return conn


def save_baseline(conn, file_path, file_hash, size, modified_at, owner, permissions):
    """Save one file entry to the baselines table."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO baselines
        (file_path, hash, size, modified_at, owner, permissions, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (file_path, file_hash, size, modified_at, owner, permissions, now))

    conn.commit()


def get_baseline(conn, file_path):
    """Get the saved baseline for one file. Returns a dict or None."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM baselines WHERE file_path = ?", (file_path,))
    row = cursor.fetchone()
    if row:
        return dict(row)
    return None


def get_all_baselines(conn):
    """Get all baseline entries as a dict keyed by file path."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM baselines")
    result = {}
    for row in cursor.fetchall():
        result[row["file_path"]] = dict(row)
    return result


def count_baselines(conn):
    """Count how many files are in the baseline."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM baselines")
    return cursor.fetchone()[0]


def clear_baselines(conn):
    """Delete all baseline entries. Used when resetting."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM baselines")
    conn.commit()


def remove_baseline(conn, file_path):
    """Remove one file from the baseline."""
    cursor = conn.cursor()
    cursor.execute("DELETE FROM baselines WHERE file_path = ?", (file_path,))
    conn.commit()


def record_change(conn, file_path, change_type, old_hash, new_hash, hostname):
    """Save a detected change to the changes table."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO changes (file_path, change_type, old_hash, new_hash, timestamp, hostname)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (file_path, change_type, old_hash, new_hash, now, hostname))

    conn.commit()


def get_recent_changes(conn, limit=20):
    """Get the most recent changes from the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM changes ORDER BY id DESC LIMIT ?", (limit,))
    return [dict(row) for row in cursor.fetchall()]

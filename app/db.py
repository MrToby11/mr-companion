# app/db.py
# SQLite connection manager.
# All routers call get_db() to obtain a connection for the duration of a request.
# Foreign keys are enabled per-connection (SQLite requires this each time).
# seed_event_types() is called once on app startup to populate the EventType table.

import sqlite3
from contextlib import contextmanager

DB_PATH = "mr_companion.db"


@contextmanager
def get_db():
    """
    Yield a SQLite connection with foreign keys enabled and rows accessible by column name.
    Commits on success, rolls back on any exception, and always closes the connection.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def seed_event_types():
    """
    Insert the built-in EventType rows on startup.
    INSERT OR IGNORE means this is safe to call every time — it won't duplicate rows.
    """
    with get_db() as db:
        db.executemany(
            "INSERT OR IGNORE INTO EventType (eventTypeID, name, severityLevel) VALUES (?, ?, ?)",
            [
                (1, "Fall Detected",  "critical"),
                (2, "Battery Low",    "info"),
                (3, "Device Offline", "info"),
            ],
        )

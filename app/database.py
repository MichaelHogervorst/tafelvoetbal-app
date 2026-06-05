"""SQLite database access.

All database access goes through this module so that the storage backend
can be swapped later (e.g. to Postgres) by changing only this file.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path("data/tafelvoetbal.db")


def get_connection() -> sqlite3.Connection:
    """Open a SQLite connection with sensible defaults."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    """Context manager that commits on success and rolls back on error."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create the players and games tables if they don't exist yet."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS players (
                player_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL UNIQUE,
                wins        INTEGER NOT NULL DEFAULT 0,
                losses      INTEGER NOT NULL DEFAULT 0,
                score       REAL    NOT NULL DEFAULT 0.0,
                elo         INTEGER NOT NULL DEFAULT 1200
            );

            CREATE TABLE IF NOT EXISTS games (
                game_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                t1p1            TEXT    NOT NULL,
                t1p2            TEXT    NOT NULL,
                t2p1            TEXT    NOT NULL,
                t2p2            TEXT    NOT NULL,
                points_team1    INTEGER NOT NULL,
                points_team2    INTEGER NOT NULL,
                insertion_date  TEXT    NOT NULL DEFAULT (DATE('now'))
            );
        """)

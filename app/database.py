"""SQLite database access.

All database access goes through this module so that the storage backend
can be swapped later (e.g. to Postgres) by changing only this file.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import trueskill as _ts_lib

from app.config import settings

# TrueSkill environment — no draws in foosball.
_TS = _ts_lib.TrueSkill(draw_probability=0.0)

DB_PATH = Path(settings.db_path)


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
                elo         INTEGER NOT NULL DEFAULT 1200,
                ts_mu       REAL    NOT NULL DEFAULT 25.0,
                ts_sigma    REAL    NOT NULL DEFAULT 8.333
            );

            CREATE TABLE IF NOT EXISTS games (
                game_id         INTEGER PRIMARY KEY AUTOINCREMENT,
                t1p1            TEXT    NOT NULL,
                t1p2            TEXT    NOT NULL DEFAULT '',
                t2p1            TEXT    NOT NULL,
                t2p2            TEXT    NOT NULL DEFAULT '',
                points_team1    INTEGER NOT NULL,
                points_team2    INTEGER NOT NULL,
                insertion_date  TEXT    NOT NULL DEFAULT (DATE('now'))
            );
        """)


def migrate_db() -> None:
    """Add columns introduced after the initial schema (safe to run on every startup)."""
    with get_db() as conn:
        for col, definition in [
            ("ts_mu", "REAL NOT NULL DEFAULT 25.0"),
            ("ts_sigma", "REAL NOT NULL DEFAULT 8.333"),
        ]:
            try:
                conn.execute(f"ALTER TABLE players ADD COLUMN {col} {definition}")
            except sqlite3.OperationalError:
                pass  # column already exists


def get_leaderboard() -> list[sqlite3.Row]:
    """Return all players sorted by score descending."""
    with get_db() as conn:
        return conn.execute("""
            SELECT name, wins, losses, ROUND(score, 1) AS score, elo,
                   ROUND(ts_mu, 1) AS ts_mu, ROUND(ts_sigma, 2) AS ts_sigma,
                   ROUND(ts_mu - 3 * ts_sigma, 1) AS ts_rating
            FROM players
            WHERE wins + losses > 0
            ORDER BY score DESC, wins DESC
        """).fetchall()


def get_player_names() -> list[str]:
    """Return all known player names for autocomplete."""
    with get_db() as conn:
        rows = conn.execute("SELECT name FROM players ORDER BY name").fetchall()
        return [r["name"] for r in rows]


def get_game_history() -> list[sqlite3.Row]:
    """Return all games ordered by most recent first."""
    with get_db() as conn:
        return conn.execute("""
            SELECT game_id, t1p1, t1p2, t2p1, t2p2,
                   points_team1, points_team2, insertion_date
            FROM games
            ORDER BY game_id DESC
        """).fetchall()


def get_player_detail(name: str) -> dict | None:
    """Return stats and game history for a single player, or None if not found."""
    with get_db() as conn:
        player = conn.execute(
            """SELECT name, wins, losses, ROUND(score, 1) AS score, elo,
                      ROUND(ts_mu, 1) AS ts_mu, ROUND(ts_sigma, 2) AS ts_sigma,
                      ROUND(ts_mu - 3 * ts_sigma, 1) AS ts_rating
               FROM players WHERE name = ?""",
            (name,),
        ).fetchone()
        if player is None:
            return None

        games = conn.execute("""
            SELECT game_id, t1p1, t1p2, t2p1, t2p2,
                   points_team1, points_team2, insertion_date,
                   CASE
                       WHEN (t1p1 = :n OR t1p2 = :n) AND points_team1 > points_team2 THEN 1
                       WHEN (t2p1 = :n OR t2p2 = :n) AND points_team2 > points_team1 THEN 1
                       ELSE 0
                   END AS won
            FROM games
            WHERE t1p1 = :n OR t1p2 = :n OR t2p1 = :n OR t2p2 = :n
            ORDER BY game_id DESC
        """, {"n": name}).fetchall()

        return {"player": player, "games": games}


# ---------------------------------------------------------------------------
# Elo helpers
# ---------------------------------------------------------------------------

def _get_elo(conn: sqlite3.Connection, name: str) -> int:
    row = conn.execute("SELECT elo FROM players WHERE name = ?", (name,)).fetchone()
    return int(row["elo"]) if row else 1200


def _calc_elo(current: int, opp_avg: float, won: bool, k: int = 32) -> int:
    expected = 1 / (1 + 10 ** ((opp_avg - current) / 400))
    return round(current + k * ((1 if won else 0) - expected))


def _upsert_player(conn: sqlite3.Connection, name: str, won: bool, new_elo: int) -> None:
    row = conn.execute(
        "SELECT wins, losses FROM players WHERE name = ?", (name,)
    ).fetchone()
    if row:
        wins = row["wins"] + (1 if won else 0)
        losses = row["losses"] + (0 if won else 1)
        score = wins / (wins + losses) * 100
        conn.execute(
            "UPDATE players SET wins=?, losses=?, score=?, elo=? WHERE name=?",
            (wins, losses, score, new_elo, name),
        )
    else:
        wins, losses = (1, 0) if won else (0, 1)
        score = 100.0 if won else 0.0
        conn.execute(
            "INSERT INTO players (name, wins, losses, score, elo) VALUES (?,?,?,?,?)",
            (name, wins, losses, score, new_elo),
        )


# ---------------------------------------------------------------------------
# Game submission
# ---------------------------------------------------------------------------

def submit_game(t1p1: str, t1p2: str, t2p1: str, t2p2: str, t1_score: int, t2_score: int) -> None:
    """Insert game, then update all four players' stats and Elo."""
    if t1_score == t2_score:
        raise ValueError("Scores cannot be equal — there must be a winner.")
    team1_won = t1_score > t2_score

    with get_db() as conn:
        # Current Elos
        e1a, e1b = _get_elo(conn, t1p1), _get_elo(conn, t1p2)
        e2a, e2b = _get_elo(conn, t2p1), _get_elo(conn, t2p2)
        avg1, avg2 = (e1a + e1b) / 2, (e2a + e2b) / 2

        # New Elos
        new_e1a = _calc_elo(e1a, avg2, team1_won)
        new_e1b = _calc_elo(e1b, avg2, team1_won)
        new_e2a = _calc_elo(e2a, avg1, not team1_won)
        new_e2b = _calc_elo(e2b, avg1, not team1_won)

        # Insert game with real scores
        conn.execute(
            """INSERT INTO games (t1p1, t1p2, t2p1, t2p2, points_team1, points_team2)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (t1p1, t1p2, t2p1, t2p2, t1_score, t2_score),
        )

        # Upsert all four players
        _upsert_player(conn, t1p1, team1_won, new_e1a)
        _upsert_player(conn, t1p2, team1_won, new_e1b)
        _upsert_player(conn, t2p1, not team1_won, new_e2a)
        _upsert_player(conn, t2p2, not team1_won, new_e2b)

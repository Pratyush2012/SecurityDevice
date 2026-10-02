"""SQLite storage for events.

Timestamps are stored as UTC ISO-8601 strings. Same format + same timezone means
string order equals time order, so SQL range filters and ORDER BY work on text.
Embeddings go in a separate table/index on Day 6.
"""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from src.schemas import Event, EventCreate

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp     TEXT    NOT NULL,
    source        TEXT    NOT NULL,
    track_id      INTEGER,
    zone          TEXT,
    dwell_seconds REAL    NOT NULL DEFAULT 0,
    identity      TEXT    NOT NULL DEFAULT 'unknown',
    snapshot_path TEXT,
    description   TEXT,
    activity      TEXT,
    threat_level  TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_zone ON events(zone);
"""

COLUMNS = [
    "timestamp", "source", "track_id", "zone", "dwell_seconds", "identity",
    "snapshot_path", "description", "activity", "threat_level",
]  # fmt: skip


def connect(path: str) -> sqlite3.Connection:
    """Open the database (creating file and tables if needed)."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    # FastAPI may open the connection in one worker thread and use it in another
    # (still one request at a time), so allow cross-thread use.
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # rows behave like dicts
    conn.executescript(SCHEMA)
    return conn


def _to_utc_text(ts: datetime) -> str:
    return ts.astimezone(UTC).isoformat()


def insert_event(conn: sqlite3.Connection, event: EventCreate) -> Event:
    values = event.model_dump()
    values["timestamp"] = _to_utc_text(event.timestamp)
    placeholders = ", ".join("?" for _ in COLUMNS)
    with conn:  # commits on success, rolls back on error
        cur = conn.execute(
            f"INSERT INTO events ({', '.join(COLUMNS)}) VALUES ({placeholders})",
            [values[c] for c in COLUMNS],
        )
    return get_event(conn, cur.lastrowid)


def get_event(conn: sqlite3.Connection, event_id: int) -> Event | None:
    row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    return Event(**row) if row else None


def list_events(
    conn: sqlite3.Connection,
    start: datetime | None = None,
    end: datetime | None = None,
    zone: str | None = None,
    limit: int = 100,
) -> list[Event]:
    """Newest first. start is inclusive, end is exclusive."""
    where, params = [], []
    if start is not None:
        where.append("timestamp >= ?")
        params.append(_to_utc_text(start))
    if end is not None:
        where.append("timestamp < ?")
        params.append(_to_utc_text(end))
    if zone is not None:
        where.append("zone = ?")
        params.append(zone)
    sql = "SELECT * FROM events"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    return [Event(**row) for row in conn.execute(sql, params)]

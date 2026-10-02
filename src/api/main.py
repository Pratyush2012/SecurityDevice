"""HTTP API for events. Run: uvicorn src.api.main:app --reload"""

import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import AwareDatetime

from src import db
from src.config import settings
from src.schemas import Event, EventCreate

app = FastAPI(title="Security Event Assistant")


def get_conn() -> Iterator[sqlite3.Connection]:
    """One connection per request, closed afterwards. Tests override this."""
    conn = db.connect(settings.database_path)
    try:
        yield conn
    finally:
        conn.close()


Conn = Annotated[sqlite3.Connection, Depends(get_conn)]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/events", status_code=201)
def create_event(event: EventCreate, conn: Conn) -> Event:
    return db.insert_event(conn, event)


@app.get("/events")
def list_events(
    conn: Conn,
    start: AwareDatetime | None = None,
    end: AwareDatetime | None = None,
    zone: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[Event]:
    return db.list_events(conn, start=start, end=end, zone=zone, limit=limit)


@app.get("/events/{event_id}")
def get_event(event_id: int, conn: Conn) -> Event:
    event = db.get_event(conn, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

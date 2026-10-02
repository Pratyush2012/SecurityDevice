from datetime import UTC, datetime

import pytest

from src.db import connect, get_event, insert_event, list_events
from src.schemas import EventCreate


@pytest.fixture
def conn(tmp_path):
    c = connect(str(tmp_path / "test.db"))
    yield c
    c.close()


def make(ts: str, zone: str = "door") -> EventCreate:
    return EventCreate(timestamp=ts, source="synthetic", zone=zone)


def test_insert_assigns_id_and_roundtrips(conn):
    e = insert_event(conn, make("2026-10-02T21:00:00+02:00"))
    assert e.id == 1
    assert get_event(conn, 1) == e
    # stored as UTC, same instant
    assert e.timestamp == datetime(2026, 10, 2, 19, 0, tzinfo=UTC)


def test_get_missing_returns_none(conn):
    assert get_event(conn, 999) is None


def test_list_filters_by_time_and_zone(conn):
    insert_event(conn, make("2026-10-01T10:00:00+00:00"))
    insert_event(conn, make("2026-10-02T10:00:00+00:00"))
    insert_event(conn, make("2026-10-02T12:00:00+00:00", zone="garden"))
    insert_event(conn, make("2026-10-03T10:00:00+00:00"))

    day = list_events(
        conn,
        start=datetime(2026, 10, 2, tzinfo=UTC),
        end=datetime(2026, 10, 3, tzinfo=UTC),
    )
    assert [e.id for e in day] == [3, 2]  # newest first, end exclusive

    assert [e.id for e in list_events(conn, zone="garden")] == [3]
    assert len(list_events(conn, limit=2)) == 2


def test_time_filter_respects_timezones(conn):
    # 01:30 in UTC+2 is 23:30 UTC the previous day
    insert_event(conn, make("2026-10-02T01:30:00+02:00"))
    assert list_events(conn, start=datetime(2026, 10, 2, tzinfo=UTC)) == []

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.schemas import Event, EventCreate

VALID = {"timestamp": "2026-10-02T21:15:00+02:00", "source": "webcam:0", "zone": "door"}


def test_minimal_event_gets_defaults():
    e = EventCreate(**VALID)
    assert e.identity == "unknown"
    assert e.dwell_seconds == 0.0
    assert e.description is None


@pytest.mark.parametrize(
    "bad",
    [
        {"timestamp": "2026-10-02T21:15:00"},  # no timezone
        {"dwell_seconds": -1},
        {"threat_level": "extreme"},
        {"source": ""},
    ],
)
def test_invalid_events_rejected(bad):
    with pytest.raises(ValidationError):
        EventCreate(**{**VALID, **bad})


def test_embedding_not_serialized():
    e = Event(**VALID, id=1, embedding=[0.1, 0.2])
    assert "embedding" not in e.model_dump()
    assert isinstance(e.timestamp, datetime)

"""Event schema: the core contract shared by vision, API, storage, RAG and bot."""

from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field

ThreatLevel = Literal["none", "low", "medium", "high"]


class EventCreate(BaseModel):
    """What a producer (event builder or synthetic generator) sends. No id yet."""

    timestamp: AwareDatetime  # timezone required so time-range queries are unambiguous
    source: str = Field(min_length=1, examples=["webcam:0", "file:clip_03.mp4", "synthetic"])
    track_id: int | None = Field(default=None, ge=0)
    zone: str | None = None
    dwell_seconds: float = Field(default=0.0, ge=0)
    identity: str = "unknown"
    snapshot_path: str | None = None
    # Filled by the vision LLM (Day 5); empty until then.
    description: str | None = None
    activity: str | None = None
    threat_level: ThreatLevel | None = None


class Event(EventCreate):
    """A stored event, as returned by the API."""

    id: int
    # Filled on Day 6. Kept out of API responses (hundreds of floats per event).
    embedding: list[float] | None = Field(default=None, exclude=True)

import pytest
from fastapi.testclient import TestClient

from src import db
from src.api.main import app, get_conn


@pytest.fixture
def client(tmp_path):
    path = str(tmp_path / "api.db")

    def test_conn():
        conn = db.connect(path)
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_conn] = test_conn
    yield TestClient(app)
    app.dependency_overrides.clear()


EVENT = {"timestamp": "2026-10-02T21:00:00+02:00", "source": "webcam:0", "zone": "door"}


def test_create_then_get(client):
    r = client.post("/events", json=EVENT)
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1
    assert body["identity"] == "unknown"
    assert "embedding" not in body
    assert client.get("/events/1").json() == body


def test_invalid_event_rejected(client):
    r = client.post("/events", json={**EVENT, "dwell_seconds": -5})
    assert r.status_code == 422


def test_missing_event_404(client):
    assert client.get("/events/42").status_code == 404


def test_list_with_filters(client):
    client.post("/events", json=EVENT)
    client.post("/events", json={**EVENT, "zone": "garden"})
    assert len(client.get("/events").json()) == 2
    garden = client.get("/events", params={"zone": "garden"}).json()
    assert [e["id"] for e in garden] == [2]
    later = client.get("/events", params={"start": "2026-10-03T00:00:00Z"}).json()
    assert later == []

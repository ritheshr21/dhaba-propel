import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

TICKETS_PATH = Path(__file__).resolve().parent.parent / "dhaba_tickets.json"
client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_triage_rejects_empty_body() -> None:
    response = client.post("/triage", json={})
    assert response.status_code == 422


def test_triage_accepts_valid_ticket_returns_not_implemented() -> None:
    ticket = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))["tickets"][0]
    response = client.post("/triage", json=ticket)
    assert response.status_code == 501
    assert response.json()["detail"] == "Triage pipeline not implemented yet."

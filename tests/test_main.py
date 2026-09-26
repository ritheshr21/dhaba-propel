import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

TICKETS_PATH = Path(__file__).resolve().parent.parent / "dhaba_tickets.json"
client = TestClient(app)

@pytest.fixture(autouse=True)
def isolate_test_database(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv(
        "TRIAGE_DB_PATH",
        str(tmp_path / "triage.sqlite3"),
    )

REQUIRED_TOP_LEVEL = {
    "category",
    "severity",
    "refund",
    "reply_draft",
    "needs_human",
    "confidence",
}


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_triage_rejects_empty_body() -> None:
    response = client.post("/triage", json={})
    assert response.status_code == 422


def test_triage_returns_triage_out_offline() -> None:
    ticket = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))["tickets"][0]
    response = client.post("/triage", json=ticket)
    assert response.status_code == 200
    body = response.json()
    assert REQUIRED_TOP_LEVEL <= set(body.keys())
    assert body["refund"]["reason_code"] == "policy_review_required"


def test_triage_same_input_same_output() -> None:
    ticket = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))["tickets"][0]
    first = client.post("/triage", json=ticket).json()
    second = client.post("/triage", json=ticket).json()
    assert first == second


def test_all_twelve_tickets_triage_offline() -> None:
    tickets = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))["tickets"]
    for ticket in tickets:
        response = client.post("/triage", json=ticket)
        assert response.status_code == 200, ticket["id"]
        assert REQUIRED_TOP_LEVEL <= set(response.json().keys())


def test_live_mode_not_implemented(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DHABA_LLM_MODE", "live")
    ticket = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))["tickets"][0]
    response = client.post("/triage", json=ticket)
    assert response.status_code == 501

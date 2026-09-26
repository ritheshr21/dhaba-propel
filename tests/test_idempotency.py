from fastapi.testclient import TestClient

from app import main
from app.schemas import (
    Category,
    ConfidenceBand,
    ConfidenceOut,
    RefundAction,
    RefundDecision,
    Severity,
    TriageOut,
)


def _response() -> TriageOut:
    return TriageOut(
        category=Category.BILLING,
        severity=Severity.HIGH,
        refund=RefundDecision(
            action=RefundAction.UNDETERMINED,
            amount_inr=None,
            reason_code="policy_review_required",
            reason_summary="Human review required.",
        ),
        reply_draft="We will review your request.",
        needs_human=True,
        confidence=ConfidenceOut(
            score=0.8,
            band=ConfidenceBand.MEDIUM,
            on_low="Review manually.",
        ),
    )


def _ticket() -> dict:
    return {
        "id": "T-idempotency-test",
        "received_at": "2026-09-02T09:14:00+05:30",
        "subject": "Refund request",
        "body": "Please check my payment.",
        "purchases": [],
        "app_opens_since_renewal": 0,
    }


def test_repeated_ticket_returns_saved_result(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv(
        "TRIAGE_DB_PATH",
        str(tmp_path / "triage.sqlite3"),
    )

    calls = 0

    def fake_run_triage(ticket):
        nonlocal calls
        calls += 1
        return _response()

    monkeypatch.setattr(main, "run_triage", fake_run_triage)
    client = TestClient(main.app)

    first = client.post("/triage", json=_ticket())
    second = client.post("/triage", json=_ticket())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert calls == 1


def test_saved_result_survives_new_client(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv(
        "TRIAGE_DB_PATH",
        str(tmp_path / "triage.sqlite3"),
    )

    calls = 0

    def fake_run_triage(ticket):
        nonlocal calls
        calls += 1
        return _response()

    monkeypatch.setattr(main, "run_triage", fake_run_triage)

    first_client = TestClient(main.app)
    first = first_client.post("/triage", json=_ticket())

    # A new client uses the same persistent database.
    second_client = TestClient(main.app)
    second = second_client.post("/triage", json=_ticket())

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert calls == 1
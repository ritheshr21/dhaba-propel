import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.schemas import TicketIn, TriageOut

TICKETS_PATH = Path(__file__).resolve().parent.parent / "dhaba_tickets.json"


def test_all_fixture_tickets_validate() -> None:
    payload = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))
    for ticket in payload["tickets"]:
        parsed = TicketIn.model_validate(ticket)
        assert parsed.id == ticket["id"]


def test_ticket_rejects_missing_id() -> None:
    with pytest.raises(ValidationError):
        TicketIn.model_validate(
            {
                "received_at": "2026-09-02T09:14:00+05:30",
                "subject": "x",
                "body": "y",
                "purchases": [],
                "app_opens_since_renewal": 0,
            }
        )


def test_triage_out_round_trip() -> None:
    sample = TriageOut.model_validate(
        {
            "category": "billing",
            "severity": "medium",
            "refund": {
                "action": "undetermined",
                "amount_inr": None,
                "reason_code": "not_implemented",
                "reason_summary": "Stage 1 placeholder.",
            },
            "reply_draft": "We are looking into your request.",
            "needs_human": True,
            "confidence": {
                "score": 0.0,
                "band": "low",
                "on_low": "Escalate to a human agent.",
            },
        }
    )
    assert sample.refund.action.value == "undetermined"

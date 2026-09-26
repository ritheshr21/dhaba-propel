from typing import Any

from app.pipeline import extract_llm_output, run_triage
from app.schemas import Category, ConfidenceBand, Severity, TicketIn


class _SequenceProvider:
    def __init__(self, payloads: list[dict[str, Any]]) -> None:
        self._payloads = payloads
        self.calls = 0

    def generate(self, ticket: TicketIn) -> dict[str, Any]:
        self.calls += 1
        index = min(self.calls - 1, len(self._payloads) - 1)
        return self._payloads[index]


def test_extract_retries_then_succeeds() -> None:
    ticket = TicketIn.model_validate(
        {
            "id": "T-test",
            "received_at": "2026-09-02T09:14:00+05:30",
            "subject": "x",
            "body": "y",
            "purchases": [],
            "app_opens_since_renewal": 0,
        }
    )
    provider = _SequenceProvider(
        [
            {"category": "not_a_real_category"},
            {
                "category": "billing",
                "severity": "low",
                "reply_draft": "ok",
                "needs_human": False,
                "confidence": {
                    "score": 0.9,
                    "band": "high",
                    "on_low": "n/a",
                },
            },
        ]
    )
    result = extract_llm_output(ticket, provider, max_retries=2)
    assert result.category is Category.BILLING
    assert provider.calls == 2


def test_extract_degrades_after_invalid_payloads() -> None:
    ticket = TicketIn.model_validate(
        {
            "id": "T-test",
            "received_at": "2026-09-02T09:14:00+05:30",
            "subject": "x",
            "body": "y",
            "purchases": [],
            "app_opens_since_renewal": 0,
        }
    )
    provider = _SequenceProvider([{"invalid": True}, {"also": "bad"}])
    result = extract_llm_output(ticket, provider, max_retries=1)
    assert result.needs_human is True
    assert result.confidence.band is ConfidenceBand.LOW
    assert result.severity is Severity.MEDIUM


def test_run_triage_uses_pending_refund_stub() -> None:
    ticket = TicketIn.model_validate(
        {
            "id": "T-1001",
            "received_at": "2026-09-02T09:14:00+05:30",
            "subject": "s",
            "body": "b",
            "purchases": [],
            "app_opens_since_renewal": 0,
        }
    )
    from app.config import DEFAULT_FIXTURES_DIR
    from app.providers.fixture import FixtureModelProvider

    out = run_triage(ticket, FixtureModelProvider(DEFAULT_FIXTURES_DIR))
    assert out.refund.reason_code == "refund_gate_pending"
    assert out.refund.action.value == "undetermined"

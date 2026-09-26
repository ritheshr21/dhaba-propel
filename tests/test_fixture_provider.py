import json
from pathlib import Path

import pytest

from app.config import DEFAULT_FIXTURES_DIR
from app.providers.fixture import FixtureModelProvider
from app.schemas import LLMExtraction, TicketIn

TICKETS_PATH = Path(__file__).resolve().parent.parent / "dhaba_tickets.json"


@pytest.fixture
def provider() -> FixtureModelProvider:
    return FixtureModelProvider(DEFAULT_FIXTURES_DIR)


def test_fixture_loads_validate_as_llm_extraction(provider: FixtureModelProvider) -> None:
    tickets = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))["tickets"]
    for row in tickets:
        ticket = TicketIn.model_validate(row)
        raw = provider.generate(ticket)
        LLMExtraction.model_validate(raw)


def test_same_ticket_id_same_raw_output(provider: FixtureModelProvider) -> None:
    ticket = TicketIn.model_validate(
        json.loads(TICKETS_PATH.read_text(encoding="utf-8"))["tickets"][0]
    )
    first = provider.generate(ticket)
    second = provider.generate(ticket)
    assert first == second

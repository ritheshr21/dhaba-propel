import json
from pathlib import Path

from app.schemas import TicketIn


class FixtureModelProvider:
    """Deterministic offline provider: one fixture file per ticket id."""

    def __init__(self, fixtures_dir: Path) -> None:
        self._fixtures_dir = fixtures_dir

    def generate(self, ticket: TicketIn) -> dict:
        path = self._fixtures_dir / f"{ticket.id}.json"
        if not path.is_file():
            raise FileNotFoundError(
                f"No LLM fixture for ticket {ticket.id!r} at {path}"
            )
        return json.loads(path.read_text(encoding="utf-8"))

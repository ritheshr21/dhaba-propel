from typing import Any, Protocol, runtime_checkable

from app.schemas import TicketIn


@runtime_checkable
class ModelProvider(Protocol):
    """Produces raw structured dicts for validation into LLMExtraction."""

    def generate(self, ticket: TicketIn) -> dict[str, Any]:
        """Return model output as a JSON-like dict (no refund fields)."""

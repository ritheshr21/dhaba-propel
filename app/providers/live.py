from app.schemas import TicketIn


class LiveModelProvider:
    """Placeholder for a future paid/local LLM adapter (Stage 2+)."""

    def generate(self, ticket: TicketIn) -> dict:
        raise NotImplementedError(
            "Live LLM provider is not implemented. Set DHABA_LLM_MODE=replay for offline fixtures."
        )

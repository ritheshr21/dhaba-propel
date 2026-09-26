from pydantic import ValidationError

from app.config import get_extraction_max_retries
from app.providers.base import ModelProvider
from app.providers.factory import get_model_provider
from app.schemas import (
    Category,
    ConfidenceBand,
    ConfidenceOut,
    LLMExtraction,
    RefundAction,
    RefundDecision,
    Severity,
    TicketIn,
    TriageOut,
)

REFUND_GATE_PENDING = RefundDecision(
    action=RefundAction.UNDETERMINED,
    amount_inr=None,
    reason_code="refund_gate_pending",
    reason_summary="Refund eligibility is decided by the policy gate (not implemented yet).",
)


def _degraded_extraction() -> LLMExtraction:
    return LLMExtraction(
        category=Category.OTHER,
        severity=Severity.MEDIUM,
        reply_draft=(
            "Thanks for contacting Dhaba support. "
            "A team member will review your message and reply shortly."
        ),
        needs_human=True,
        confidence=ConfidenceOut(
            score=0.0,
            band=ConfidenceBand.LOW,
            on_low="Model output failed validation after retries; escalated to a human.",
        ),
    )


def extract_llm_output(
    ticket: TicketIn,
    provider: ModelProvider,
    *,
    max_retries: int | None = None,
) -> LLMExtraction:
    attempts = get_extraction_max_retries() if max_retries is None else max_retries
    for _ in range(attempts + 1):
        raw = provider.generate(ticket)
        try:
            return LLMExtraction.model_validate(raw)
        except ValidationError:
            continue
    return _degraded_extraction()


def run_triage(
    ticket: TicketIn,
    provider: ModelProvider | None = None,
) -> TriageOut:
    model = provider or get_model_provider()
    extraction = extract_llm_output(ticket, model)
    return TriageOut(
        category=extraction.category,
        severity=extraction.severity,
        refund=REFUND_GATE_PENDING,
        reply_draft=extraction.reply_draft,
        needs_human=extraction.needs_human,
        confidence=extraction.confidence,
    )

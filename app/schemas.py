from datetime import datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class PurchaseStatus(str, Enum):
    INITIATED = "initiated"
    FAILED = "failed"
    SUCCESSFUL = "successful"
    RENEWAL = "renewal"


class PurchaseIn(BaseModel):
    id: str
    type: str
    amount_inr: Annotated[int, Field(ge=0)]
    status: PurchaseStatus
    at: datetime


class TicketIn(BaseModel):
    """Support ticket body as in dhaba_tickets.json."""

    id: str
    received_at: datetime
    subject: str
    body: str
    purchases: list[PurchaseIn] = Field(default_factory=list)
    app_opens_since_renewal: Annotated[int, Field(ge=0)]


class Category(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    CANCELLATION = "cancellation"
    INVOICE = "invoice"
    FEATURE_REQUEST = "feature_request"
    ABUSE_OR_FRAUD = "abuse_or_fraud"
    OTHER = "other"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceBand(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RefundAction(str, Enum):
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"
    UNDETERMINED = "undetermined"


class RefundDecision(BaseModel):
    """Deterministic refund outcome (populated by refund gate in later stages)."""

    action: RefundAction
    amount_inr: int | None = None
    reason_code: str
    reason_summary: str


class ConfidenceOut(BaseModel):
    score: Annotated[float, Field(ge=0.0, le=1.0)]
    band: ConfidenceBand
    on_low: str


class TriageOut(BaseModel):
    """JSON a support tool could act on (assignment Task 1)."""

    category: Category
    severity: Severity
    refund: RefundDecision
    reply_draft: str
    needs_human: bool
    confidence: ConfidenceOut


class LLMExtraction(BaseModel):
    """Structured model output only — no refund amounts (later stages)."""

    category: Category
    severity: Severity
    reply_draft: str
    needs_human: bool
    confidence: ConfidenceOut

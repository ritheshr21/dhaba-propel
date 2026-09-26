from app.schemas import (
    RefundAction,
    RefundDecision,
    TicketIn,
)

REFUND_KEYWORDS = (
    "refund",
    "refund it",
    "reverse",
    "reimburse",
    "money back",
    "charged me",
    "charge back",
    "double charge",
    "paisa kat",
)


def decide_refund(ticket: TicketIn) -> RefundDecision:
    """
    Conservative refund gate.

    This does not approve refunds. The actual refund policy has not
    been provided, so requests involving successful payments require
    human review.
    """
    message = f"{ticket.subject} {ticket.body}".lower()

    refund_requested = any(
        keyword in message for keyword in REFUND_KEYWORDS
    )

    if not refund_requested:
        return RefundDecision(
            action=RefundAction.NONE,
            amount_inr=None,
            reason_code="no_refund_request",
            reason_summary="No refund request was detected.",
        )

    successful_payments = [
        purchase
        for purchase in ticket.purchases
        if purchase.status.value in {"successful", "renewal"}
    ]

    if not successful_payments:
        return RefundDecision(
            action=RefundAction.NONE,
            amount_inr=None,
            reason_code="no_successful_payment",
            reason_summary=(
                "No successful payment is recorded. "
                "No refund can be approved from the available data."
            ),
        )

    return RefundDecision(
        action=RefundAction.UNDETERMINED,
        amount_inr=None,
        reason_code="policy_review_required",
        reason_summary=(
            "A refund was requested and successful payment records exist. "
            "Eligibility must be checked against the refund policy by a "
            "human reviewer."
        ),
    )
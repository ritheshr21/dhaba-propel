import re

from app.schemas import RefundAction, RefundDecision, TicketIn


REFUND_KEYWORDS = (
    "refund it",
    "refund my",
    "refund this",
    "please refund",
    "money back",
    "reverse",
    "double charge",
)


def decide_refund(ticket: TicketIn) -> RefundDecision:
    """Conservative refund gate; does not approve or issue refunds."""

    # Ignore common prompt-injection sections in the ticket text.
    message = f"{ticket.subject} {ticket.body}".lower()
    message = re.split(
        r"\n\s*---\s*\n|p\.s\.\s*for the automated agent",
        message,
        maxsplit=1,
    )[0]

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
            "A refund or duplicate-charge concern was detected. "
            "Eligibility must be checked by a human reviewer."
        ),
    )
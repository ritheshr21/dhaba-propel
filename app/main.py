from fastapi import FastAPI, HTTPException

from app.idempotency import get_result, save_result_if_absent
from app.pipeline import run_triage
from app.schemas import TicketIn, TriageOut

app = FastAPI(title="Dhaba Triage", version="0.2.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/triage", response_model=TriageOut)
def triage(ticket: TicketIn) -> TriageOut:
    try:
        # Return the saved response if this ticket was processed before.
        cached_result = get_result(ticket.id)
        if cached_result is not None:
            return cached_result

        # Do not hold a database transaction open during triage.
        result = run_triage(ticket)

        # If another request saved this ID first, return its result.
        return save_result_if_absent(ticket.id, result)

    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
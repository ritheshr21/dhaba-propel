from fastapi import FastAPI, HTTPException

from app.pipeline import run_triage
from app.schemas import TicketIn, TriageOut

app = FastAPI(title="Dhaba Triage", version="0.2.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/triage", response_model=TriageOut)
def triage(ticket: TicketIn) -> TriageOut:
    try:
        return run_triage(ticket)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

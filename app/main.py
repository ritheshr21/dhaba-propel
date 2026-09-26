from fastapi import FastAPI, HTTPException

from app.schemas import TicketIn

app = FastAPI(title="Dhaba Triage", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/triage")
def triage(_ticket: TicketIn) -> None:
    """Validate ticket shape; triage pipeline not implemented until later stages."""
    raise HTTPException(
        status_code=501,
        detail="Triage pipeline not implemented yet.",
    )

import os
import sqlite3
from pathlib import Path

from app.schemas import TriageOut


def _db_path() -> Path:
    return Path(
        os.getenv("TRIAGE_DB_PATH", "data/triage.sqlite3")
    )


def _connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path, timeout=10)
    connection.execute("PRAGMA busy_timeout = 10000")
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS triage_results (
            ticket_id TEXT PRIMARY KEY,
            response_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return connection


def get_result(ticket_id: str) -> TriageOut | None:
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT response_json
            FROM triage_results
            WHERE ticket_id = ?
            """,
            (ticket_id,),
        ).fetchone()

    if row is None:
        return None

    return TriageOut.model_validate_json(row[0])


def save_result_if_absent(
    ticket_id: str,
    result: TriageOut,
) -> TriageOut:
    response_json = result.model_dump_json()

    with _connect() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO triage_results (
                ticket_id,
                response_json
            )
            VALUES (?, ?)
            """,
            (ticket_id, response_json),
        )

        row = connection.execute(
            """
            SELECT response_json
            FROM triage_results
            WHERE ticket_id = ?
            """,
            (ticket_id,),
        ).fetchone()

    if row is None:
        raise RuntimeError("Could not retrieve stored triage result")

    return TriageOut.model_validate_json(row[0])
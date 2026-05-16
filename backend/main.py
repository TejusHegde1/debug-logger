"""
Anti-Pattern & Debug Logger — Backend API
FastAPI application with SQLite persistence.
"""

import os
import uuid
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH = os.environ.get("DB_PATH", "/data/debug_logs.db")

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Return a connection with row-factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the debug_logs table if it doesn't exist."""
    os.makedirs(os.path.dirname(DB_PATH) if os.path.dirname(DB_PATH) else ".", exist_ok=True)
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS debug_logs (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            anti_pattern TEXT NOT NULL,
            working_code TEXT NOT NULL,
            root_cause  TEXT NOT NULL,
            tags        TEXT DEFAULT '',
            created_at  TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


@asynccontextmanager
async def lifespan(application: FastAPI):
    init_db()
    yield


app = FastAPI(title="Debug Logger API", version="1.0.0", lifespan=lifespan)

# Allow all origins for local / K8s development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class LogCreate(BaseModel):
    title: str
    anti_pattern: str
    working_code: str
    root_cause: str
    tags: Optional[str] = ""

    @field_validator("root_cause")
    @classmethod
    def root_cause_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("root_cause must not be empty")
        return v


class LogResponse(BaseModel):
    id: str
    title: str
    anti_pattern: str
    working_code: str
    root_cause: str
    tags: str
    created_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health_check():
    """Kubernetes readiness / liveness probe."""
    return {"status": "ok"}


@app.post("/api/logs", response_model=LogResponse, status_code=201)
def create_log(payload: LogCreate):
    """Create a new debug log entry."""
    log_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    conn = get_db()
    conn.execute(
        """
        INSERT INTO debug_logs (id, title, anti_pattern, working_code, root_cause, tags, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (log_id, payload.title, payload.anti_pattern, payload.working_code,
         payload.root_cause, payload.tags or "", created_at),
    )
    conn.commit()
    conn.close()

    return LogResponse(
        id=log_id,
        title=payload.title,
        anti_pattern=payload.anti_pattern,
        working_code=payload.working_code,
        root_cause=payload.root_cause,
        tags=payload.tags or "",
        created_at=created_at,
    )


@app.get("/api/logs", response_model=List[LogResponse])
def list_logs(tag: Optional[str] = Query(None)):
    """Retrieve all debug logs, optionally filtered by tag."""
    conn = get_db()

    if tag:
        # Search for the tag anywhere in the comma-separated list
        rows = conn.execute(
            "SELECT * FROM debug_logs WHERE tags LIKE ? ORDER BY created_at DESC",
            (f"%{tag}%",),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM debug_logs ORDER BY created_at DESC"
        ).fetchall()

    conn.close()
    return [LogResponse(**dict(r)) for r in rows]


@app.get("/api/logs/{log_id}", response_model=LogResponse)
def get_log(log_id: str):
    """Retrieve a single debug log by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM debug_logs WHERE id = ?", (log_id,)).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Log not found")

    return LogResponse(**dict(row))

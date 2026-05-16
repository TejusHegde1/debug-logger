"""
Pytest tests for the Debug Logger API.
"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# Point DB to a temp file so tests don't touch real data
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DB_PATH"] = _tmp.name
_tmp.close()

from main import app, init_db  # noqa: E402  (import after env override)

# Ensure the table exists (lifespan may not fire in all test setups)
init_db()

client = TestClient(app)

SAMPLE_LOG = {
    "title": "Mutable Default Argument",
    "anti_pattern": "def append(item, lst=[]):\n    lst.append(item)\n    return lst",
    "working_code": "def append(item, lst=None):\n    if lst is None:\n        lst = []\n    lst.append(item)\n    return lst",
    "root_cause": "Mutable default arguments are shared across calls.",
    "tags": "python,functions",
}


def test_health():
    """GET /health should return 200."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_log():
    """POST /api/logs should return 201 with the new log."""
    resp = client.post("/api/logs", json=SAMPLE_LOG)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == SAMPLE_LOG["title"]
    assert "id" in data
    assert "created_at" in data


def test_create_log_empty_root_cause():
    """POST /api/logs with empty root_cause should fail validation."""
    bad = {**SAMPLE_LOG, "root_cause": "   "}
    resp = client.post("/api/logs", json=bad)
    assert resp.status_code == 422


def test_list_logs():
    """GET /api/logs should return a list containing the created log."""
    resp = client.get("/api/logs")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_list_logs_filter_tag():
    """GET /api/logs?tag=python should return matching logs."""
    resp = client.get("/api/logs?tag=python")
    assert resp.status_code == 200
    data = resp.json()
    assert all("python" in log["tags"] for log in data)


def test_get_log_by_id():
    """GET /api/logs/{id} should return the specific log."""
    # Create one first
    create_resp = client.post("/api/logs", json=SAMPLE_LOG)
    log_id = create_resp.json()["id"]

    resp = client.get(f"/api/logs/{log_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == log_id


def test_get_log_not_found():
    """GET /api/logs/{id} with bad id should return 404."""
    resp = client.get("/api/logs/nonexistent-id")
    assert resp.status_code == 404

"""
Unit & Integration Tests for Health and Diagnostics Endpoint
"""

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Verifies that root '/' endpoint returns valid service metadata and docs links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "project" in data
    assert "version" in data
    assert data["status"] == "operational"
    assert data["docs"] == "/docs"


def test_health_endpoint(client: TestClient):
    """Verifies that GET /api/v1/health returns healthy status and mock mode."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["mock_mode"] is True
    assert "uptime_seconds" in data
    assert data["uptime_seconds"] >= 0
    assert "timestamp" in data
    assert "system_info" in data
    assert data["system_info"]["max_upload_size_mb"] == 15.0

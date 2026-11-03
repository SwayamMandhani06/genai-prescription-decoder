"""
Unit & Integration Tests for Health and Diagnostics Endpoint
Validates:
- Root '/' endpoint metadata and docs links.
- Versioned '/api/v1/health' endpoint diagnostics.
- RAG reference index availability verification.
- Storage filesystem writability diagnostics.
- Active runtime configuration readiness.
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
    assert data["system_info"]["max_upload_size_mb"] in (10.0, 15.0)


def test_health_rag_reference_diagnostics(client: TestClient):
    """Verifies that health probe validates RAG formulary reference data availability."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    deps = data["system_info"]["dependencies"]
    assert deps["rag_formulary_status"] == "ready"
    assert deps["rag_reference_records"] > 0
    assert deps["rag_detail"] == "available"


def test_health_storage_writability_diagnostics(client: TestClient):
    """Verifies that health probe validates ephemeral storage directory writability."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    deps = data["system_info"]["dependencies"]
    assert deps["storage_service_status"] == "ready"
    assert deps["storage_writability"] == "writable"


def test_health_active_configuration_readiness(client: TestClient):
    """Verifies that health probe validates runtime configuration parameter integrity."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    deps = data["system_info"]["dependencies"]
    assert deps["active_configuration_readiness"] == "ready"
    assert "retention_ttl_seconds" in deps
    assert "zero_retention_enforced" in deps
    assert isinstance(deps["zero_retention_enforced"], bool)

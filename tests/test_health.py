"""Tests for the /health endpoint."""
import os

import pytest
from fastapi.testclient import TestClient

# Provide minimal env vars before importing the app so config validation passes
os.environ.setdefault("B2_KEY_ID", "test-key-id")
os.environ.setdefault("B2_APP_KEY", "test-app-key")
os.environ.setdefault("B2_BUCKET", "test-bucket")
os.environ.setdefault("B2_REGION", "eu-central-003")
os.environ.setdefault("GMI_API_KEY", "test-gmi-key")

from app.main import app  # noqa: E402  (import after env setup)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_body(client):
    data = client.get("/health").json()
    assert data["status"] == "healthy"
    assert data["service"] == "forgeflow-api"

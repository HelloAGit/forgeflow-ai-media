"""Tests for the /health endpoint.

The health endpoint must respond 200 without any storage or generation
credentials being set in the environment.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Ensure settings cache is cleared before/after each test."""
    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()
    yield
    cfg_mod.get_settings.cache_clear()


@pytest.fixture
def client(monkeypatch):
    """TestClient with no credentials set."""
    for key in (
        "GMI_API_KEY",
        "B2_ENDPOINT",
        "B2_REGION",
        "B2_BUCKET",
        "B2_ACCESS_KEY_ID",
        "B2_SECRET_ACCESS_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()

    # Import app AFTER clearing env to pick up the mocked env
    from app.main import app

    return TestClient(app)


def test_health_without_credentials(client):
    """GET /health must return 200 even with no credentials."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "forgeflow-api"

"""Tests for request validation in the generations endpoint."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()
    yield
    cfg_mod.get_settings.cache_clear()


@pytest.fixture
def client():
    from app.main import app

    return TestClient(app)


# ---------------------------------------------------------------------------
# Prompt validation
# ---------------------------------------------------------------------------


def test_prompt_too_short(client):
    resp = client.post(
        "/api/v1/generations/",
        json={"prompt": "ab"},  # < 3 chars
    )
    assert resp.status_code == 422


def test_prompt_too_long(client):
    resp = client.post(
        "/api/v1/generations/",
        json={"prompt": "x" * 1001},  # > 1000 chars
    )
    assert resp.status_code == 422


def test_prompt_valid_minimum(client, monkeypatch):
    """A 3-char prompt passes validation (generation itself may fail without creds)."""
    # Patch pipeline + storage so we don't need real credentials
    monkeypatch.setattr(
        "app.services.pipeline.pipeline_service.generate_media",
        lambda *a, **kw: b"fake-bytes",
    )
    monkeypatch.setattr(
        "app.services.storage.storage_service.upload_file",
        lambda *a, **kw: a[2],  # returns object_key
    )
    monkeypatch.setattr(
        "app.services.storage.storage_service.generate_presigned_url",
        lambda key, **kw: f"https://presigned.example.com/{key}",
    )

    resp = client.post(
        "/api/v1/generations/",
        json={"prompt": "abc"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["prompt"] == "abc"
    assert "presigned_url" in data
    assert "object_key" in data
    assert "id" in data


# ---------------------------------------------------------------------------
# Media-type validation
# ---------------------------------------------------------------------------


def test_invalid_media_type(client):
    resp = client.post(
        "/api/v1/generations/",
        json={"prompt": "A test prompt", "media_type": "application/pdf"},
    )
    assert resp.status_code == 422


def test_valid_media_types(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.pipeline.pipeline_service.generate_media",
        lambda *a, **kw: b"fake-bytes",
    )
    monkeypatch.setattr(
        "app.services.storage.storage_service.upload_file",
        lambda *a, **kw: a[2],
    )
    monkeypatch.setattr(
        "app.services.storage.storage_service.generate_presigned_url",
        lambda key, **kw: f"https://presigned.example.com/{key}",
    )

    for mt in ("image/png", "image/jpeg", "image/webp"):
        resp = client.post(
            "/api/v1/generations/",
            json={"prompt": "A valid prompt", "media_type": mt},
        )
        assert resp.status_code == 200, f"Expected 200 for {mt}, got {resp.status_code}"


# ---------------------------------------------------------------------------
# Model validation
# ---------------------------------------------------------------------------


def test_invalid_model(client):
    resp = client.post(
        "/api/v1/generations/",
        json={"prompt": "A test prompt", "model": "gpt-image-99"},
    )
    assert resp.status_code == 422


def test_valid_model(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.pipeline.pipeline_service.generate_media",
        lambda *a, **kw: b"fake-bytes",
    )
    monkeypatch.setattr(
        "app.services.storage.storage_service.upload_file",
        lambda *a, **kw: a[2],
    )
    monkeypatch.setattr(
        "app.services.storage.storage_service.generate_presigned_url",
        lambda key, **kw: f"https://presigned.example.com/{key}",
    )

    resp = client.post(
        "/api/v1/generations/",
        json={"prompt": "A valid prompt", "model": "seedream-5.0-lite"},
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Error handling — internal errors must not leak raw exception text
# ---------------------------------------------------------------------------


def test_generation_error_hides_exception_details(client, monkeypatch):
    """Internal exceptions must not be exposed raw to clients."""

    def _boom(*a, **kw):
        raise RuntimeError("super secret internal error details")

    monkeypatch.setattr(
        "app.services.pipeline.pipeline_service.generate_media",
        _boom,
    )

    resp = client.post(
        "/api/v1/generations/",
        json={"prompt": "A valid prompt"},
    )
    assert resp.status_code == 500
    body = resp.json()
    # The raw exception text must NOT appear in the response
    assert "super secret internal error details" not in str(body)
    # But a request_id must be present for log correlation
    assert "request_id" in body.get("detail", {})


# ---------------------------------------------------------------------------
# UUID reuse — id and object_key must share the same UUID prefix
# ---------------------------------------------------------------------------


def test_uuid_reuse_in_response(client, monkeypatch):
    monkeypatch.setattr(
        "app.services.pipeline.pipeline_service.generate_media",
        lambda *a, **kw: b"fake-bytes",
    )
    monkeypatch.setattr(
        "app.services.storage.storage_service.upload_file",
        lambda *a, **kw: a[2],
    )
    monkeypatch.setattr(
        "app.services.storage.storage_service.generate_presigned_url",
        lambda key, **kw: f"https://presigned.example.com/{key}",
    )

    resp = client.post(
        "/api/v1/generations/",
        json={"prompt": "A valid prompt"},
    )
    assert resp.status_code == 200
    data = resp.json()
    # object_key must include the same UUID as 'id'
    assert data["id"] in data["object_key"]

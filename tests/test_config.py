"""Tests for settings parsing, aliasing, and lazy validation."""

import pytest


def test_settings_load_without_credentials(monkeypatch):
    """Settings should load successfully even when credentials are absent."""
    for key in (
        "GMI_API_KEY",
        "B2_ENDPOINT",
        "B2_REGION",
        "B2_BUCKET",
        "B2_ACCESS_KEY_ID",
        "B2_SECRET_ACCESS_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    # Re-import with a clean cache to avoid interference from other tests.
    import importlib
    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()
    settings = cfg_mod.get_settings()

    assert settings.GMI_API_KEY is None
    assert settings.B2_BUCKET is None


def test_settings_read_canonical_names(monkeypatch):
    """Canonical env var names must be read correctly."""
    monkeypatch.setenv("GMI_API_KEY", "test-key-123")
    monkeypatch.setenv("B2_ACCESS_KEY_ID", "keyid-abc")
    monkeypatch.setenv("B2_SECRET_ACCESS_KEY", "secret-xyz")
    monkeypatch.setenv("B2_BUCKET", "my-bucket")
    monkeypatch.setenv("B2_REGION", "eu-central-003")
    monkeypatch.setenv("B2_ENDPOINT", "https://s3.eu-central-003.backblazeb2.com")

    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()
    settings = cfg_mod.get_settings()

    assert settings.GMI_API_KEY == "test-key-123"
    assert settings.B2_ACCESS_KEY_ID == "keyid-abc"
    assert settings.B2_SECRET_ACCESS_KEY == "secret-xyz"
    assert settings.B2_BUCKET == "my-bucket"
    assert settings.B2_REGION == "eu-central-003"
    assert settings.B2_ENDPOINT == "https://s3.eu-central-003.backblazeb2.com"


def test_require_generation_settings_raises_when_missing(monkeypatch):
    """require_generation_settings must raise when GMI_API_KEY is not set."""
    monkeypatch.delenv("GMI_API_KEY", raising=False)

    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()
    settings = cfg_mod.get_settings()
    with pytest.raises(RuntimeError, match="GMI_API_KEY"):
        settings.require_generation_settings()


def test_require_storage_settings_raises_when_missing(monkeypatch):
    """require_storage_settings must raise when B2 credentials are absent."""
    for key in ("B2_ENDPOINT", "B2_REGION", "B2_BUCKET", "B2_ACCESS_KEY_ID", "B2_SECRET_ACCESS_KEY"):
        monkeypatch.delenv(key, raising=False)

    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()
    settings = cfg_mod.get_settings()
    with pytest.raises(RuntimeError):
        settings.require_storage_settings()


def test_cors_origins_default():
    """CORS_ORIGINS should default to localhost."""
    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()
    settings = cfg_mod.get_settings()
    assert "localhost" in settings.CORS_ORIGINS


def test_cors_origins_custom(monkeypatch):
    """CORS_ORIGINS should be overridable via env var."""
    monkeypatch.setenv("CORS_ORIGINS", "https://app.example.com,https://staging.example.com")

    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()
    settings = cfg_mod.get_settings()
    parsed = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    assert parsed == ["https://app.example.com", "https://staging.example.com"]

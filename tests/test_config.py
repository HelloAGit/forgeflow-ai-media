"""Tests for Settings validation in app/config.py."""
import pytest
from pydantic import ValidationError


def _make_settings(**overrides):
    """Helper: build a Settings object from a base valid config with overrides."""
    from pydantic_settings import BaseSettings
    import re
    from pydantic import field_validator

    # Import the real class but initialise it without an .env file
    base = {
        "B2_KEY_ID": "key123",
        "B2_APP_KEY": "app456",
        "B2_BUCKET": "my-bucket",
        "B2_REGION": "eu-central-003",
        "GMI_API_KEY": "gmi-secret",
    }
    base.update(overrides)

    # Re-import Settings to avoid module-level singleton side-effects
    import importlib, sys
    # Patch env vars so Settings() reads them
    import os
    old = {}
    for k, v in base.items():
        old[k] = os.environ.get(k)
        os.environ[k] = v

    try:
        if "app.config" in sys.modules:
            del sys.modules["app.config"]
        from app.config import Settings
        return Settings()
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_valid_config():
    s = _make_settings()
    assert s.B2_REGION == "eu-central-003"
    assert s.B2_BUCKET == "my-bucket"


def test_invalid_b2_region_raises():
    with pytest.raises(Exception):
        _make_settings(B2_REGION="Europe")


def test_invalid_b2_region_no_number_raises():
    with pytest.raises(Exception):
        _make_settings(B2_REGION="eu-central")


def test_valid_us_region():
    s = _make_settings(B2_REGION="us-west-004")
    assert s.B2_REGION == "us-west-004"


def test_empty_bucket_raises():
    with pytest.raises(Exception):
        _make_settings(B2_BUCKET="")

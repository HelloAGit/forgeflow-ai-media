"""Tests for storage key generation and presigned URL behaviour."""

import unittest.mock as mock

import pytest


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()
    yield
    cfg_mod.get_settings.cache_clear()


# ---------------------------------------------------------------------------
# StorageService unit tests (boto3 boundary mocked)
# ---------------------------------------------------------------------------


@pytest.fixture
def storage_env(monkeypatch):
    """Set all required B2 env vars."""
    monkeypatch.setenv("B2_ENDPOINT", "https://s3.eu-central-003.backblazeb2.com")
    monkeypatch.setenv("B2_REGION", "eu-central-003")
    monkeypatch.setenv("B2_BUCKET", "test-bucket")
    monkeypatch.setenv("B2_ACCESS_KEY_ID", "key-id-abc")
    monkeypatch.setenv("B2_SECRET_ACCESS_KEY", "secret-xyz")

    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()


def test_upload_returns_object_key(storage_env, monkeypatch):
    """upload_file must return the object key, not a public URL."""
    mock_client = mock.MagicMock()
    monkeypatch.setattr("boto3.client", lambda *a, **kw: mock_client)

    from app.services.storage import StorageService

    svc = StorageService()
    key = svc.upload_file(b"test-bytes", "generations/abc/output.png", "image/png")

    assert key == "generations/abc/output.png"
    mock_client.put_object.assert_called_once()
    call_kwargs = mock_client.put_object.call_args[1]
    assert call_kwargs["Key"] == "generations/abc/output.png"
    assert call_kwargs["Body"] == b"test-bytes"
    assert call_kwargs["ContentType"] == "image/png"
    # Must NOT set a public ACL
    assert "ACL" not in call_kwargs


def test_upload_uses_configured_endpoint(storage_env, monkeypatch):
    """The boto3 client must be built with the endpoint from settings, not a rebuilt one."""
    captured = {}

    def _capture_client(*args, **kwargs):
        captured.update(kwargs)
        return mock.MagicMock()

    monkeypatch.setattr("boto3.client", _capture_client)

    from app.services.storage import StorageService

    svc = StorageService()
    svc.upload_file(b"x", "some/key.png", "image/png")

    assert captured["endpoint_url"] == "https://s3.eu-central-003.backblazeb2.com"
    assert captured["aws_access_key_id"] == "key-id-abc"
    assert captured["aws_secret_access_key"] == "secret-xyz"
    assert captured["region_name"] == "eu-central-003"


def test_generate_presigned_url(storage_env, monkeypatch):
    """generate_presigned_url must call generate_presigned_url on the boto3 client."""
    mock_client = mock.MagicMock()
    mock_client.generate_presigned_url.return_value = (
        "https://s3.eu-central-003.backblazeb2.com/test-bucket/generations/abc/output.png"
        "?X-Amz-Signature=sig123"
    )
    monkeypatch.setattr("boto3.client", lambda *a, **kw: mock_client)

    from app.services.storage import StorageService

    svc = StorageService()
    url = svc.generate_presigned_url("generations/abc/output.png", expiration=900)

    mock_client.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={"Bucket": "test-bucket", "Key": "generations/abc/output.png"},
        ExpiresIn=900,
    )
    assert "sig123" in url


def test_storage_requires_credentials(monkeypatch):
    """StorageService must raise RuntimeError when B2 creds are missing."""
    for key in ("B2_ENDPOINT", "B2_REGION", "B2_BUCKET", "B2_ACCESS_KEY_ID", "B2_SECRET_ACCESS_KEY"):
        monkeypatch.delenv(key, raising=False)

    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()

    from app.services.storage import StorageService

    svc = StorageService()
    with pytest.raises(RuntimeError):
        svc.upload_file(b"x", "k", "image/png")

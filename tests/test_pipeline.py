"""Tests for the pipeline generation contract (mocked SDK boundary).

All SDK calls (Pipeline, GMICloudImageProvider, httpx) are patched so these
tests run without real credentials or network access.
"""

import unittest.mock as mock

import pytest


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()
    yield
    cfg_mod.get_settings.cache_clear()


@pytest.fixture
def gen_env(monkeypatch):
    """Set GMI credentials in env."""
    monkeypatch.setenv("GMI_API_KEY", "test-gmi-key")

    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()


def _make_mock_run(asset_url: str = "https://cdn.gmicloud.ai/test.png", status: str = "succeeded"):
    """Build a minimal mock of the (run, manifest) tuple returned by Pipeline.run()."""
    mock_asset = mock.MagicMock()
    mock_asset.url = asset_url
    mock_asset.media_type = "image/png"

    mock_step = mock.MagicMock()
    mock_step.assets = [mock_asset]
    mock_step.status = status

    mock_run = mock.MagicMock()
    mock_run.steps = [mock_step]

    mock_manifest = mock.MagicMock()
    return mock_run, mock_manifest


def _patch_pipeline(monkeypatch, mock_run, mock_manifest):
    """Patch the Pipeline class in app.services.pipeline to return a controlled run."""
    mock_pipeline_instance = mock.MagicMock()
    mock_pipeline_instance.step.return_value = mock_pipeline_instance
    mock_pipeline_instance.run.return_value = (mock_run, mock_manifest)

    mock_Pipeline = mock.MagicMock(return_value=mock_pipeline_instance)
    monkeypatch.setattr("app.services.pipeline.Pipeline", mock_Pipeline)
    return mock_Pipeline, mock_pipeline_instance


def _patch_httpx(monkeypatch, content: bytes = b"fake-bytes"):
    """Patch httpx.Client in app.services.pipeline."""
    mock_response = mock.MagicMock()
    mock_response.content = content
    mock_response.raise_for_status = mock.MagicMock()
    mock_cm = mock.MagicMock()
    mock_cm.__enter__ = mock.MagicMock(return_value=mock_cm)
    mock_cm.__exit__ = mock.MagicMock(return_value=False)
    mock_cm.get.return_value = mock_response
    monkeypatch.setattr("app.services.pipeline.httpx.Client", mock.MagicMock(return_value=mock_cm))
    return mock_response


def test_generate_media_returns_bytes(gen_env, monkeypatch):
    """generate_media must return the downloaded bytes."""
    fake_image_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    mock_run, mock_manifest = _make_mock_run()
    _patch_pipeline(monkeypatch, mock_run, mock_manifest)
    _patch_httpx(monkeypatch, fake_image_bytes)

    from app.services.pipeline import GenblazePipeline

    result = GenblazePipeline().generate_media("A beautiful sunset", "seedream-5.0-lite", {})
    assert result == fake_image_bytes


def test_generate_media_passes_api_key(gen_env, monkeypatch):
    """The GMICloudImageProvider must be initialised with the GMI_API_KEY from settings."""
    mock_run, mock_manifest = _make_mock_run()
    _patch_pipeline(monkeypatch, mock_run, mock_manifest)
    _patch_httpx(monkeypatch)

    captured = {}

    def _capture(**kwargs):
        captured.update(kwargs)
        return mock.MagicMock()

    monkeypatch.setattr(
        "app.services.pipeline.GMICloudImageProvider",
        mock.MagicMock(side_effect=_capture),
    )

    from app.services.pipeline import GenblazePipeline

    GenblazePipeline().generate_media("A test prompt", "seedream-5.0-lite")
    assert captured.get("api_key") == "test-gmi-key"


def test_generate_media_raises_when_no_assets(gen_env, monkeypatch):
    """generate_media must raise RuntimeError when no assets are returned."""
    mock_run, mock_manifest = _make_mock_run()
    mock_run.steps[0].assets = []
    _patch_pipeline(monkeypatch, mock_run, mock_manifest)

    from app.services.pipeline import GenblazePipeline

    with pytest.raises(RuntimeError, match="no assets"):
        GenblazePipeline().generate_media("A test prompt", "seedream-5.0-lite")


def test_generate_media_raises_without_credentials(monkeypatch):
    """generate_media must raise RuntimeError when GMI_API_KEY is missing."""
    monkeypatch.delenv("GMI_API_KEY", raising=False)

    import app.config as cfg_mod

    cfg_mod.get_settings.cache_clear()

    from app.services.pipeline import GenblazePipeline

    with pytest.raises(RuntimeError, match="GMI_API_KEY"):
        GenblazePipeline().generate_media("A test prompt", "seedream-5.0-lite")

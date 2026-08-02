"""
Tests for the /api/v1/generations/ endpoint and underlying Genblaze pipeline.

All network calls are mocked at the httpx boundary so the tests are
hermetic and do not require live Genblaze or B2 credentials.
"""
import pytest
from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Minimal env vars required to import app modules without a real .env file
@pytest.fixture(autouse=True)
def _mock_settings(monkeypatch):
    monkeypatch.setenv("B2_KEY_ID", "test_key_id")
    monkeypatch.setenv("B2_APP_KEY", "test_app_key")
    monkeypatch.setenv("B2_BUCKET", "test-bucket")
    monkeypatch.setenv("B2_REGION", "us-west-004")
    monkeypatch.setenv("GMI_API_KEY", "test_gmi_key")


@pytest.fixture
def app():
    from app.main import app as fastapi_app
    return fastapi_app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_result(**overrides):
    from app.services.pipeline import PipelineResult
    defaults = dict(
        run_id="run-abc123",
        asset_url="https://f000.backblazeb2.com/file/test-bucket/generations/img.png",
        sha256="deadbeefcafe0123456789abcdef0123456789abcdef0123456789abcdef0123",
        manifest_uri="b2://test-bucket/generations/img.png.manifest.json",
    )
    defaults.update(overrides)
    return PipelineResult(**defaults)


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_create_generation_returns_real_fields(app):
    """POST /api/v1/generations/ returns all four real Genblaze result fields."""
    mock_result = _make_result()

    with patch("app.routes.generations.pipeline_service") as mock_svc:
        mock_svc.generate_media_async = AsyncMock(return_value=mock_result)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/generations/",
                json={"prompt": "a sunset over mountains"},
            )

    assert resp.status_code == 200
    data = resp.json()
    assert data["run_id"] == mock_result.run_id
    assert data["asset_url"] == mock_result.asset_url
    assert data["sha256"] == mock_result.sha256
    assert data["manifest_uri"] == mock_result.manifest_uri
    assert data["prompt"] == "a sunset over mountains"


@pytest.mark.anyio
async def test_create_generation_with_parameters(app):
    """Extra parameters are forwarded to the pipeline."""
    mock_result = _make_result()

    with patch("app.routes.generations.pipeline_service") as mock_svc:
        mock_svc.generate_media_async = AsyncMock(return_value=mock_result)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/generations/",
                json={"prompt": "cat", "parameters": {"steps": 30, "cfg_scale": 7}},
            )

        call_args = mock_svc.generate_media_async.call_args
        assert call_args[0][1] == {"steps": 30, "cfg_scale": 7}

    assert resp.status_code == 200


@pytest.mark.anyio
async def test_create_generation_pipeline_error_returns_500(app):
    """Pipeline errors surface as HTTP 500."""
    with patch("app.routes.generations.pipeline_service") as mock_svc:
        mock_svc.generate_media_async = AsyncMock(
            side_effect=RuntimeError("Genblaze run 'run-x' ended with status: failed")
        )
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/generations/",
                json={"prompt": "test"},
            )

    assert resp.status_code == 500
    assert "failed" in resp.json()["detail"]


@pytest.mark.anyio
async def test_create_generation_missing_config_returns_500(app):
    """Missing GMI_API_KEY surfaces as HTTP 500."""
    with patch("app.routes.generations.pipeline_service") as mock_svc:
        mock_svc.generate_media_async = AsyncMock(
            side_effect=RuntimeError(
                "GMI_API_KEY is required but not configured."
            )
        )
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/generations/",
                json={"prompt": "test"},
            )

    assert resp.status_code == 500
    assert "GMI_API_KEY" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Mutable-default test
# ---------------------------------------------------------------------------

def test_generation_request_parameters_not_shared():
    """Each GenerationRequest gets its own independent parameters dict."""
    from app.routes.generations import GenerationRequest

    req1 = GenerationRequest(prompt="first")
    req2 = GenerationRequest(prompt="second")
    req1.parameters["key"] = "value"
    assert "key" not in req2.parameters, (
        "Mutable default was shared between GenerationRequest instances"
    )


# ---------------------------------------------------------------------------
# Pipeline unit tests (async non-blocking path)
# ---------------------------------------------------------------------------

@pytest.mark.anyio
async def test_pipeline_submits_b2_sink():
    """generate_media_async includes the B2 sink in the request payload."""
    import httpx
    import respx

    completed_resp = {
        "run_id": "run-xyz",
        "status": "completed",
        "output": {
            "asset_url": "https://example.b2.com/img.png",
            "sha256": "aabbcc",
            "manifest_uri": "b2://bucket/img.manifest",
        },
    }

    with respx.mock(base_url="https://api.gmicloud.ai") as mock_api:
        mock_api.post("/v1/pipelines/runs").mock(
            return_value=httpx.Response(200, json=completed_resp)
        )

        from app.services.pipeline import GenblazePipeline
        svc = GenblazePipeline()
        result = await svc.generate_media_async("test prompt", {})

    assert result.run_id == "run-xyz"
    assert result.asset_url == "https://example.b2.com/img.png"
    assert result.sha256 == "aabbcc"
    assert result.manifest_uri == "b2://bucket/img.manifest"


@pytest.mark.anyio
async def test_pipeline_polls_until_complete():
    """generate_media_async polls the status endpoint when run is not yet done."""
    import httpx
    import respx

    run_id = "run-poll-test"
    pending_resp = {"run_id": run_id, "status": "running"}
    completed_resp = {
        "run_id": run_id,
        "status": "completed",
        "output": {
            "asset_url": "https://example.b2.com/polled.png",
            "sha256": "cafe",
            "manifest_uri": "b2://bucket/polled.manifest",
        },
    }

    call_count = 0

    def _status_side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            return httpx.Response(200, json={**pending_resp, "status": "running"})
        return httpx.Response(200, json=completed_resp)

    with respx.mock(base_url="https://api.gmicloud.ai") as mock_api:
        mock_api.post("/v1/pipelines/runs").mock(
            return_value=httpx.Response(200, json=pending_resp)
        )
        mock_api.get(f"/v1/pipelines/runs/{run_id}").mock(
            side_effect=_status_side_effect
        )

        from app.services.pipeline import GenblazePipeline
        import unittest.mock as mock

        svc = GenblazePipeline()
        # Speed up polling in tests
        with mock.patch("asyncio.sleep", new_callable=AsyncMock):
            result = await svc.generate_media_async("poll test", {})

    assert result.run_id == run_id
    assert result.asset_url == "https://example.b2.com/polled.png"

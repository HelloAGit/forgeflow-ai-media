import asyncio
import logging
import time
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    run_id: str
    asset_url: str
    sha256: str
    manifest_uri: str


class GenblazePipeline:
    """Async client for the Genblaze GMI Cloud image-generation pipeline."""

    def __init__(self) -> None:
        self._base_url = settings.GMI_BASE_URL.rstrip("/")
        self._pipeline_id = settings.GMI_PIPELINE_ID
        self._timeout = settings.GMI_TIMEOUT

    @property
    def _headers(self) -> dict:
        api_key = settings.GMI_API_KEY
        if not api_key:
            raise RuntimeError(
                "GMI_API_KEY is required but not configured. "
                "Set the GMI_API_KEY environment variable."
            )
        return {
            "Authorization": f"******",
            "Content-Type": "application/json",
        }

    def _build_payload(self, prompt: str, parameters: dict) -> dict:
        """Build the Genblaze pipeline run request payload with the B2 sink."""
        return {
            "pipeline_id": self._pipeline_id,
            "inputs": {
                "prompt": prompt,
                **parameters,
            },
            "sink": {
                "type": "b2",
                "bucket": settings.B2_BUCKET,
                "key_id": settings.B2_KEY_ID,
                "app_key": settings.B2_APP_KEY,
                "region": settings.B2_REGION,
            },
        }

    async def generate_media_async(
        self, prompt: str, parameters: dict
    ) -> PipelineResult:
        """
        Submit a Genblaze GMI Cloud pipeline run and await its completion.

        The B2 sink configuration is included in the request so Genblaze
        writes the generated asset directly to our Backblaze B2 bucket and
        returns object-level metadata (asset_url, sha256, manifest_uri).
        """
        payload = self._build_payload(prompt, parameters)
        headers = self._headers  # raises early if GMI_API_KEY is missing

        async with httpx.AsyncClient(timeout=float(self._timeout)) as client:
            response = await client.post(
                f"{self._base_url}/pipelines/runs",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        run_id: str = data["run_id"]
        logger.info("Genblaze run submitted: run_id=%s", run_id)

        status = data.get("status", "")
        if status not in ("completed", "succeeded"):
            data = await self._poll_until_complete(run_id, headers)

        output: dict = data.get("output") or data
        return PipelineResult(
            run_id=run_id,
            asset_url=output["asset_url"],
            sha256=output["sha256"],
            manifest_uri=output["manifest_uri"],
        )

    async def _poll_until_complete(self, run_id: str, headers: dict) -> dict:
        """Poll the run-status endpoint until the run is complete or times out."""
        deadline = time.monotonic() + self._timeout
        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                if time.monotonic() > deadline:
                    raise TimeoutError(
                        f"Genblaze run {run_id!r} did not complete "
                        f"within {self._timeout}s"
                    )
                await asyncio.sleep(2)
                resp = await client.get(
                    f"{self._base_url}/pipelines/runs/{run_id}",
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
                status: str = data.get("status", "")
                logger.debug("Run %s status: %s", run_id, status)
                if status in ("completed", "succeeded"):
                    return data
                if status in ("failed", "error", "cancelled"):
                    raise RuntimeError(
                        f"Genblaze run {run_id!r} ended with status: {status}"
                    )


pipeline_service = GenblazePipeline()

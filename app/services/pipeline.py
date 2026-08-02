"""Generation pipeline using the official Genblaze SDK.

Supported image models (pass one of these strings as ``model``):
- ``"seedream-5.0-lite"``   (default -- fast, general purpose)
- ``"flux-kontext-pro"``
- ``"gemini-2.5-flash-image"``

The provider/client abstraction follows the genblaze-core pattern:
  Pipeline -> GMICloudImageProvider -> CDN URL -> download bytes -> return
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from genblaze_core import Modality, Pipeline
from genblaze_gmicloud import GMICloudImageProvider

from app.config import get_settings

logger = logging.getLogger(__name__)

# Accepted image model slugs (GMICloud naming)
SUPPORTED_IMAGE_MODELS: frozenset[str] = frozenset(
    {
        "seedream-5.0-lite",
        "flux-kontext-pro",
        "gemini-2.5-flash-image",
    }
)
DEFAULT_IMAGE_MODEL = "seedream-5.0-lite"


class GenblazePipeline:
    """Thin wrapper around the Genblaze Pipeline/GMICloudImageProvider pattern.

    *Credentials are read lazily* -- instantiating this class never reads env
    vars; that happens the first time :meth:`generate_media` is called.
    """

    def generate_media(
        self,
        prompt: str,
        model: str = DEFAULT_IMAGE_MODEL,
        parameters: dict[str, Any] | None = None,
    ) -> bytes:
        """Generate an image and return its raw bytes.

        1. Validates credentials via :meth:`Settings.require_generation_settings`.
        2. Runs ``Pipeline -> GMICloudImageProvider`` with the requested model.
        3. Downloads the generated image from the provider CDN URL.
        4. Returns raw bytes to the caller (B2 upload is handled by the route).
        """
        if parameters is None:
            parameters = {}

        settings = get_settings()
        settings.require_generation_settings()

        gmi_model = model if model in SUPPORTED_IMAGE_MODELS else DEFAULT_IMAGE_MODEL
        if gmi_model != model:
            logger.warning(
                "Unsupported model %r -- falling back to %r", model, gmi_model
            )

        step_kwargs: dict[str, Any] = {
            "prompt": prompt,
            "modality": Modality.IMAGE,
        }
        if "aspect_ratio" in parameters:
            step_kwargs["aspect_ratio"] = parameters["aspect_ratio"]

        logger.info("Starting image generation: model=%s", gmi_model)
        run, _manifest = (
            Pipeline("forgeflow-image-gen")
            .step(
                GMICloudImageProvider(api_key=settings.GMI_API_KEY),
                model=gmi_model,
                **step_kwargs,
            )
            .run(timeout=120)
        )

        step = run.steps[0]
        if not step.assets:
            raise RuntimeError(
                f"Image generation completed but no assets were returned "
                f"(status={step.status!r})"
            )
        if step.status != "succeeded":
            raise RuntimeError(
                f"Image generation failed: status={step.status!r}, "
                f"error={getattr(step, 'error', None)!r}"
            )

        asset_url = step.assets[0].url
        logger.info("Downloading generated asset from CDN: %s", asset_url)

        with httpx.Client(timeout=60) as client:
            resp = client.get(asset_url)
            resp.raise_for_status()
            return resp.content


pipeline_service = GenblazePipeline()

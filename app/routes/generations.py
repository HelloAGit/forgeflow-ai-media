import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field, field_validator

from app.services.pipeline import SUPPORTED_IMAGE_MODELS, DEFAULT_IMAGE_MODEL, pipeline_service
from app.services.storage import storage_service

logger = logging.getLogger(__name__)
router = APIRouter()

_ALLOWED_MEDIA_TYPES = {"image/png", "image/jpeg", "image/webp"}
_PROMPT_MIN_LEN = 3
_PROMPT_MAX_LEN = 1000


class GenerationRequest(BaseModel):
    prompt: str
    media_type: str = "image/png"
    model: str = DEFAULT_IMAGE_MODEL
    parameters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v: str) -> str:
        v = v.strip()
        if len(v) < _PROMPT_MIN_LEN:
            raise ValueError(
                f"Prompt must be at least {_PROMPT_MIN_LEN} characters."
            )
        if len(v) > _PROMPT_MAX_LEN:
            raise ValueError(
                f"Prompt must be at most {_PROMPT_MAX_LEN} characters."
            )
        return v

    @field_validator("media_type")
    @classmethod
    def validate_media_type(cls, v: str) -> str:
        if v not in _ALLOWED_MEDIA_TYPES:
            raise ValueError(
                f"media_type must be one of: {sorted(_ALLOWED_MEDIA_TYPES)}"
            )
        return v

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        if v not in SUPPORTED_IMAGE_MODELS:
            raise ValueError(
                f"model must be one of: {sorted(SUPPORTED_IMAGE_MODELS)}"
            )
        return v


class GenerationResponse(BaseModel):
    id: str
    object_key: str
    presigned_url: str
    prompt: str


def _ext_for(media_type: str) -> str:
    return {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/webp": "webp",
    }.get(media_type, "bin")


def _run_generation(
    request_id: str,
    req: GenerationRequest,
) -> tuple[str, str]:
    """Synchronous worker: generate → upload asset → upload provenance.

    Returns ``(object_key, presigned_url)``.
    """
    ext = _ext_for(req.media_type)
    asset_key = f"generations/{request_id}/output.{ext}"
    provenance_key = f"generations/{request_id}/provenance.json"

    # 1. Generate media
    media_bytes = pipeline_service.generate_media(req.prompt, req.model, req.parameters)

    # 2. Upload asset (private)
    storage_service.upload_file(media_bytes, asset_key, req.media_type)

    # 3. Upload provenance JSON
    provenance = {
        "id": request_id,
        "model": req.model,
        "prompt_sha256": hashlib.sha256(req.prompt.encode()).hexdigest(),
        "media_type": req.media_type,
        "asset_key": asset_key,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    storage_service.upload_file(
        json.dumps(provenance).encode(),
        provenance_key,
        "application/json",
    )

    # 4. Generate presigned URL
    presigned_url = storage_service.generate_presigned_url(asset_key)

    return asset_key, presigned_url


@router.post("/", response_model=GenerationResponse)
async def create_generation(req: GenerationRequest):
    request_id = str(uuid.uuid4())
    try:
        asset_key, presigned_url = await run_in_threadpool(
            _run_generation, request_id, req
        )
        return GenerationResponse(
            id=request_id,
            object_key=asset_key,
            presigned_url=presigned_url,
            prompt=req.prompt,
        )
    except Exception:
        logger.exception("Generation failed [request_id=%s]", request_id)
        raise HTTPException(
            status_code=500,
            detail={"error": "Generation failed.", "request_id": request_id},
        )

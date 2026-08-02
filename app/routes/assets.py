import logging
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from app.services.storage import storage_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/{object_key:path}")
async def get_asset_url(object_key: str):
    """Return a short-lived presigned URL for a private B2 object."""
    request_id = str(uuid.uuid4())
    try:
        presigned_url = await run_in_threadpool(
            storage_service.generate_presigned_url, object_key
        )
        return {"object_key": object_key, "presigned_url": presigned_url}
    except Exception:
        logger.exception(
            "Presigned URL generation failed [request_id=%s, key=%s]",
            request_id,
            object_key,
        )
        raise HTTPException(
            status_code=500,
            detail={"error": "Could not generate presigned URL.", "request_id": request_id},
        )

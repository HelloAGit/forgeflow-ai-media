import logging

from fastapi import APIRouter, HTTPException

from app.services.storage import storage_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{filename:path}")
async def get_asset_url(filename: str):
    """
    Returns a secure, pre-signed URL to view an asset if your B2 bucket is private.
    """
    try:
        url = storage_service.generate_presigned_url(filename)
        return {"filename": filename, "presigned_url": url}
    except Exception:
        logger.exception("Failed to generate presigned URL for: %s", filename)
        raise HTTPException(status_code=500, detail="Could not retrieve asset URL. Please try again later.")

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.pipeline import pipeline_service

router = APIRouter()


class GenerationRequest(BaseModel):
    prompt: str
    parameters: dict = Field(default_factory=dict)


class GenerationResponse(BaseModel):
    run_id: str
    asset_url: str
    sha256: str
    manifest_uri: str
    prompt: str


@router.post("/", response_model=GenerationResponse)
async def create_generation(req: GenerationRequest) -> GenerationResponse:
    """
    Submit an image-generation job to the Genblaze GMI Cloud pipeline.

    The pipeline stores the generated asset in Backblaze B2 and returns
    real Genblaze run metadata: run_id, asset_url, sha256, manifest_uri.
    """
    try:
        result = await pipeline_service.generate_media_async(
            req.prompt, req.parameters
        )
        return GenerationResponse(
            run_id=result.run_id,
            asset_url=result.asset_url,
            sha256=result.sha256,
            manifest_uri=result.manifest_uri,
            prompt=req.prompt,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
from app.services.pipeline import pipeline_service
from app.services.storage import storage_service

router = APIRouter()

class GenerationRequest(BaseModel):
    prompt: str
    parameters: dict = {}

class GenerationResponse(BaseModel):
    id: str
    url: str
    prompt: str

@router.post("/", response_model=GenerationResponse)
async def create_generation(req: GenerationRequest):
    try:
        # 1. Run the Genblaze Pipeline
        media_bytes = pipeline_service.generate_media(req.prompt, req.parameters)
        
        # 2. Store the result in Backblaze B2
        filename = f"generations/{uuid.uuid4()}.png"
        asset_url = storage_service.upload_file(media_bytes, filename, "image/png")
        
        # 3. Return the contract to the frontend
        return GenerationResponse(
            id=str(uuid.uuid4()),
            url=asset_url,
            prompt=req.prompt
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

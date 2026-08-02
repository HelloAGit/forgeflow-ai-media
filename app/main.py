from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import generations, assets

app = FastAPI(
    title="ForgeFlow AI Media API",
    description="Backend service for generating and managing AI media pipelines.",
    version="1.0.0",
)

# CORS origins are configured via the CORS_ORIGINS environment variable
# (comma-separated list).  Default is localhost only for local development.
_settings = get_settings()
_cors_origins = [o.strip() for o in _settings.CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(generations.router, prefix="/api/v1/generations", tags=["Generations"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["Assets"])


@app.get("/health")
def health_check():
    """Liveness probe — does not require storage or generation credentials."""
    return {"status": "healthy", "service": "forgeflow-api"}

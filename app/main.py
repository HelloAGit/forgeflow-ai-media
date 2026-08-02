from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import generations, assets

app = FastAPI(
    title="ForgeFlow AI Media API",
    description="Backend service for generating and managing AI media pipelines.",
    version="1.0.0"
)

# Allow frontend to communicate with API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(generations.router, prefix="/api/v1/generations", tags=["Generations"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["Assets"])

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "forgeflow-api"}

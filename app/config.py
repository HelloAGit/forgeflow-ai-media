from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Backblaze B2 Configuration (S3-compatible API)
    B2_KEY_ID: str
    B2_APP_KEY: str
    B2_BUCKET: str
    B2_REGION: str
    
    # Genblaze / Model API Configuration
    GMI_API_KEY: str

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

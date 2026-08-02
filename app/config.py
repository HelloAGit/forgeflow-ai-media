from dotenv import load_dotenv
import os
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Backblaze B2 Configuration (S3-compatible API)
    B2_KEY_ID: str = os.getenv("B2_KEY_ID", "")
    B2_APP_KEY: str = os.getenv("B2_APP_KEY", "")
    B2_BUCKET: str = os.getenv("B2_BUCKET", "")
    B2_REGION: str = os.getenv("B2_REGION", "Europe")
    
    # GMI API Configuration
    GMI_API_KEY: str = os.getenv("GMI_API_KEY", "")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

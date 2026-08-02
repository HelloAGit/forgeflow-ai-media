from dotenv import load_dotenv
import os
from pydantic_settings import BaseSettings

load_dotenv()  # Load .env file

class Settings(BaseSettings):
    B2_KEY_ID: str = os.getenv("B2_KEY_ID", "6fda75616ee7")
    B2_APP_KEY: str = os.getenv("B2_APP_KEY", "003eda6b144b99023ef48da4564e329d2111aeb8c3")
    B2_BUCKET: str = os.getenv("B2_BUCKET", "666f7d6a4795c63196fe0e17")
    B2_REGION: str = os.getenv("B2_REGION", "Europe")
    GMI_API_KEY: str = os.getenv("GMI_API_KEY", "")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

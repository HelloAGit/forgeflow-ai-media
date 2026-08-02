from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Backblaze B2 Configuration (S3-compatible API)
    B2_KEY_ID: str
    B2_APP_KEY: str
    B2_BUCKET: str
    B2_REGION: str = "us-west-004"

    # Genblaze / GMI Cloud API Configuration
    GMI_API_KEY: str
    GMI_BASE_URL: str = "https://api.gmicloud.ai/v1"
    GMI_PIPELINE_ID: str = "image-generation"
    GMI_TIMEOUT: int = 120


settings = Settings()

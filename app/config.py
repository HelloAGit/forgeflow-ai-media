from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    All credentials are optional at import time so that the application
    can start and serve /health without storage/generation credentials
    being present.  Services that require credentials validate them at
    call time via :func:`require_generation_settings` /
    :func:`require_storage_settings`.
    """

    # Genblaze / GMI
    GMI_API_KEY: Optional[str] = None
    GMI_BASE_URL: str = "https://api.genblaze.ai"

    # Backblaze B2 (S3-compatible)
    B2_ENDPOINT: Optional[str] = None
    B2_REGION: Optional[str] = None
    # B2_BUCKET must be the bucket NAME, not the bucket ID
    B2_BUCKET: Optional[str] = None
    B2_ACCESS_KEY_ID: Optional[str] = None
    B2_SECRET_ACCESS_KEY: Optional[str] = None

    # CORS — comma-separated list of allowed origins
    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    def require_generation_settings(self) -> None:
        """Raise RuntimeError if generation credentials are missing."""
        missing = [
            name
            for name in ("GMI_API_KEY",)
            if not getattr(self, name)
        ]
        if missing:
            raise RuntimeError(
                f"Missing required environment variable(s): {', '.join(missing)}"
            )

    def require_storage_settings(self) -> None:
        """Raise RuntimeError if storage credentials are missing."""
        missing = [
            name
            for name in (
                "B2_ENDPOINT",
                "B2_REGION",
                "B2_BUCKET",
                "B2_ACCESS_KEY_ID",
                "B2_SECRET_ACCESS_KEY",
            )
            if not getattr(self, name)
        ]
        if missing:
            raise RuntimeError(
                f"Missing required environment variable(s): {', '.join(missing)}"
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()

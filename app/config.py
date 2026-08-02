import re
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Backblaze B2 Configuration (S3-compatible API)
    B2_KEY_ID: str
    B2_APP_KEY: str
    B2_BUCKET: str
    B2_REGION: str

    # Genblaze / Model API Configuration
    GMI_API_KEY: str

    @field_validator("B2_REGION")
    @classmethod
    def validate_b2_region(cls, v: str) -> str:
        # B2 S3-compatible regions follow the format <area>-<direction>-<NNN>
        # e.g. us-west-004, eu-central-003, us-east-005
        if not re.match(r"^[a-z]+-[a-z]+-\d{3}$", v):
            raise ValueError(
                f"B2_REGION '{v}' is not a valid B2 S3 region. "
                "Expected format: <region>-<NNN> (e.g. eu-central-003)."
            )
        return v

    @field_validator("B2_BUCKET")
    @classmethod
    def validate_b2_bucket(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("B2_BUCKET must be a non-empty bucket name.")
        return v

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

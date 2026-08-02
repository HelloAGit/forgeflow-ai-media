import os
from dataclasses import dataclass


def _required(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.strip()


@dataclass(frozen=True)
class Settings:
    # Genblaze / GMI
    gmi_api_key: str
    gmi_base_url: str

    # Backblaze B2 S3-compatible settings
    b2_endpoint: str
    b2_region: str
    b2_bucket: str  # bucket NAME, not bucket ID
    b2_access_key_id: str
    b2_secret_access_key: str

    @staticmethod
    def from_env() -> "Settings":
        return Settings(
            gmi_api_key=_required("GMI_API_KEY"),
            gmi_base_url=os.getenv("GMI_BASE_URL", "https://api.genblaze.ai").strip(),
            b2_endpoint=_required("B2_ENDPOINT"),
            b2_region=_required("B2_REGION"),
            b2_bucket=_required("B2_BUCKET"),
            b2_access_key_id=_required("B2_ACCESS_KEY_ID"),
            b2_secret_access_key=_required("B2_SECRET_ACCESS_KEY"),
        )


settings = Settings.from_env()

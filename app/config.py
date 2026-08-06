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
            gmi_api_key=_required("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImRhYWU5MDEwLTMzMTYtNDI5My05MDBmLTAyYjFhNDkxYjI5NiIsInNjb3BlIjoiaWVfbW9kZWwiLCJwcm9kdWN0IjoiSUUiLCJvd25lcklkIjoiOGQ1NGJmNTItNzAyYy00YmU5LTk2YTQtMThjNDVhYjE4ZWM1In0.4e5AHv9vJT3mZ4quH9FrJK7ZGboTpVM6-7hnxpNdrME"),
            gmi_base_url=os.getenv("GMI_BASE_URL", "https://api.genblaze.ai").strip(),
            b2_endpoint=_required("s3.eu-central-003.backblazeb2.com"),
            b2_region=_required("eu-central-003"),
            b2_bucket=_required("666f7d6a4795c63196fe0e17"),
            b2_access_key_id=_required("6fda75616ee7"),
            b2_secret_access_key=_required("
003d55afb5c8e3c3490c9bbb830dcf42230541198c"),
        )


settings = Settings.from_env()

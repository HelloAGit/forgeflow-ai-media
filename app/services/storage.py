import logging

import boto3
from botocore.config import Config

from app.config import get_settings

logger = logging.getLogger(__name__)


class StorageService:
    """S3-compatible storage service backed by Backblaze B2."""

    def _client(self):
        """Return a lazily-created boto3 S3 client using configured settings."""
        settings = get_settings()
        settings.require_storage_settings()
        return boto3.client(
            "s3",
            endpoint_url=settings.B2_ENDPOINT,
            region_name=settings.B2_REGION,
            aws_access_key_id=settings.B2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.B2_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4"),
        )

    def _bucket(self) -> str:
        return get_settings().B2_BUCKET  # type: ignore[return-value]

    def upload_file(
        self,
        file_bytes: bytes,
        object_key: str,
        content_type: str,
    ) -> str:
        """Upload bytes to B2 as a **private** object.

        Returns the object key (not a public URL).
        """
        client = self._client()
        client.put_object(
            Bucket=self._bucket(),
            Key=object_key,
            Body=file_bytes,
            ContentType=content_type,
        )
        logger.info("Uploaded private object: %s", object_key)
        return object_key

    def generate_presigned_url(self, object_key: str, expiration: int = 3600) -> str:
        """Generate a short-lived presigned GET URL for a private object."""
        client = self._client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._bucket(), "Key": object_key},
            ExpiresIn=expiration,
        )


storage_service = StorageService()

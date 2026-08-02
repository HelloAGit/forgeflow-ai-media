import boto3
from botocore.config import Config
from app.config import settings

class StorageService:
    def __init__(self):
        # Backblaze B2 is S3-compatible, so we use boto3
        endpoint_url = f"https://s3.{settings.B2_REGION}.backblazeb2.com"
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.B2_KEY_ID,
            aws_secret_access_key=settings.B2_APP_KEY,
            config=Config(signature_version='s3v4')
        )
        self.bucket = settings.B2_BUCKET

    def upload_file(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        """Uploads a file to B2 and returns the public URL (if bucket is public)."""
        self.s3_client.put_object(
            Bucket=self.bucket,
            Key=filename,
            Body=file_bytes,
            ContentType=content_type
        )
        return f"https://f000.backblazeb2.com/file/{self.bucket}/{filename}"
        
    def generate_presigned_url(self, filename: str, expiration: int = 3600) -> str:
        """Generates a pre-signed URL for secure, temporary access to private assets."""
        return self.s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': filename},
            ExpiresIn=expiration
        )

storage_service = StorageService()

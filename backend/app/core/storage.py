"""
backend/app/core/storage.py
───────────────────────────
Abstract Storage Provider Adapter pattern supporting Local and S3/MinIO compatible object stores.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageProvider(ABC):
    """Abstract interface defining required storage operations."""

    @abstractmethod
    def save(self, content: bytes, filename: str) -> str:
        """Save raw bytes to storage and return the public URL or relative path."""
        pass

    @abstractmethod
    def delete(self, filename: str) -> bool:
        """Delete file from storage."""
        pass


class LocalStorageProvider(StorageProvider):
    """Saves uploads to local container directories (fallback for development)."""

    def __init__(self) -> None:
        self.upload_dir = (
            Path(__file__).resolve().parent.parent.parent.parent / "static" / "uploads"
        )
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, filename: str) -> str:
        file_path = self.upload_dir / filename
        with open(file_path, "wb") as f:
            f.write(content)
        return f"/static/uploads/{filename}"

    def delete(self, filename: str) -> bool:
        file_path = self.upload_dir / filename
        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except Exception as exc:
                logger.error(f"Failed to delete local file '{filename}': {exc}")
        return False


class S3StorageProvider(StorageProvider):
    """Saves uploads to MinIO / AWS S3 buckets (production standard)."""

    def __init__(self) -> None:
        # Load configs from Settings / Secrets Manager
        self.bucket = "nika-uploads"
        self.endpoint_url = "http://minio:9000"
        self.access_key = "minio_access_key"
        self.secret_key = "minio_secret_key"

        # Initialize boto3 dynamically to avoid boot errors if boto3 is missing
        self._s3 = None
        try:
            import boto3

            self._s3 = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_key_id=self.secret_key,
            )
            # Assert bucket exists
            self._s3.create_bucket(Bucket=self.bucket)
        except Exception as exc:
            logger.warning(
                f"Failed to initialize S3 boto3 provider: {exc}. Falling back to Local."
            )

    def save(self, content: bytes, filename: str) -> str:
        if not self._s3:
            # Fallback to local
            return LocalStorageProvider().save(content, filename)
        try:
            self._s3.put_object(
                Bucket=self.bucket, Key=filename, Body=content, ContentType="image/jpeg"
            )
            return f"{self.endpoint_url}/{self.bucket}/{filename}"
        except Exception as exc:
            logger.error(f"S3 save failure: {exc}. Falling back to local.")
            return LocalStorageProvider().save(content, filename)

    def delete(self, filename: str) -> bool:
        if not self._s3:
            return LocalStorageProvider().delete(filename)
        try:
            self._s3.delete_object(Bucket=self.bucket, Key=filename)
            return True
        except Exception as exc:
            logger.error(f"S3 delete failure for '{filename}': {exc}")
            return False


# Initialize the active storage provider
# Use S3 provider if ENVIRONMENT is production, otherwise fallback to Local
if settings.env.value == "production":
    storage_provider: StorageProvider = S3StorageProvider()
else:
    storage_provider = LocalStorageProvider()

"""Storage provider adapter with local and S3-compatible implementations."""

from abc import ABC, abstractmethod
from contextlib import suppress
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageProvider(ABC):
    """Abstract interface defining required storage operations."""

    @abstractmethod
    def save(self, content: bytes, filename: str) -> str:
        """Save raw bytes to storage and return the public URL or relative path."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, filename: str) -> bool:
        """Delete file from storage."""
        raise NotImplementedError


class LocalStorageProvider(StorageProvider):
    """Saves uploads to local container directories (fallback for development)."""

    def __init__(self) -> None:
        self.upload_dir = (
            Path(__file__).resolve().parent.parent.parent.parent / "static" / "uploads"
        )
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save(self, content: bytes, filename: str) -> str:
        file_path = self.upload_dir / filename
        with open(file_path, "wb") as file_handle:
            file_handle.write(content)
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
    """Saves uploads to S3-compatible buckets when configured."""

    def __init__(self) -> None:
        self.bucket = settings.s3_bucket
        self.endpoint_url = settings.s3_endpoint_url.rstrip("/")
        self.access_key = settings.s3_access_key_id
        self.secret_key = settings.s3_secret_access_key
        self.region = settings.s3_region
        self.use_ssl = settings.s3_use_ssl
        self._s3 = None

        try:
            import boto3

            if not self.access_key or not self.secret_key:
                raise ValueError("S3 credentials are not configured.")

            self._s3 = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                use_ssl=self.use_ssl,
            )
            with suppress(Exception):
                self._s3.head_bucket(Bucket=self.bucket)
        except Exception as exc:
            logger.warning(
                f"Failed to initialize S3 provider: {exc}. Falling back to local storage."
            )

    def save(self, content: bytes, filename: str) -> str:
        if not self._s3:
            return LocalStorageProvider().save(content, filename)
        try:
            self._s3.put_object(
                Bucket=self.bucket,
                Key=filename,
                Body=content,
                ContentType="image/jpeg",
            )
            return f"{self.endpoint_url}/{self.bucket}/{filename}"
        except Exception as exc:
            logger.error(f"S3 save failure: {exc}. Falling back to local storage.")
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


def _build_storage_provider() -> StorageProvider:
    backend = settings.storage_backend.lower().strip()
    if backend == "s3":
        return S3StorageProvider()
    return LocalStorageProvider()


storage_provider: StorageProvider = _build_storage_provider()

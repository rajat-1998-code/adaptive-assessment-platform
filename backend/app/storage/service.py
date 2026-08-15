"""S3-compatible storage service used by document uploads."""

from __future__ import annotations

from typing import Any, BinaryIO

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings


class StorageError(Exception):
    """Raised when an object-storage operation fails."""


class StorageService:
    """Small application boundary around the boto3 S3 client."""

    def __init__(self) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY.get_secret_value(),
            region_name=settings.S3_REGION,
        )

    @property
    def client(self) -> Any:
        """Expose the client for focused tests without leaking it to routes."""

        return self._client

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        *,
        storage_key: str,
        content_type: str,
        file_size: int,
    ) -> None:
        """Upload a private object to the configured bucket."""

        try:
            self._client.put_object(
                Bucket=settings.S3_BUCKET,
                Key=storage_key,
                Body=fileobj,
                ContentLength=file_size,
                ContentType=content_type,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError("Object upload failed") from exc

    def delete_object(self, storage_key: str) -> None:
        """Delete an object, translating provider errors to StorageError."""

        try:
            self._client.delete_object(Bucket=settings.S3_BUCKET, Key=storage_key)
        except (BotoCoreError, ClientError) as exc:
            raise StorageError("Object deletion failed") from exc

    def create_download_url(self, storage_key: str) -> str:
        """Create a short-lived presigned download URL."""

        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.S3_BUCKET, "Key": storage_key},
                ExpiresIn=settings.S3_PRESIGNED_URL_EXPIRE_SECONDS,
            )
        except (BotoCoreError, ClientError) as exc:
            raise StorageError("Download URL creation failed") from exc


def get_storage_service() -> StorageService:
    """FastAPI dependency factory for the storage service."""

    return StorageService()

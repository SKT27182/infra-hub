"""
MinIO S3-compatible object storage service implementation.
"""

from typing import Any

from minio import Minio
from minio.error import S3Error

from app.core.config import settings
from app.services.base import BaseService, ServiceHealth


class MinIOService(BaseService):
    """MinIO object storage service."""

    name = "minio"
    display_name = "MinIO"
    container_name = "infra-minio"
    admin_url = "http://localhost:9001"
    admin_container = None  # MinIO has built-in console

    def _get_client(self) -> Minio:
        """Get MinIO client."""
        return Minio(
            settings.minio_endpoint,
            access_key=settings.minio_user,
            secret_key=settings.minio_password,
            secure=False,  # Use HTTP for local development
        )

    async def check_health(self) -> ServiceHealth:
        """Check MinIO connectivity."""
        try:
            client = self._get_client()
            # List buckets to verify connection
            buckets = client.list_buckets()
            return ServiceHealth(
                healthy=True,
                message="MinIO is responding",
                details={"buckets_count": len(buckets)},
            )
        except Exception as e:
            return ServiceHealth(
                healthy=False,
                message=f"MinIO connection failed: {e}",
            )

    async def get_info(self) -> dict[str, Any]:
        """Get MinIO server information."""
        try:
            client = self._get_client()

            # Get buckets
            buckets = client.list_buckets()
            bucket_details = []

            for bucket in buckets:
                # Count objects in bucket
                object_count = 0
                total_size = 0
                try:
                    for obj in client.list_objects(bucket.name, recursive=True):
                        object_count += 1
                        total_size += obj.size or 0
                except S3Error:
                    pass

                bucket_details.append(
                    {
                        "name": bucket.name,
                        "created": (
                            bucket.creation_date.isoformat()
                            if bucket.creation_date
                            else None
                        ),
                        "objects": object_count,
                        "size": total_size,
                    }
                )

            return {
                "buckets": bucket_details,
                "total_buckets": len(buckets),
            }
        except Exception as e:
            return {"error": str(e)}

    async def list_buckets(self) -> list[dict[str, Any]]:
        """List all buckets with details."""
        try:
            client = self._get_client()
            buckets = []

            for bucket in client.list_buckets():
                # Count objects and size
                object_count = 0
                total_size = 0
                try:
                    for obj in client.list_objects(bucket.name, recursive=True):
                        object_count += 1
                        total_size += obj.size or 0
                except S3Error:
                    pass

                buckets.append(
                    {
                        "name": bucket.name,
                        "created": (
                            bucket.creation_date.isoformat()
                            if bucket.creation_date
                            else None
                        ),
                        "objects": object_count,
                        "size": total_size,
                    }
                )

            return buckets
        except Exception as e:
            return [{"error": str(e)}]

    async def get_bucket_info(self, bucket_name: str) -> dict[str, Any]:
        """Get detailed bucket information."""
        try:
            client = self._get_client()

            # Check if bucket exists
            if not client.bucket_exists(bucket_name):
                return {"error": f"Bucket '{bucket_name}' not found"}

            # Get objects
            objects = []
            total_size = 0
            for obj in client.list_objects(bucket_name, recursive=True):
                objects.append(
                    {
                        "name": obj.object_name,
                        "size": obj.size,
                        "last_modified": (
                            obj.last_modified.isoformat() if obj.last_modified else None
                        ),
                        "etag": obj.etag,
                    }
                )
                total_size += obj.size or 0

            return {
                "name": bucket_name,
                "objects": objects[:100],  # Limit to first 100 objects
                "total_objects": len(objects),
                "total_size": total_size,
            }
        except Exception as e:
            return {"error": str(e)}

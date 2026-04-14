"""
MinIO S3-compatible object storage service implementation.
"""

from typing import Any

from minio import Minio
from minio.error import S3Error

from config import settings
from .base import BaseService


class MinIOService(BaseService):
    """MinIO object storage service."""

    name = settings.minio_service_name
    display_name = settings.minio_display_name
    container_name = settings.minio_container_name
    admin_url = settings.minio_admin_url

    def _get_client(self) -> Minio:
        return Minio(
            settings.minio_endpoint,
            access_key=settings.minio_user,
            secret_key=settings.minio_password,
            secure=False,
        )

    async def get_info(self) -> dict[str, Any]:
        """Get minimal but complete MinIO information."""
        try:
            client = self._get_client()
            buckets = client.list_buckets()
            details = []
            for b in buckets:
                try:
                    objs = list(client.list_objects(b.name, recursive=True))
                    details.append(
                        {
                            "name": b.name,
                            "objects": len(objs),
                            "size": sum(o.size for o in objs),
                        }
                    )
                except:
                    details.append({"name": b.name, "error": "Could not list objects"})

            return {
                "status": self.get_status().model_dump(),
                "connection": {
                    "url": f"http://{settings.service_public_host}:{settings.minio_port}",
                    "access_key": settings.minio_user,
                    "secret_key": settings.minio_password,
                },
                "buckets": details,
            }
        except Exception as e:
            return {"error": str(e), "status": self.get_status().model_dump()}

    async def create_bucket(self, name: str) -> bool:
        """Create a new bucket."""
        try:
            client = self._get_client()
            client.make_bucket(name)
            return True
        except Exception:
            return False

    async def drop_bucket(self, name: str) -> bool:
        """Drop an existing bucket."""
        try:
            client = self._get_client()
            client.remove_bucket(name)
            return True
        except Exception:
            return False

    async def query(
        self, action: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute MinIO query actions."""
        payload = params or {}

        try:
            client = self._get_client()

            if action == "list_buckets":
                buckets = client.list_buckets()
                return {
                    "success": True,
                    "result": [
                        {
                            "name": b.name,
                            "creation_date": (
                                b.creation_date.isoformat() if b.creation_date else None
                            ),
                        }
                        for b in buckets
                    ],
                }

            bucket = str(payload.get("bucket") or "").strip()
            if not bucket:
                return {"success": False, "error": "bucket is required"}

            if action == "list_objects":
                prefix = str(payload.get("prefix") or "")
                recursive = bool(payload.get("recursive", True))
                limit = int(payload.get("limit", 100))
                objects = client.list_objects(
                    bucket, prefix=prefix, recursive=recursive
                )
                result = []
                for i, obj in enumerate(objects):
                    if i >= limit:
                        break
                    result.append(
                        {
                            "name": obj.object_name,
                            "size": obj.size,
                            "last_modified": (
                                obj.last_modified.isoformat()
                                if obj.last_modified
                                else None
                            ),
                            "etag": obj.etag,
                        }
                    )
                return {"success": True, "count": len(result), "result": result}

            if action == "stat_object":
                object_name = str(payload.get("object_name") or "").strip()
                if not object_name:
                    return {"success": False, "error": "object_name is required"}
                stat = client.stat_object(bucket, object_name)
                return {
                    "success": True,
                    "result": {
                        "name": object_name,
                        "size": stat.size,
                        "etag": stat.etag,
                        "content_type": stat.content_type,
                        "last_modified": (
                            stat.last_modified.isoformat()
                            if stat.last_modified
                            else None
                        ),
                    },
                }

            return {"success": False, "error": f"Unsupported action: {action}"}
        except S3Error as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": str(e)}

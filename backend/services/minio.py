"""
MinIO S3-compatible object storage service implementation.
"""

import asyncio
from typing import Any

from minio import Minio
from minio.error import S3Error

from config import settings
from utils.logger import create_logger

from .admin_access import admin_access_block
from .base import BaseService

logger = create_logger(__name__, level=settings.log_level)


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
            buckets = await asyncio.to_thread(client.list_buckets)
            details = [{"name": bucket.name} for bucket in buckets[:500]]

            return {
                "status": self.get_status().model_dump(),
                "admin_access": admin_access_block(
                    url=settings.minio_admin_url,
                    instructions=[
                        "Open the MinIO Console in your browser.",
                        "Sign in with MINIO_USER and MINIO_PASSWORD from backend/.env.",
                    ],
                    login={
                        "username": settings.minio_user,
                        "password_env": "MINIO_PASSWORD",
                    },
                ),
                "connection": {
                    "url": f"http://{settings.service_public_host}:{settings.minio_port}",
                    "access_key": settings.minio_user,
                    "secret_key_env": "MINIO_PASSWORD",
                },
                "buckets": details,
                "buckets_truncated": len(buckets) > 500,
            }
        except Exception as e:
            logger.warning("MinIO get_info failed (%s)", type(e).__name__)
            return {"error": "MinIO information is unavailable", "status": self.get_status().model_dump()}

    async def create_bucket(self, name: str) -> bool:
        """Create a new bucket."""
        try:
            client = self._get_client()
            await asyncio.to_thread(client.make_bucket, name)
            return True
        except Exception:
            return False

    async def drop_bucket(self, name: str) -> bool:
        """Drop an existing bucket."""
        try:
            client = self._get_client()
            await asyncio.to_thread(client.remove_bucket, name)
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
                buckets = await asyncio.to_thread(client.list_buckets)
                return {
                    "success": True,
                    "result": [
                        {
                            "name": b.name,
                            "creation_date": (
                                b.creation_date.isoformat() if b.creation_date else None
                            ),
                        }
                        for b in buckets[:500]
                    ],
                    "truncated": len(buckets) > 500,
                }

            bucket = str(payload.get("bucket") or "").strip()
            if not bucket:
                return {"success": False, "error": "bucket is required"}

            if action == "list_objects":
                prefix = str(payload.get("prefix") or "")
                start_after = str(payload.get("cursor") or "")
                recursive = bool(payload.get("recursive", True))
                limit = max(1, min(int(payload.get("limit", 100)), 500))
                def collect_objects() -> list[dict[str, Any]]:
                    result: list[dict[str, Any]] = []
                    objects = client.list_objects(
                        bucket,
                        prefix=prefix,
                        recursive=recursive,
                        start_after=start_after or None,
                    )
                    for index, obj in enumerate(objects):
                        if index > limit:
                            break
                        result.append(
                            {
                                "name": obj.object_name,
                                "size": obj.size,
                                "last_modified": obj.last_modified.isoformat()
                                if obj.last_modified
                                else None,
                                "etag": obj.etag,
                            }
                        )
                    return result

                result = await asyncio.to_thread(collect_objects)
                return {
                    "success": True,
                    "count": min(len(result), limit),
                    "result": result[:limit],
                    "page_size": limit,
                    "truncated": len(result) > limit,
                    "next_cursor": result[limit - 1]["name"]
                    if len(result) > limit
                    else None,
                }

            if action == "stat_object":
                object_name = str(payload.get("object_name") or "").strip()
                if not object_name:
                    return {"success": False, "error": "object_name is required"}
                stat = await asyncio.to_thread(client.stat_object, bucket, object_name)
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
            logger.error("MinIO S3 error action=%s type=%s", action, type(e).__name__)
            return {"success": False, "error": "MinIO request failed"}
        except Exception as e:
            logger.error("MinIO query failed action=%s type=%s", action, type(e).__name__)
            return {"success": False, "error": "MinIO request failed"}

from __future__ import annotations

import os

import oss2


class OSSService:
    """Small wrapper around OSS file upload and signed download URLs."""

    def __init__(self) -> None:
        self._bucket = None

    def _get_bucket(self):
        """Lazily initialize and cache the OSS bucket client."""
        if self._bucket is None:
            access_key_id = os.getenv("OSS_ACCESS_KEY_ID", "").strip()
            access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET", "").strip()
            bucket_name = os.getenv("OSS_BUCKET_NAME", "").strip()
            endpoint = os.getenv("OSS_ENDPOINT", "").strip()
            if not all([access_key_id, access_key_secret, bucket_name, endpoint]):
                raise ValueError("Missing OSS configuration in .env")
            auth = oss2.Auth(access_key_id, access_key_secret)
            self._bucket = oss2.Bucket(auth, f"https://{endpoint}", bucket_name)
        return self._bucket

    def upload_file(self, local_path: str, object_key: str) -> str:
        """Upload one local file to OSS."""
        self._get_bucket().put_object_from_file(object_key, local_path)
        return object_key

    def signed_get_url(self, object_key: str, expires_seconds: int = 3600) -> str:
        """Generate a temporary download URL for one OSS object."""
        return self._get_bucket().sign_url("GET", object_key, expires_seconds)


oss_service = OSSService()

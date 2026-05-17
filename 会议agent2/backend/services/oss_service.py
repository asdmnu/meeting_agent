from __future__ import annotations

import os

import oss2


class OSSService:
    def __init__(self) -> None:
        self._bucket = None

    def _get_bucket(self):
        if self._bucket is None:
            access_key_id = os.getenv("OSS_ACCESS_KEY_ID", "")
            access_key_secret = os.getenv("OSS_ACCESS_KEY_SECRET", "")
            bucket_name = os.getenv("OSS_BUCKET_NAME", "")
            endpoint = os.getenv("OSS_ENDPOINT", "")
            if not all([access_key_id, access_key_secret, bucket_name, endpoint]):
                raise ValueError("Missing OSS configuration in environment variables")
            auth = oss2.Auth(access_key_id, access_key_secret)
            self._bucket = oss2.Bucket(auth, f"https://{endpoint}", bucket_name)
        return self._bucket

    def upload_file(self, local_path: str, object_key: str) -> str:
        self._get_bucket().put_object_from_file(object_key, local_path)
        return object_key

    def signed_get_url(self, object_key: str, expires_seconds: int = 3600) -> str:
        return self._get_bucket().sign_url("GET", object_key, expires_seconds)


oss_service = OSSService()

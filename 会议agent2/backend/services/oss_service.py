from __future__ import annotations

import os

import oss2


class OSSService:
    """对 OSS 文件上传和签名下载链接的轻量封装。"""

    def __init__(self) -> None:
        self._bucket = None

    def _get_bucket(self):
        """延迟初始化并缓存 OSS Bucket 客户端。"""
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
        """上传单个本地文件到 OSS。"""
        self._get_bucket().put_object_from_file(object_key, local_path)
        return object_key

    def signed_get_url(self, object_key: str, expires_seconds: int = 3600) -> str:
        """为单个 OSS 对象生成临时下载链接。"""
        return self._get_bucket().sign_url("GET", object_key, expires_seconds)


oss_service = OSSService()

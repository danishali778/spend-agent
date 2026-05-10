from __future__ import annotations

from urllib import parse, request

from app.core.config import settings


class SupabaseStorageClient:
    def __init__(self, base_url: str | None = None, service_role_key: str | None = None) -> None:
        self.base_url = (base_url or settings.supabase_url).rstrip("/")
        self.service_role_key = service_role_key or settings.supabase_service_role_key

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
        }
        if extra:
            headers.update(extra)
        return headers

    def upload_bytes(self, bucket: str, object_path: str, payload: bytes, content_type: str) -> None:
        encoded_path = "/".join(parse.quote(part) for part in object_path.split("/"))
        req = request.Request(
            f"{self.base_url}/storage/v1/object/{bucket}/{encoded_path}",
            data=payload,
            method="POST",
            headers=self._headers({"Content-Type": content_type, "x-upsert": "true"}),
        )
        with request.urlopen(req):
            return None

    def download_bytes(self, bucket: str, object_path: str) -> bytes:
        encoded_path = "/".join(parse.quote(part) for part in object_path.split("/"))
        req = request.Request(
            f"{self.base_url}/storage/v1/object/authenticated/{bucket}/{encoded_path}",
            method="GET",
            headers=self._headers(),
        )
        with request.urlopen(req) as response:
            return response.read()

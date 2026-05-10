from __future__ import annotations

import json
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from .config import settings
from .redis import get_redis_client


class CacheClient:
    def __init__(self, client: Redis | None = None) -> None:
        self.client = client or get_redis_client()

    def get_json(self, key: str) -> Any | None:
        if not settings.cache_enabled:
            return None
        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except (RedisError, TypeError, ValueError):
            return None

    def set_json(self, key: str, value: Any, ttl_seconds: int) -> None:
        if not settings.cache_enabled:
            return
        try:
            self.client.setex(key, ttl_seconds, json.dumps(value))
        except (RedisError, TypeError, ValueError):
            return

    def delete_many(self, *keys: str) -> None:
        filtered = [key for key in keys if key]
        if not filtered:
            return
        try:
            self.client.delete(*filtered)
        except RedisError:
            return

    def acquire_lock(self, key: str, ttl_seconds: int = 300) -> bool:
        try:
            return bool(self.client.set(key, "1", nx=True, ex=ttl_seconds))
        except RedisError:
            return True

    def release_lock(self, key: str) -> None:
        try:
            self.client.delete(key)
        except RedisError:
            return

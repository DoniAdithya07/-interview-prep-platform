import hashlib
import json
import time
from typing import Any

from backend.app.core.config import settings

try:
    import redis
except ImportError:
    redis = None


_memory_cache: dict[str, tuple[float, Any]] = {}
_redis_client = None


def _get_redis_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not settings.redis_url or redis is None:
        return None
    try:
        _redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        _redis_client.ping()
        return _redis_client
    except Exception:
        _redis_client = None
        return None


def build_cache_key(*parts: Any) -> str:
    raw = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def get_cached_value(key: str) -> Any | None:
    client = _get_redis_client()
    if client is not None:
        try:
            value = client.get(key)
            if value is not None:
                return json.loads(value)
        except Exception:
            pass

    entry = _memory_cache.get(key)
    if not entry:
        return None
    expires_at, value = entry
    if expires_at < time.time():
        _memory_cache.pop(key, None)
        return None
    return value


def set_cached_value(key: str, value: Any, ttl_seconds: int = 3600) -> None:
    client = _get_redis_client()
    if client is not None:
        try:
            client.setex(key, ttl_seconds, json.dumps(value, default=str))
            return
        except Exception:
            pass

    _memory_cache[key] = (time.time() + ttl_seconds, value)

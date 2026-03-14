import time

from fastapi import HTTPException, status

from backend.app.core.config import settings
from backend.app.services.cache_service import get_cached_value, set_cached_value


def enforce_daily_rate_limit(user_id: str, scope: str) -> None:
    window = settings.rate_limit_window_seconds
    limit = settings.rate_limit_requests
    now = int(time.time())
    bucket = now // max(window, 1)
    key = f"rate-limit:{scope}:{user_id}:{bucket}"
    current = int(get_cached_value(key) or 0)
    if current >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit reached for {scope}. Try again later.",
        )
    set_cached_value(key, current + 1, ttl_seconds=window)

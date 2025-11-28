"""Async Redis client helper used for token revocation and rate-limiting."""
import redis.asyncio as aioredis
from typing import Optional
from app.core.settings import settings


_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """Return an initialized aioredis Redis client (create if needed)."""
    global _redis
    if _redis is None:
        url = f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        if settings.redis_password:
            url = f"redis://:{settings.redis_password}@{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"
        _redis = aioredis.from_url(url, decode_responses=True)
        # try a ping to ensure connection pool initialized
        try:
            await _redis.ping()
        except Exception:
            # ignore here; connection will be reattempted on use
            pass
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.close()
        _redis = None

"""Redis cache configuration and utilities."""

import asyncio
import json
from typing import Any, Callable, Optional

from redis import asyncio as redis_asyncio

from app.core.settings import REDIS_CONFIG


class RedisCache:
    """Redis cache manager for alert-related data."""

    def __init__(
        self,
        *,
        url: Optional[str] = None,
        prefix: Optional[str] = None,
        redis_client: Optional[redis_asyncio.Redis] = None,
    ) -> None:
        self._prefix = prefix or REDIS_CONFIG["PREFIX"]
        if redis_client is not None:
            self.redis = redis_client
        else:
            redis_url = url or self._build_url()
            self.redis = redis_asyncio.from_url(
                redis_url,
                encoding="utf-8",
                decode_responses=True,
            )

    @staticmethod
    def _build_url() -> str:
        password = REDIS_CONFIG.get("PASSWORD")
        auth = f":{password}@" if password else ""
        return f"redis://{auth}{REDIS_CONFIG['HOST']}:{REDIS_CONFIG['PORT']}/{REDIS_CONFIG['DB']}"

    def get_key(self, *parts: str) -> str:
        """Generate a namespaced cache key."""
        sanitized = [str(part) for part in parts if part is not None]
        return ":".join([self._prefix, *sanitized])

    async def get(self, key: str) -> Optional[Any]:
        """Return a value from cache (decoded from JSON)."""
        value = await self.redis.get(key)
        return json.loads(value) if value is not None else None

    async def set(self, key: str, value: Any, *, expire: Optional[int] = None) -> None:
        """Store a value (encoded as JSON) with optional expiration."""
        ttl = expire if expire is not None else REDIS_CONFIG["DEFAULT_TIMEOUT"]
        await self.redis.set(key, json.dumps(value), ex=ttl)

    async def delete(self, key: str) -> None:
        """Remove a single cache entry."""
        await self.redis.delete(key)

    async def invalidate_pattern(self, pattern: str) -> None:
        """Remove keys matching the provided glob pattern."""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

    async def clear_all(self) -> None:
        """Clear the entire Redis database used by the cache."""
        await self.redis.flushdb()

    async def get_or_set(
        self,
        key: str,
        getter_func: Callable[[], Any],
        *,
        expire: Optional[int] = None,
    ) -> Any:
        """Read-through cache helper."""
        value = await self.get(key)
        if value is not None:
            return value

        maybe_coroutine = getter_func()
        if asyncio.iscoroutine(maybe_coroutine):
            value = await maybe_coroutine
        else:
            value = maybe_coroutine

        await self.set(key, value, expire=expire)
        return value

    async def close(self) -> None:
        """Close the underlying Redis connection pool."""
        await self.redis.close()


# Create global cache instance for application use
cache = RedisCache()
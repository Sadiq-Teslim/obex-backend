"""Cache helper tests using the in-memory stub."""

from datetime import datetime

import pytest

from tests.conftest import InMemoryAsyncCache


@pytest.fixture
def cache_instance() -> InMemoryAsyncCache:
    return InMemoryAsyncCache(prefix="test")


@pytest.mark.asyncio
async def test_basic_set_get_and_delete(cache_instance: InMemoryAsyncCache) -> None:
    key = cache_instance.get_key("basic")
    payload = {"value": 42}

    await cache_instance.set(key, payload)
    assert await cache_instance.get(key) == payload

    await cache_instance.delete(key)
    assert await cache_instance.get(key) is None


@pytest.mark.asyncio
async def test_get_or_set(cache_instance: InMemoryAsyncCache) -> None:
    key = cache_instance.get_key("compute")

    async def compute() -> dict:
        return {"generated": True}

    first = await cache_instance.get_or_set(key, compute)
    second = await cache_instance.get_or_set(key, compute)

    assert first == second == {"generated": True}


@pytest.mark.asyncio
async def test_invalidate_pattern(cache_instance: InMemoryAsyncCache) -> None:
    await cache_instance.set(cache_instance.get_key("users", 1), {"name": "Ada"})
    await cache_instance.set(cache_instance.get_key("users", 2), {"name": "Bob"})
    await cache_instance.set(cache_instance.get_key("devices", 1), {"name": "Cam"})

    await cache_instance.invalidate_pattern("test:users:*")

    assert await cache_instance.get(cache_instance.get_key("users", 1)) is None
    assert await cache_instance.get(cache_instance.get_key("users", 2)) is None
    assert await cache_instance.get(cache_instance.get_key("devices", 1)) == {"name": "Cam"}


@pytest.mark.asyncio
async def test_complex_payload_serialisation(cache_instance: InMemoryAsyncCache) -> None:
    key = cache_instance.get_key("complex")
    value = {
        "string": "hello",
        "number": 7,
        "list": [1, 2, 3],
        "nested": {"ts": datetime.utcnow().isoformat()},
    }

    await cache_instance.set(key, value)
    assert await cache_instance.get(key) == value
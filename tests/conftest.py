"""Pytest fixtures for the OBEX backend test suite."""

import asyncio
import os
import sys
from typing import Any, AsyncGenerator, Callable, Dict, Generator, Optional

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
	sys.path.insert(0, ROOT_DIR)

# Ensure each pytest worker uses an isolated SQLite database.
worker_id = os.environ.get("PYTEST_XDIST_WORKER")
db_suffix = worker_id or "test"
database_url = f"sqlite+aiosqlite:///./test_{db_suffix}.db"
os.environ["DATABASE_URL"] = database_url
os.environ["TEST_DATABASE_URL"] = database_url

from importlib import reload

from app.core import settings as settings_module

# Reset cached settings so the test database URL is honoured.
settings_module.get_settings.cache_clear()
settings_module.settings = settings_module.get_settings()

# Reload database modules so they pick up the updated settings.
import app.config.database as database_module

database_module = reload(database_module)
from app.config.database import Base, engine

import app.db.session as db_session_module

db_session_module = reload(db_session_module)

AsyncSessionLocal = db_session_module.AsyncSessionLocal

# Import models so metadata is loaded before schema creation.
from app import models as _models  # noqa: F401
from app.main import app
import app.services.cache as cache_module
from app.services.mqtt_client import mqtt_service
from app.services.websocket import manager


class InMemoryAsyncCache:
	"""A lightweight async cache used to stub Redis during tests."""

	def __init__(self, prefix: str = "test") -> None:
		self._prefix = prefix
		self._store: Dict[str, Any] = {}

	def get_key(self, *parts: Any) -> str:
		return ":".join([self._prefix, *[str(part) for part in parts if part is not None]])

	async def get(self, key: str) -> Optional[Any]:
		return self._store.get(key)

	async def set(self, key: str, value: Any, *, expire: Optional[int] = None) -> None:  # noqa: ARG002
		self._store[key] = value

	async def delete(self, key: str) -> None:
		self._store.pop(key, None)

	async def invalidate_pattern(self, pattern: str) -> None:
		from fnmatch import fnmatch

		for stored_key in list(self._store.keys()):
			if fnmatch(stored_key, pattern):
				del self._store[stored_key]

	async def clear_all(self) -> None:
		self._store.clear()

	async def get_or_set(
		self,
		key: str,
		getter: Callable[[], Any],
		*,
		expire: Optional[int] = None,  # noqa: ARG002
	) -> Any:
		cached = await self.get(key)
		if cached is not None:
			return cached

		value = getter()
		if asyncio.iscoroutine(value):
			value = await value

		await self.set(key, value)
		return value

	async def close(self) -> None:  # pragma: no cover - compatibility helper
		self._store.clear()


async def _recreate_schema() -> None:
	async with engine.begin() as conn:
		try:
			await conn.run_sync(Base.metadata.drop_all)
		except OperationalError:
			# Tables may not exist yet; ignore drop errors
			pass
		await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
	"""Provide a dedicated event loop for the entire test run."""
	loop = asyncio.new_event_loop()
	yield loop
	loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _initialise_database() -> AsyncGenerator[None, None]:
	await _recreate_schema()
	yield
	await _recreate_schema()


@pytest_asyncio.fixture(autouse=True)
async def _clean_database() -> AsyncGenerator[None, None]:
	await _recreate_schema()
	yield


@pytest.fixture(autouse=True)
def mock_cache(monkeypatch: pytest.MonkeyPatch) -> InMemoryAsyncCache:
	"""Replace the global Redis cache with an in-memory stub."""
	cache = InMemoryAsyncCache()
	monkeypatch.setattr(cache_module, "cache", cache)
	return cache


@pytest.fixture
def api_client(monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
	"""FastAPI test client with patched MQTT and WebSocket behaviours."""

	async def noop_broadcast(message: str) -> None:  # noqa: ARG001
		return None

	monkeypatch.setattr(manager, "broadcast", noop_broadcast)
	monkeypatch.setattr(mqtt_service, "start", lambda: None)
	monkeypatch.setattr(mqtt_service, "stop", lambda: None)

	asyncio.get_event_loop().run_until_complete(_recreate_schema())

	with TestClient(app) as client:
		yield client


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSessionLocal, None]:
	"""Yield an async session bound to the test database."""
	async with AsyncSessionLocal() as session:  # type: ignore[call-arg]
		yield session
		await session.rollback()

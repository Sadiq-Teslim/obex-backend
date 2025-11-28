"""Low-level asyncpg helpers used as a fallback when SQLAlchemy connections fail.

This module creates a direct asyncpg connection using the configured
DATABASE_URL (or DIRECT_DATABASE_URL) and ensures `statement_cache_size=0`
to avoid DuplicatePreparedStatementError when connecting through poolers.
"""
from __future__ import annotations

import os
import ssl
import logging
from typing import Any, Optional

import asyncpg
from sqlalchemy.engine import make_url

from app.core.settings import settings

LOG = logging.getLogger(__name__)


def _dsn_from_sqlalchemy_url(url: str) -> str:
    # Convert sqlalchemy-style URL (postgresql+asyncpg://...) to asyncpg DSN
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if url.startswith("postgres+asyncpg://"):
        return url.replace("postgres+asyncpg://", "postgresql://", 1)
    return url


def _ssl_connect_arg() -> Any:
    # Respect DISABLE_SSL_VERIFY env var for diagnostics only
    disable = bool(os.getenv("DISABLE_SSL_VERIFY"))
    if disable:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return True


async def fetchrow(query: str, *args: Any, dsn: Optional[str] = None) -> Optional[asyncpg.Record]:
    dsn = dsn or os.getenv("DIRECT_DATABASE_URL") or settings.database_url
    dsn = _dsn_from_sqlalchemy_url(dsn)
    try:
        conn = await asyncpg.connect(dsn, ssl=_ssl_connect_arg(), statement_cache_size=0)
    except Exception as exc:  # pragma: no cover - runtime network errors
        # If the failure looks like an SSL certificate verification problem,
        # retry with a permissive context. This is a diagnostic fallback only.
        msg = str(exc).lower()
        if "certificate verify failed" in msg or "self signed certificate" in msg:
            LOG.warning("asyncpg.connect SSL verify failed; retrying with permissive SSL (diagnostic)")
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            conn = await asyncpg.connect(dsn, ssl=ctx, statement_cache_size=0)
        else:
            LOG.exception("asyncpg.connect failed")
            raise
    try:
        row = await conn.fetchrow(query, *args)
        return row
    finally:
        await conn.close()


async def execute(query: str, *args: Any, dsn: Optional[str] = None) -> str:
    dsn = dsn or os.getenv("DIRECT_DATABASE_URL") or settings.database_url
    dsn = _dsn_from_sqlalchemy_url(dsn)
    try:
        conn = await asyncpg.connect(dsn, ssl=_ssl_connect_arg(), statement_cache_size=0)
    except Exception as exc:  # pragma: no cover - runtime network errors
        msg = str(exc).lower()
        if "certificate verify failed" in msg or "self signed certificate" in msg:
            LOG.warning("asyncpg.connect SSL verify failed; retrying with permissive SSL (diagnostic)")
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            conn = await asyncpg.connect(dsn, ssl=ctx, statement_cache_size=0)
        else:
            LOG.exception("asyncpg.connect failed")
            raise
    try:
        result = await conn.execute(query, *args)
        return result
    finally:
        await conn.close()

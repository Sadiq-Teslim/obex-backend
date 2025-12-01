from logging.config import fileConfig
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.config.database import Base  # Changed to use app.config
from app.core.settings import settings

config = context.config
if config.config_file_name is None:
    raise RuntimeError("Alembic config file name is not set. Check your Alembic configuration.")
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    if url is None:
        raise RuntimeError("sqlalchemy.url is not set in Alembic config. Check your Alembic configuration.")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    # Determine database URL: prefer DIRECT_DATABASE_URL (direct connection), then
    # environment DATABASE_URL, then alembic.ini, then project settings
    url = (
        os.getenv("DIRECT_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or config.get_main_option("sqlalchemy.url")
        or settings.database_url
    )
    if url is None:
        raise RuntimeError("No database URL found for running migrations")
    # For asyncpg connections to cloud Postgres (e.g., Supabase, Render), ensure SSL/TLS is enabled.
    if url.startswith("postgresql+asyncpg"):
        # asyncpg accepts an `ssl` connect arg rather than `sslmode` in the URL
        connectable = create_async_engine(url, connect_args={"ssl": True, "statement_cache_size": 0})
    else:
        connectable = create_async_engine(url)

    async def do_run_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(do_migrations)

    def do_migrations(connection: Connection):
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

    import asyncio
    asyncio.run(do_run_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

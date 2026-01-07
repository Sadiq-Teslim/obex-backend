from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv
import os

load_dotenv() 

from app.config.database import Base  # your Base
from app.models import user, camera, otp, alert  # import ALL models

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_online():
    connectable = engine_from_config(
        {
            "sqlalchemy.url": os.getenv("DATABASE_URL_SYNC")
        },
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # VERY IMPORTANT for Supabase
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()

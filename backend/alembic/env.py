# alembic/env.py

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── Import your app's Base and all models ─────────────────
# Models must be imported so Alembic can see them in Base.metadata
from app.config import settings
from app.database import Base

from app.models.user import User         # noqa: F401
from app.models.prompt import Prompt     # noqa: F401
from app.models.image import Image       # noqa: F401
from app.models.social import (          # noqa: F401
    Like, Comment, Follow,
    Collection, CollectionPrompt
)

# ──────────────────────────────────────────────────────────

config = context.config

# Pull DB URL from your settings instead of alembic.ini
# This way you never hard-code credentials
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
"""Alembic migration environment (online + offline).

Wired to the project's own settings/URL and metadata so migrations and
autogenerate operate on the exact same schema the application uses.  Nothing
here connects to a database at import time; connections are created only when
a migration is actually run.
"""

from __future__ import annotations

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Import models so Base.metadata is fully populated for autogenerate.
import backend.app.models.tables  # noqa: F401
from backend.app.core.config import settings
from backend.app.models.base import Base

config = context.config

# Inject the runtime URL from settings (never read credentials from ini).
config.set_main_option("sqlalchemy.url", settings.postgres_url)

if config.config_file_name is not None:
    try:
        fileConfig(config.config_file_name)
    except Exception:
        # Logging configuration is optional and must never block a migration.
        pass

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL, no DBAPI connection)."""
    context.configure(
        url=settings.postgres_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to the database)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
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


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

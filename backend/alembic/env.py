from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import models so metadata is populated
from app.db.base import Base  # noqa: E402
import app.db.models  # noqa: E402, F401

# Use DATABASE_URL env var if set (e.g. for autogenerate against SQLite),
# otherwise fall back to app Settings (which may be cached via lru_cache).
import os as _os  # noqa: E402
from app.config import get_settings  # noqa: E402
_db_url = _os.environ.get("DATABASE_URL") or get_settings().database_url
# Escape % so ConfigParser doesn't treat percent-encoded URL chars (e.g. a
# password containing %40/%2A) as interpolation syntax. ConfigParser un-escapes
# %% -> % when the value is read back, yielding the correct URL.
config.set_main_option("sqlalchemy.url", _db_url.replace("%", "%%"))

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

import sys
import os
from logging.config import fileConfig

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import engine_from_config, pool
from alembic import context
from app.core.config import settings
from app.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Normalize async URL to sync for Alembic CLI operations
cli_url = config.get_main_option("sqlalchemy.url")
if cli_url and cli_url != "driver://user:pass@localhost/dbname":
    db_url = cli_url
else:
    db_url = settings.DATABASE_URL

if "sqlite+aiosqlite" in db_url:
    sync_url = db_url.replace("sqlite+aiosqlite", "sqlite")
elif "postgresql+asyncpg" in db_url:
    sync_url = db_url.replace("postgresql+asyncpg", "postgresql")
else:
    sync_url = db_url

config.set_main_option("sqlalchemy.url", sync_url)

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

def run_migrations_online() -> None:
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

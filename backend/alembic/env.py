"""
Purpose: Alembic environment configuration.
         Reads DATABASE_URL from .env, imports all ORM models for autogenerate.
Owner: [Claude]
"""
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import create_engine, pool
from alembic import context
from dotenv import load_dotenv

# ── Load .env from backend root ─────────────────────────────────────────────
_backend_root = Path(__file__).resolve().parent.parent
load_dotenv(_backend_root / ".env")

# ── Add backend root to sys.path so app.* imports work ──────────────────────
sys.path.insert(0, str(_backend_root))

# ── Import all ORM models so Alembic autogenerate can discover them ──────────
from app.database import Base
import app.models  # noqa: F401 — side-effect import; registers all 15 models

# ── Alembic config ───────────────────────────────────────────────────────────
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from environment
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL not set. Check your .env file.")
config.set_main_option("sqlalchemy.url", database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Purpose: Run migrations in 'offline' mode — generates SQL without DB connection.
    Inputs: none
    Outputs: none
    Owner: [Claude]
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Purpose: Run migrations in 'online' mode — connects to the live database.
    Inputs: none
    Outputs: none
    Owner: [Claude]
    """
    connectable = create_engine(
        database_url,
        poolclass=pool.NullPool,
        connect_args={"options": "-c timezone=utc"},
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

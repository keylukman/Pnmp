"""
Alembic Environment Configuration
"""
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base
from app.core.config import settings
from app.models.models import *  # Import all models

# this is the Alembic Config object
config = context.config

# Override sqlalchemy.url from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def _run_stamp_without_db() -> None:
    """PNMP recovery helper: run ``alembic stamp <rev>`` WITHOUT a database
    connection (offline mode).

    Stamping only rewrites the single-row ``alembic_version`` table. When the
    configured PostgreSQL URL is unreachable or points at a different DB than
    the one being repaired, the normal online-mode stamp fails before it can
    help. Invoked via:  alembic -x noconnect=1 stamp <revision>
    """
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
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


_x_args = context.get_x_argument(as_dictionary=True)

if _x_args.get("noconnect"):
    if "stamp" not in sys.argv:
        raise RuntimeError(
            "noconnect=1 is only supported for `alembic stamp` "
            "(migrations must run against a live database)"
        )
    # Offline stamp: emit the UPDATE/INSERT for alembic_version as SQL text
    # (no DB connection needed). Usage:
    #   alembic -x noconnect=1 -x as_sql=1 stamp <revision> > stamp.sql
    # then execute stamp.sql with psql against the correct database.
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        as_sql=bool(_x_args.get("as_sql")),
    )
    with context.begin_transaction():
        context.run_migrations()
elif context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

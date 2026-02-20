from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

from alembic import context

# Import Base and ALL models so Alembic can see them for autogenerate
from app.models.base import Base
from app.models.user import User          # noqa: F401
from app.models.industry import Industry  # noqa: F401
from app.models.company import Company    # noqa: F401
from app.models.transcript import Transcript  # noqa: F401
from app.models.use_case import UseCase   # noqa: F401
from app.models.use_case_relation import UseCaseRelation  # noqa: F401
from app.models.comment import Comment    # noqa: F401
from app.config import settings

config = context.config

# Override sqlalchemy.url from our settings so .env is the single source of truth
# Use the SYNC URL for Alembic (alembic does not support async migrations)
config.set_main_option("sqlalchemy.url", settings.DATABASE_SYNC_URL)

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


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode using sync engine."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

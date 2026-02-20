#!/bin/bash
# scaffold.sh — Run from project root
# Creates the complete UseCase Manager directory structure
set -e

echo "🏗  Creating directory structure..."

mkdir -p alembic/versions
mkdir -p app/{models,schemas,handlers,services,repository,tasks,ai,utils}
mkdir -p tests

echo "📄 Creating app files..."
touch app/__init__.py
touch app/main.py
touch app/database.py
touch app/celery_app.py

# config.py — written immediately so alembic/env.py import works
cat > app/config.py << 'EOF'
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres — async URL for SQLAlchemy / FastAPI
    DATABASE_URL: str = "postgresql+asyncpg://ucm:ucm@localhost:5432/ucm"
    # Postgres — sync URL for Alembic migrations and Celery worker
    DATABASE_SYNC_URL: str = "postgresql://ucm:ucm@localhost:5432/ucm"

    REDIS_URL: str = "redis://localhost:6379/0"
    QDRANT_URL: str = "http://localhost:6333"
    OPENROUTER_API_KEY: str = ""
    SECRET: str = "change-me-in-production"


settings = Settings()
EOF

echo "📦 Creating models..."
for f in __init__ base user industry company transcript use_case use_case_relation comment enums; do
  touch app/models/$f.py
done

echo "📝 Creating schemas..."
for f in __init__ user industry company transcript use_case comment pagination; do
  touch app/schemas/$f.py
done

echo "🔌 Creating handlers..."
for f in __init__ auth users industries companies transcripts use_cases comments search events; do
  touch app/handlers/$f.py
done

echo "⚙️  Creating services..."
for f in __init__ company_service transcript_service use_case_service comment_service search_service; do
  touch app/services/$f.py
done

echo "🗄  Creating repositories..."
for f in __init__ base user_repo industry_repo company_repo transcript_repo use_case_repo comment_repo; do
  touch app/repository/$f.py
done

echo "⚡ Creating tasks & AI..."
touch app/tasks/__init__.py
touch app/tasks/transcript_tasks.py
for f in __init__ chains chunker embedder; do touch app/ai/$f.py; done

echo "🔧 Creating utils..."
for f in __init__ permissions pagination sse; do touch app/utils/$f.py; done

echo "🧪 Creating tests..."
touch tests/__init__.py
touch tests/conftest.py
touch tests/test_use_cases.py
touch tests/test_extraction.py

echo "📋 Creating root config files..."

# .env.example
cat > .env.example << 'EOF'
DATABASE_URL=postgresql+asyncpg://ucm:ucm@localhost:5432/ucm
DATABASE_SYNC_URL=postgresql://ucm:ucm@localhost:5432/ucm
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
OPENROUTER_API_KEY=sk-or-...
SECRET=your-secret-key-change-in-production
EOF

# alembic.ini
cat > alembic.ini << 'EOF'
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql://ucm:ucm@localhost:5432/ucm

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
EOF

# docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: "3.9"
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ucm
      POSTGRES_PASSWORD: ucm
      POSTGRES_DB: ucm
    ports: ["5432:5432"]
    volumes: ["postgres_data:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ucm"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes: ["qdrant_data:/qdrant/storage"]

  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    env_file: .env
    ports: ["8000:8000"]
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
      qdrant:
        condition: service_started
    volumes: [".:/app"]

  worker:
    build: .
    command: celery -A app.celery_app worker --loglevel=info --concurrency=2
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
      qdrant:
        condition: service_started
    volumes: [".:/app"]

volumes:
  postgres_data:
  qdrant_data:
EOF

# Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN pip install poetry==1.8.3
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

COPY . .

EXPOSE 8000
EOF

# pyproject.toml
cat > pyproject.toml << 'EOF'
[tool.poetry]
name = "usecase-manager"
version = "0.1.0"
description = "AI-powered use case management from workshop transcripts"
authors = []

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.115"
uvicorn = {extras = ["standard"], version = "^0.30"}
fastapi-users = {extras = ["sqlalchemy"], version = "^13"}
sqlalchemy = {extras = ["asyncio"], version = "^2.0"}
asyncpg = "^0.29"
psycopg2-binary = "^2.9"
alembic = "^1.13"
celery = {extras = ["redis"], version = "^5.4"}
redis = {extras = ["asyncio"], version = "^5.0"}
langchain = "^0.3"
langchain-openai = "^0.2"
openai = "^1.40"
qdrant-client = "^1.11"
pydantic-settings = "^2.4"
python-multipart = "^0.0.9"

[tool.poetry.dev-dependencies]
pytest = "^8"
pytest-asyncio = "^0.23"
httpx = "^0.27"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
asyncio_mode = "auto"
EOF

# alembic/env.py
cat > alembic/env.py << 'EOF'
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

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


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF

# README stub
cat > README.md << 'EOF'
# UseCase Manager

AI-powered use case extraction and management from workshop transcripts.

## Quick Start

```bash
# 1. Copy env
cp .env.example .env
# Edit .env with your OPENROUTER_API_KEY and SECRET

# 2. Start infrastructure
docker compose up -d db redis qdrant

# 3. Install deps
poetry install

# 4. Run migrations
alembic upgrade head

# 5. Start API
uvicorn app.main:app --reload

# 6. Start Celery worker (separate terminal)
celery -A app.celery_app worker --loglevel=info

# API docs available at http://localhost:8000/docs
```

## Or with Docker (all-in-one)

```bash
docker compose up --build
```

## Architecture

See ARCHITECTURE_PLAN.md
EOF

echo ""
echo "✅ Scaffold complete!"
echo ""
echo "Next steps:"
echo "  1. poetry install"
echo "  2. cp .env.example .env  (fill in OPENROUTER_API_KEY and SECRET)"
echo "  3. docker compose up -d db redis qdrant"
echo "  4. Write your models (app/models/*.py)"
echo "  5. alembic revision --autogenerate -m 'initial'   ← generates versions/xxxx_initial.py"
echo "  6. Review the generated file, then: alembic upgrade head"
echo "  7. uvicorn app.main:app --reload"
echo "  8. celery -A app.celery_app worker --loglevel=info  (separate terminal)"
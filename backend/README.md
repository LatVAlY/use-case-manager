# UseCase Manager

AI-powered use case extraction and management from workshop transcripts.

## Quick Start

```bash
# 1. Copy env
cd backend
cp .env.example .env
# Edit .env with your OPENROUTER_API_KEY and SECRET

# 2. Start infrastructure
docker compose up -d db redis qdrant

# 3. Install deps
poetry install

# 4. Run migrations
alembic upgrade head

# 5. Start API
export PROCESS=server
./run.sh

# 6. Start Celery worker (separate terminal)
export PROCESS=worker
./run.sh

# API docs available at http://localhost:8000/docs
```

## Or with Docker (all-in-one)

```bash
docker compose up --build
```

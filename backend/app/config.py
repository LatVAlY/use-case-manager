from pydantic_settings import BaseSettings, SettingsConfigDict
from app.environment import config


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres — async URL for SQLAlchemy / FastAPI
    DATABASE_URL: str = config["DATABASE_URL"]
    # Postgres — sync URL for Alembic migrations and Celery worker
    DATABASE_SYNC_URL: str = config["DATABASE_SYNC_URL"]

    REDIS_URL: str = config["REDIS_URL"]
    QDRANT_URL: str = config["QDRANT_URL"]
    OPENROUTER_API_KEY: str = config["OPENROUTER_API_KEY"]
    SECRET: str = config["SECRET_KEY"]

    # OpenAI / OpenRouter — models from env
    EMBEDDING_MODEL: str = "openai/text-embedding-3-small"
    CHAT_MODEL: str = "openai/gpt-4o-mini"

    # Knowledge base / Qdrant — rest hardcoded
    TRANSCRIPTS_COLLECTION: str = "transcripts"
    USE_CASES_COLLECTION: str = "use_cases"
    VECTOR_SIZE: int = 1536
    DENSE_VECTOR_NAME: str = "dense"
    SPARSE_VECTOR_NAME: str = "sparse"
    INITIAL_K: int = 20  # Results per prefetch before RRF fusion


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict
from app.environment import config


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres — async URL for SQLAlchemy / FastAPI
    DATABASE_URL: str =  config["DATABASE_URL"]
    # Postgres — sync URL for Alembic migrations and Celery worker
    DATABASE_SYNC_URL: str = config["DATABASE_SYNC_URL"]

    REDIS_URL: str = config["REDIS_URL"]
    QDRANT_URL: str = config["QDRANT_URL"]
    OPENROUTER_API_KEY: str = config["OPENROUTER_API_KEY"]
    SECRET: str = config["SECRET_KEY"]


settings = Settings()

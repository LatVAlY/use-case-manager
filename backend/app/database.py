from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.config import settings
from app.models import Base

# Async engine for FastAPI
async_engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True,
    pool_size=10,
    max_overflow=0,
)

# Async session factory for FastAPI
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# Sync engine for Alembic and Celery
sync_engine = create_engine(settings.DATABASE_SYNC_URL)

# Sync session for Celery
SyncSessionLocal = sessionmaker(bind=sync_engine)


async def get_async_session():
    """Dependency for FastAPI endpoints"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_db_tables():
    """Create all tables (called in startup)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db_tables():
    """Drop all tables (for testing)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

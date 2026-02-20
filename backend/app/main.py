"""FastAPI app - entry point for uvicorn app.main:app"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_db_tables
from app.dependencies import fastapi_users, auth_backend
from app.schemas import UserResponse, UserCreate
from app.ai.embedder import QdrantEmbedder
from app.ai.knowledge_base import KnowledgeBase
from app.handlers import (
    industries_router,
    companies_router,
    transcripts_router,
    use_cases_router,
    comments_router,
    search_router,
    users_router,
)
from app.handlers.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting up...")
    await create_db_tables()
    print("✓ Database tables created")
    embedder = QdrantEmbedder(settings.QDRANT_URL)
    kb = KnowledgeBase(settings.QDRANT_URL)
    try:
        # KB first so use_cases gets hybrid (dense+sparse) schema; embedder is legacy fallback
        kb.ensure_transcripts_collection()
        kb.ensure_use_cases_collection()
        embedder.ensure_collection_exists()
        print("✓ Qdrant collections initialized")
    except Exception as e:
        print(f"⚠ Qdrant init warning: {e}")
    yield
    print("🛑 Shutting down...")


app = FastAPI(
    title="UseCase Manager",
    description="AI-powered use case extraction from workshop transcripts",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserResponse, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(industries_router)
app.include_router(companies_router)
app.include_router(transcripts_router)
app.include_router(use_cases_router)
app.include_router(comments_router)
app.include_router(search_router)
app.include_router(users_router)
app.include_router(chat_router)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/")
async def root():
    return {"app": "UseCase Manager", "docs": "/docs", "v1": "0.1.0"}

"""
Centralized OpenAI client for OpenRouter (OpenAI-compatible API).
Single source for embeddings and chat LLM across the app.
"""
from openai import OpenAI
from langchain_openai import ChatOpenAI

from app.config import settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_openai_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    """Return the shared OpenAI client (OpenRouter)."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )
    return _openai_client


def get_chat_llm(
    model: str | None = None,
    temperature: float = 0.3,
) -> ChatOpenAI:
    """Return a ChatOpenAI instance for LangChain (OpenRouter)."""
    return ChatOpenAI(
        model=model or settings.CHAT_MODEL,
        openai_api_key=settings.OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        temperature=temperature,
    )

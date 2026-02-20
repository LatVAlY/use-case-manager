from app.handlers.users import router as users_router
from app.handlers.industries import router as industries_router
from app.handlers.companies import router as companies_router
from app.handlers.transcripts import router as transcripts_router
from app.handlers.use_cases import router as use_cases_router
from app.handlers.comments import router as comments_router
from app.handlers.search import router as search_router


__all__ = [
    "users_router",
    "industries_router",
    "companies_router",
    "transcripts_router",
    "use_cases_router",
    "comments_router",
    "search_router",
]

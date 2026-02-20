"""
Celery tasks for company-related operations.
"""
import logging

from app.celery_app import celery_app
from app.config import settings
from app.ai.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def cleanup_company_data(company_id: str):
    """
    Delete all Qdrant embeddings for a company (transcripts + use cases).
    DB records (use cases, transcripts, company) are deleted by the handler.
    """
    try:
        logger.info(f"Starting company embedding cleanup | company_id={company_id}")
        kb = KnowledgeBase(settings.QDRANT_URL)
        kb.delete_company_embeddings(company_id)
        logger.info(f"Company embedding cleanup completed | company_id={company_id}")
    except Exception as e:
        logger.exception(f"Company embedding cleanup failed | company_id={company_id} | error={e}")
        raise

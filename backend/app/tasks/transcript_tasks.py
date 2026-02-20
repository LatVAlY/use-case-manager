import json
import logging
from uuid import UUID
from sqlalchemy.orm import Session
from redis import Redis
from app.celery_app import celery_app
from app.database import SyncSessionLocal
from app.ai.chunker import chunk_transcript
from app.ai.chains import create_extraction_chain, create_reduction_chain
from app.config import settings
from app.models import Transcript, UseCase, Company
from app.models.enums import TranscriptStatus, UseCaseStatus
from app.ai.embedder import QdrantEmbedder

logger = logging.getLogger(__name__)


def publish_progress(transcript_id: str, event_type: str, data: dict):
    """Publish progress events to Redis"""
    redis_client = Redis.from_url(settings.REDIS_URL)
    channel = f"transcript:{transcript_id}"
    message = {"event": event_type, **data}
    try:
        redis_client.publish(channel, json.dumps(message))
    except Exception as e:
        logger.error(f"Failed to publish to {channel}: {e}")


@celery_app.task(bind=True)
def process_transcript(self, transcript_id: str):
    """
    Process a transcript: chunk → map → reduce → persist → embed
    """
    db: Session = SyncSessionLocal()
    embedder = QdrantEmbedder(settings.QDRANT_URL)
    task_id = self.request.id

    try:
        logger.info(f"Starting transcript processing | transcript_id={transcript_id} | task_id={task_id}")

        # ── Step 0: Load transcript ───────────────────────────────────────
        transcript = db.query(Transcript).filter(Transcript.id == UUID(transcript_id)).first()
        if not transcript:
            logger.error(f"Transcript not found | transcript_id={transcript_id}")
            return

        logger.info(f"Transcript loaded | id={transcript.id} | filename={transcript.filename} | company_id={transcript.company_id}")

        # Update status → processing
        transcript.status = TranscriptStatus.processing
        transcript.task_id = task_id
        db.commit()
        logger.info(f"Status updated to processing | transcript_id={transcript_id}")

        # Publish started
        publish_progress(transcript_id, "started", {"chunk_count": 0})
        logger.info(f"Started event published | transcript_id={transcript_id}")

        # ── Step 1: Chunking ───────────────────────────────────────────────
        logger.info(f"Starting chunking | transcript_id={transcript_id}")
        chunks = chunk_transcript(transcript.raw_text)
        chunk_count = len(chunks)

        transcript.chunk_count = chunk_count
        db.commit()
        logger.info(f"Chunking completed | transcript_id={transcript_id} | chunks={chunk_count}")


        extraction_chain = create_extraction_chain()
        all_use_cases = []

        for i, chunk in enumerate(chunks, 1):
            try:
                logger.debug(f"Processing chunk {i}/{chunk_count} | length={len(chunk)}")

                result = extraction_chain.invoke({"text": chunk})
                extracted_count = len(result.use_cases)
                all_use_cases.extend(result.use_cases)

                publish_progress(
                    transcript_id,
                    "chunk_done",
                    {"chunk": i, "total": chunk_count, "extracted": extracted_count}
                )

                transcript.chunks_processed = i
                db.commit()

                logger.info(f"Chunk processed | transcript_id={transcript_id} | chunk={i}/{chunk_count} | extracted={extracted_count}")

            except Exception as e:
                logger.exception(f"MAP failed on chunk {i}/{chunk_count} | error={str(e)}")
                publish_progress(transcript_id, "failed", {"error": str(e)})
                transcript.status = TranscriptStatus.failed
                transcript.error_message = str(e)
                db.commit()
                return

        logger.info(f"MAP phase completed | transcript_id={transcript_id} | raw_use_cases={len(all_use_cases)}")

        # ── Step 3: REDUCE – deduplicate & merge ───────────────────────────
        publish_progress(transcript_id, "reducing", {"raw_count": len(all_use_cases)})
        logger.info(f"Starting REDUCE phase | raw_count={len(all_use_cases)}")

        if all_use_cases:
            use_case_json = json.dumps(
                [uc.dict() for uc in all_use_cases],
                default=str
            )

            try:
                reduction_chain = create_reduction_chain()
                reduced_result = reduction_chain.invoke({"text": use_case_json})
                final_use_cases = reduced_result.use_cases
                logger.info(f"REDUCE completed | before={len(all_use_cases)} → after={len(final_use_cases)}")
            except Exception as e:
                logger.exception(f"REDUCE failed – falling back to raw results | error={str(e)}")
                final_use_cases = all_use_cases
        else:
            final_use_cases = []
            logger.info("No use cases to reduce – empty result")

        # ── Step 4: Persist to DB ──────────────────────────────────────────
        logger.info(f"Starting persistence | use_cases_count={len(final_use_cases)}")

        company = db.query(Company).filter(Company.id == transcript.company_id).first()
        if not company:
            logger.error(f"Company not found | company_id={transcript.company_id}")

        persisted_count = 0
        for uc_data in final_use_cases:
            try:
                new_uc = UseCase(
                    title=uc_data.title,
                    description=uc_data.description,
                    expected_benefit=uc_data.expected_benefit,
                    tags=uc_data.tags,
                    confidence_score=uc_data.confidence_score,
                    status=UseCaseStatus.new,
                    company_id=transcript.company_id,
                    transcript_id=UUID(transcript_id),
                    created_by_id=transcript.uploaded_by_id,
                )
                db.add(new_uc)
                db.flush()  # get ID if needed later

                # TODO: actual embedding + Qdrant upsert
                # embedder.upsert_use_case(new_uc.id, ...)

                persisted_count += 1

            except Exception as e:
                logger.exception(f"Failed to persist use case | title={uc_data.title[:80]} | error={str(e)}")

        db.commit()
        logger.info(f"Persistence completed | persisted={persisted_count}/{len(final_use_cases)}")

        # ── Finalize ───────────────────────────────────────────────────────
        transcript.status = TranscriptStatus.completed
        db.commit()

        publish_progress(
            transcript_id,
            "completed",
            {"use_cases_count": len(final_use_cases)}
        )
        logger.info(f"Transcript processing finished successfully | transcript_id={transcript_id} | use_cases={len(final_use_cases)}")

    except Exception as e:
        logger.exception(f"Critical task failure | transcript_id={transcript_id} | error={str(e)}")
        try:
            transcript.status = TranscriptStatus.failed
            transcript.error_message = str(e)
            db.commit()
            publish_progress(transcript_id, "failed", {"error": str(e)})
        except Exception as rollback_err:
            logger.error(f"Failed to rollback status | error={str(rollback_err)}")

    finally:
        db.close()
        logger.debug(f"Database session closed | transcript_id={transcript_id}")
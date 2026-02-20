from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.schemas import UserResponse
from app.models.enums import TranscriptStatus
from app.schemas import TranscriptCreate, TranscriptUpdate, TranscriptResponse
from app.services import TranscriptService
from app.utils.permissions import require_maintainer, require_admin
from app.utils.pagination import PaginationMixin
from app.utils.sse import subscribe_to_transcript_progress
from app.tasks import process_transcript
from app.celery_app import celery_app

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


class TranscriptListParams(PaginationMixin):
    company_id: Optional[UUID] = None
    status: Optional[TranscriptStatus] = None


@router.get("", response_model=dict)
async def list_transcripts(
    params: TranscriptListParams = Depends(),
    db: AsyncSession = Depends(get_async_session),
):
    """List transcripts with optional filters"""
    service = TranscriptService(db)
    
    if params.company_id:
        items, total = await service.list_by_company(params.company_id, params.skip, params.limit)
    elif params.status:
        items, total = await service.list_by_status(params.status, params.skip, params.limit)
    else:
        items, total = await service.list_transcripts(params.skip, params.limit)
    
    await db.commit()
    return {
        "items": [TranscriptResponse.model_validate(t) for t in items],
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": (total + params.page_size - 1) // params.page_size,
    }


@router.post("", response_model=TranscriptResponse, status_code=status.HTTP_201_CREATED)
async def upload_transcript(
    file: UploadFile = File(...),
    company_id: UUID = Form(...),
    current_user: UserResponse = Depends(require_maintainer),
    db: AsyncSession = Depends(get_async_session),
):
    """Upload a transcript and trigger AI extraction. Supports .txt, .md, .doc, .docx, .pdf."""
    service = TranscriptService(db)
    
    content = await file.read()
    filename = file.filename or "transcript.txt"
    ext = filename.lower().split(".")[-1] if "." in filename else ""

    if ext == "pdf":
        from app.ai.pdf_converter import pdf_to_markdown
        text = pdf_to_markdown(content, filename)
    else:
        text = content.decode("utf-8", errors="ignore")
    
    # Create transcript
    transcript_in = TranscriptCreate(
        filename=filename,
        raw_text=text,
        company_id=company_id,
        uploaded_by_id=current_user.id,
    )
    transcript = await service.create_transcript(transcript_in)
    
    await service.commit()
    
    # Trigger Celery task
    task = process_transcript.delay(str(transcript.id))
    transcript.task_id = task.id
    db.add(transcript)
    await db.commit()
    await db.refresh(transcript)
    
    return TranscriptResponse.model_validate(transcript)


@router.get("/{transcript_id}", response_model=TranscriptResponse)
async def get_transcript(
    transcript_id: UUID,
    db: AsyncSession = Depends(get_async_session),
):
    """Get a specific transcript"""
    service = TranscriptService(db)
    transcript = await service.get_transcript(transcript_id)
    if not transcript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")
    return TranscriptResponse.model_validate(transcript)


@router.delete("/{transcript_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transcript(
    transcript_id: UUID,
    current_user: UserResponse = Depends(require_admin),
    db: AsyncSession = Depends(get_async_session),
):
    """Delete a transcript"""
    service = TranscriptService(db)
    deleted = await service.delete_transcript(transcript_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")
    await service.commit()


@router.post("/{transcript_id}/reprocess")
async def reprocess_transcript(
    transcript_id: UUID,
    current_user: UserResponse = Depends(require_maintainer),
    db: AsyncSession = Depends(get_async_session),
):
    """Retry transcript extraction"""
    service = TranscriptService(db)
    transcript = await service.get_transcript(transcript_id)
    if not transcript:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transcript not found")
    
    # Reset progress and trigger task
    await service.update_progress(transcript_id, chunks_processed=0)
    task = process_transcript.delay(str(transcript_id))
    await service.update_task_id(transcript_id, task.id)
    await service.commit()
    
    return {"task_id": task.id}


@router.get("/{transcript_id}/events")
async def transcript_progress(transcript_id: UUID):
    """SSE stream for real-time transcript processing progress"""
    return StreamingResponse(
        subscribe_to_transcript_progress(str(transcript_id)),
        media_type="text/event-stream",
    )

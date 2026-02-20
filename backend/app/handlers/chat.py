"""
WebSocket chat handler with Langraph agent streaming.
Chat history persisted per user + company.
"""
import json
import base64
import logging
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal, get_async_session
from app.services import TranscriptService, UseCaseService, CompanyService, ChatService
from app.ai.knowledge_base import KnowledgeBase
from app.ai.agents.graph import create_chat_agent, stream_agent_response
from app.tasks import process_transcript
from app.schemas import TranscriptCreate
from app.config import settings
from app.dependencies import current_active_user
from app.schemas import UserResponse, ChatMessageResponse
import jwt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/messages", response_model=list[ChatMessageResponse])
async def list_chat_messages(
    company_id: Optional[UUID] = Query(None),
    current_user: UserResponse = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    """List chat history for the current user, optionally scoped by company."""
    service = ChatService(db)
    messages = await service.list_messages(
        user_id=current_user.id,
        company_id=company_id,
    )
    await db.commit()
    return messages


async def get_user_from_ws(websocket: WebSocket) -> dict | None:
    """Extract and validate user from WebSocket. Token in query ?token=."""
    token = websocket.query_params.get("token")
    if not token:
        return None
    try:
        # Skip audience check for WebSocket (fastapi-users uses "fastapi-users:auth")
        data = jwt.decode(
            token,
            settings.SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        if data and "sub" in data:
            return {"id": str(data["sub"]), "email": data.get("email", "")}
    except Exception:
        pass
    return None


@router.websocket("/ws")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()

    user = await get_user_from_ws(websocket)
    if not user:
        await websocket.send_json({"type": "error", "message": "Unauthorized"})
        await websocket.close()
        return

    company_id_raw = websocket.query_params.get("company_id")
    company_id: UUID | None = UUID(company_id_raw) if company_id_raw else None

    async def send_event(evt: dict):
        try:
            await websocket.send_json({"type": "event", "event": evt.get("type", ""), "data": evt})
        except Exception as e:
            logger.warning(f"Failed to send event: {e}")

    history: list = []

    try:
        async with AsyncSessionLocal() as db:
            transcript_service = TranscriptService(db)
            use_case_service = UseCaseService(db)
            company_service = CompanyService(db)
            kb = KnowledgeBase(settings.QDRANT_URL)

            context = {
                "transcript_service": transcript_service,
                "use_case_service": use_case_service,
                "company_service": company_service,
                "knowledge_base": kb,
                "user_id": user["id"],
            }
            agent = create_chat_agent(context)
            chat_service = ChatService(db)

            # Load persisted history for this user + company
            messages = await chat_service.list_messages(
                user_id=UUID(user["id"]),
                company_id=company_id,
            )
            history = [{"role": m.role, "content": m.content} for m in messages]
            for m in messages:
                await websocket.send_json({
                    "type": "message",
                    "role": m.role,
                    "content": m.content,
                })

            while True:
                raw = await websocket.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                    continue

                msg_type = msg.get("type", "message")
                content = msg.get("content", "")

                if msg_type == "upload":
                    # Handle transcript upload
                    filename = msg.get("filename", "upload.txt")
                    b64 = msg.get("content", "")
                    company_id = msg.get("company_id")
                    if not company_id or not b64:
                        await websocket.send_json({"type": "error", "message": "Missing company_id or content"})
                        continue
                    try:
                        file_bytes = base64.b64decode(b64)
                        ext = filename.lower().split(".")[-1] if "." in filename else ""
                        if ext == "pdf":
                            from app.ai.pdf_converter import pdf_to_markdown
                            text = pdf_to_markdown(file_bytes, filename)
                        else:
                            text = file_bytes.decode("utf-8", errors="ignore")
                        transcript_in = TranscriptCreate(
                            filename=filename,
                            raw_text=text,
                            company_id=UUID(company_id),
                            uploaded_by_id=UUID(user["id"]),
                        )
                        transcript = await transcript_service.create_transcript(transcript_in)
                        await transcript_service.commit()
                        process_transcript.delay(str(transcript.id))
                        upload_msg = f"Transcript **{filename}** uploaded and processing started. You can track progress in the Transcripts tab."
                        await websocket.send_json({
                            "type": "message",
                            "role": "assistant",
                            "content": upload_msg,
                        })
                        try:
                            await chat_service.add_message(
                                user_id=UUID(user["id"]),
                                role="user",
                                content=f"Uploaded {filename}",
                                company_id=company_id,
                            )
                            await chat_service.add_message(
                                user_id=UUID(user["id"]),
                                role="assistant",
                                content=upload_msg,
                                company_id=company_id,
                            )
                        except Exception as pe:
                            logger.warning(f"Failed to persist upload message: {pe}")
                    except Exception as e:
                        logger.exception(f"Upload failed: {e}")
                        await websocket.send_json({"type": "error", "message": str(e)})
                    continue

                if msg_type != "message" or not content:
                    continue

                # Stream agent response
                chunks = []
                async for chunk in stream_agent_response(
                    agent,
                    content,
                    history,
                    on_event=send_event,
                ):
                    chunks.append(chunk)
                    await websocket.send_json({"type": "chunk", "content": chunk})

                full = "".join(chunks)
                history.append({"role": "user", "content": content})
                history.append({"role": "assistant", "content": full})
                # Persist to DB
                try:
                    await chat_service.add_message(
                        user_id=UUID(user["id"]),
                        role="user",
                        content=content,
                        company_id=company_id,
                    )
                    await chat_service.add_message(
                        user_id=UUID(user["id"]),
                        role="assistant",
                        content=full,
                        company_id=company_id,
                    )
                except Exception as e:
                    logger.warning(f"Failed to persist chat message: {e}")
                await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        logger.info("Chat WebSocket disconnected")
    except Exception as e:
        logger.exception(f"Chat error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass

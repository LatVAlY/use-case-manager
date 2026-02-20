from uuid import UUID
from app.dependencies import require_maintainer
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_session
from app.models import User, Comment
from app.schemas import CommentCreate, CommentUpdate, CommentResponse, UserResponse
from app.services import CommentService
from app.utils.pagination import PaginationMixin

router = APIRouter(prefix="/use-cases/{use_case_id}/comments", tags=["comments"])


class CommentListParams(PaginationMixin):
    pass


@router.get("", response_model=dict)
async def list_comments(
    use_case_id: UUID,
    params: CommentListParams = Depends(),
    db: AsyncSession = Depends(get_async_session),
):
    """List comments on a use case"""
    service = CommentService(db)
    items, total = await service.list_by_use_case(use_case_id, params.skip, params.limit)
    await db.commit()
    return {
        "items": [CommentResponse.model_validate(c) for c in items],
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": (total + params.page_size - 1) // params.page_size,
    }


@router.post("", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    use_case_id: UUID,
    comment_in: CommentCreate,
    current_user: UserResponse = Depends(require_maintainer),
    db: AsyncSession = Depends(get_async_session),
):
    """Add a comment to a use case"""
    service = CommentService(db)
    
    # Create comment with author
    db_comment = Comment(
        body=comment_in.body,
        use_case_id=use_case_id,
        author_id=current_user.id,
    )
    db.add(db_comment)
    await db.flush()
    await db.refresh(db_comment)
    
    await service.commit()
    return CommentResponse.model_validate(db_comment)


@router.patch("/{comment_id}", response_model=CommentResponse)
async def update_comment(
    use_case_id: UUID,
    comment_id: UUID,
    comment_in: CommentUpdate,
    current_user: UserResponse = Depends(require_maintainer),
    db: AsyncSession = Depends(get_async_session),
):
    """Edit a comment (only own comment, or admin)"""
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    
    # Check ownership
    if comment.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    service = CommentService(db)
    updated = await service.update_comment(comment_id, comment_in)
    await service.commit()
    return CommentResponse.model_validate(updated)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    use_case_id: UUID,
    comment_id: UUID,
    current_user: UserResponse = Depends(require_maintainer),
    db: AsyncSession = Depends(get_async_session),
):
    """Delete a comment (only own comment, or admin)"""
    comment = await db.get(Comment, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    
    # Check ownership
    if comment.author_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    service = CommentService(db)
    await service.delete_comment(comment_id)
    await service.commit()

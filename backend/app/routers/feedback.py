"""
Feedback / support endpoints (v0.1 minimal).

This router provides:
- POST /feedback: authenticated user submits feedback
- GET  /feedback: admin lists feedback entries
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.deps import get_current_active_user, get_current_admin_user
from backend.app.db.database import get_db
from backend.app.db.models import Feedback, User


router = APIRouter()


class FeedbackCreateRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    contact: Optional[str] = Field(default=None, max_length=500)


class FeedbackResponse(BaseModel):
    id: str
    user_id: str
    message: str
    contact: Optional[str] = None
    created_at: str


@router.post("", response_model=FeedbackResponse)
@router.post("/", response_model=FeedbackResponse)
async def create_feedback(
    req: FeedbackCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit feedback as the current user.
    """
    fb = Feedback(
        user_id=current_user.id,
        message=req.message,
        contact=req.contact,
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return FeedbackResponse(
        id=fb.id,
        user_id=fb.user_id,
        message=fb.message,
        contact=fb.contact,
        created_at=fb.created_at.isoformat() if fb.created_at else "",
    )


@router.get("", response_model=List[FeedbackResponse])
@router.get("/", response_model=List[FeedbackResponse])
async def list_feedback(
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin-only: list feedback entries.
    """
    if limit <= 0:
        raise HTTPException(status_code=400, detail="limit must be positive")
    if limit > 500:
        raise HTTPException(status_code=400, detail="limit too large")

    rows = (
        await db.execute(
            select(Feedback).order_by(Feedback.created_at.desc()).limit(limit)
        )
    ).scalars().all()
    return [
        FeedbackResponse(
            id=fb.id,
            user_id=fb.user_id,
            message=fb.message,
            contact=fb.contact,
            created_at=fb.created_at.isoformat() if fb.created_at else "",
        )
        for fb in rows
    ]


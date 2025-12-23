import os
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.tts_wrapper_voxcpm import voxcpm_engine as tts_engine
from backend.app.core.config import settings
from backend.app.core.deps import get_current_active_user
from backend.app.db.database import get_db
from backend.app.db.models import User
from backend.app.db.crud_task import create_task, get_task, get_user_tasks
from backend.app.db.crud_credits import apply_credit_transaction
from backend.app.schemas.task import TaskStatusResponse

router = APIRouter()

class GenerateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    voice_id: str

class TaskResponse(BaseModel):
    task_id: str
    status: str
    cost: int
    output_url: Optional[str] = None


class TaskHistoryItem(BaseModel):
    task_id: str
    status: str
    cost: int
    voice_id: str
    text_excerpt: str
    output_url: Optional[str] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None

@router.post("/generate", response_model=TaskResponse)
async def generate_audio(
    req: GenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a TTS generation task.
    Requires authentication. Deducts credits based on text length.
    """
    # Validate voice path
    full_voice_path = os.path.join(settings.VOICE_ASSETS_DIR, req.voice_id)
    if not os.path.exists(full_voice_path):
        raise HTTPException(status_code=404, detail="Voice file not found")

    # Calculate cost
    cost = len(req.text) * settings.TTS_COST_PER_CHAR
    if cost < settings.MIN_CREDITS_REQUIRED:
        cost = settings.MIN_CREDITS_REQUIRED
    
    # Create task (no commit yet; commit together with credit ledger update)
    task = await create_task(
        db,
        user_id=current_user.id,
        text=req.text,
        voice_path=full_voice_path,
        cost=cost,
        commit=False
    )
    
    print(f"🎵 [TTS Router] Task created in DB: {task.id}")
    
    # Deduct credits and write ledger entry (no commit yet)
    charge_reason = f"TTS charge: {len(req.text)} chars"
    result = await apply_credit_transaction(
        db=db,
        user_id=current_user.id,
        amount=-cost,
        kind="TTS_CHARGE",
        reason=charge_reason,
        related_task_id=task.id,
    )
    if result is None:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Required: {cost}"
        )

    await db.commit()

    # v0.1: 入队后立即返回 task_id，推理由后台 worker 处理
    if tts_engine.queue is None:
        raise HTTPException(status_code=503, detail="TTS engine not initialized")
    await tts_engine.submit_task(task.id, req.text, full_voice_path)
    return TaskResponse(task_id=task.id, status="queued", cost=cost)

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status_endpoint(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Poll task status.
    Users can only access their own tasks.
    """
    task = await get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Authorization check
    if task.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this task")
    
    return TaskStatusResponse(
        task_id=task.id,
        status=task.status.lower(),
        output_url=task.output_url,
        error=task.error_message
    )


@router.get("/history", response_model=list[TaskHistoryItem])
async def list_my_tasks(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List current user's TTS task history (most recent first).

    Parameters:
    - limit: max number of tasks to return (default 50, max 200)
    """
    if limit <= 0:
        raise HTTPException(status_code=400, detail="limit must be positive")
    if limit > 200:
        raise HTTPException(status_code=400, detail="limit too large")

    tasks = await get_user_tasks(db, current_user.id, limit=limit)
    items: list[TaskHistoryItem] = []
    for t in tasks:
        voice_id = os.path.relpath(t.voice_path, settings.VOICE_ASSETS_DIR) if t.voice_path else ""
        text_excerpt = (t.text[:120] + "...") if t.text and len(t.text) > 120 else (t.text or "")
        items.append(
            TaskHistoryItem(
                task_id=t.id,
                status=t.status.lower(),
                cost=t.cost,
                voice_id=voice_id,
                text_excerpt=text_excerpt,
                output_url=t.output_url,
                error=t.error_message,
                created_at=t.created_at.isoformat() if t.created_at else "",
                completed_at=t.completed_at.isoformat() if t.completed_at else None,
            )
        )
    return items


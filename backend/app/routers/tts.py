import uuid
import asyncio
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
from backend.app.db.crud_task import create_task, get_task, update_task_status
from backend.app.db.crud_user import check_and_deduct_credits
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
    
    # Check and deduct credits
    success = await check_and_deduct_credits(db, current_user.id, cost)
    if not success:
        raise HTTPException(
            status_code=402,
            detail=f"Insufficient credits. Required: {cost}, Available: {current_user.credits_balance}"
        )
    
    # Create task in database  
    task = await create_task(
        db,
        user_id=current_user.id,
        text=req.text,
        voice_path=full_voice_path,
        cost=cost
    )
    
    print(f"🎵 [TTS Router] Task created in DB: {task.id}")
    
    # 同步执行TTS，简化为请求内完成（避免线程/队列问题）
    print(f"   Running TTS synchronously...")
    output_filename = f"{task.id}.wav"
    output_path = os.path.join(settings.GENERATED_AUDIO_DIR, output_filename)

    try:
        print(f"🚀 [Router] Starting inference in executor...")
        print(f"   Model initialized: {tts_engine.model is not None}")
        print(f"   Executor: {tts_engine.executor}")
        # 执行推理
        result = await asyncio.get_running_loop().run_in_executor(
            tts_engine.executor,
            tts_engine._run_inference,
            req.text,
            full_voice_path,
            output_path
        )
        print(f"✅ [Router] Inference completed: {result}")
        result_url = f"/static/generated/{output_filename}"
        await update_task_status(db, task.id, "COMPLETED", output_url=result_url)
        print(f"✅ Task {task.id} completed, URL: {result_url}")
        return TaskResponse(task_id=task.id, status="completed", cost=cost, output_url=result_url)
    except Exception as e:
        error_msg = str(e) if e else "Unknown error"
        print(f"❌ Task {task.id} failed: {error_msg}")
        import traceback
        traceback.print_exc()
        await update_task_status(db, task.id, "FAILED", error_message=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

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


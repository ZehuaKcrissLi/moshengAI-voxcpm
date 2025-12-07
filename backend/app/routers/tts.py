import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional
from backend.app.core.tts_wrapper import tts_engine
from backend.app.core.config import settings
import os

router = APIRouter()

# In-memory status store for MVP (Use DB in real implementation)
# This maps task_id -> {"status": "...", "output_url": "..."}
task_store = {}

class GenerateRequest(BaseModel):
    text: str
    voice_id: str # Relative path in prompt_voice
    # user_id: Optional[str] = None # Handle auth later

class TaskResponse(BaseModel):
    task_id: str
    status: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    output_url: Optional[str] = None
    error: Optional[str] = None

@router.post("/generate", response_model=TaskResponse)
async def generate_audio(req: GenerateRequest):
    """
    Submit a TTS generation task.
    """
    # Validate voice path
    full_voice_path = os.path.join(settings.VOICE_ASSETS_DIR, req.voice_id)
    if not os.path.exists(full_voice_path):
        raise HTTPException(status_code=404, detail="Voice file not found")

    # Submit to engine queue
    # For MVP integration with polling, we need to handle the future result.
    # The tts_engine.process_queue sets the future result.
    # We will create a background task that waits for the future and updates our task_store.
    
    task_id, future = await tts_engine.submit_task(req.text, full_voice_path)
    
    # Init status
    task_store[task_id] = {"status": "queued"}
    
    # Define a callback coroutine to update status
    async def wait_for_completion(fut, t_id):
        try:
            task_store[t_id]["status"] = "processing"
            result_url = await fut # This waits until future.set_result is called
            task_store[t_id]["status"] = "completed"
            task_store[t_id]["output_url"] = result_url
        except Exception as e:
            task_store[t_id]["status"] = "failed"
            task_store[t_id]["error"] = str(e)

    # Schedule this waiter
    import asyncio
    asyncio.create_task(wait_for_completion(future, task_id))
    
    return TaskResponse(task_id=task_id, status="queued")

@router.get("/status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    """
    Poll task status.
    """
    if task_id not in task_store:
        raise HTTPException(status_code=404, detail="Task not found")
    
    info = task_store[task_id]
    return TaskStatus(
        task_id=task_id,
        status=info["status"],
        output_url=info.get("output_url"),
        error=info.get("error")
    )


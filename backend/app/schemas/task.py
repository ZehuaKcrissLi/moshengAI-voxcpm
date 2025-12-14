from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TaskBase(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    voice_id: str

class TaskCreate(TaskBase):
    pass

class TaskResponse(BaseModel):
    id: str
    user_id: str
    text: str
    status: str
    cost: int
    output_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    output_url: Optional[str] = None
    error: Optional[str] = None


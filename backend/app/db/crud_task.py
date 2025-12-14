from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from typing import Optional, List
from backend.app.db.models import Task
import uuid
import datetime

async def create_task(
    db: AsyncSession,
    user_id: str,
    text: str,
    voice_path: str,
    cost: int = 0
) -> Task:
    task = Task(
        id=str(uuid.uuid4()),
        user_id=user_id,
        text=text,
        voice_path=voice_path,
        status="PENDING",
        cost=cost,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

async def get_task(db: AsyncSession, task_id: str) -> Optional[Task]:
    result = await db.execute(select(Task).filter(Task.id == task_id))
    return result.scalars().first()

async def update_task_status(
    db: AsyncSession,
    task_id: str,
    status: str,
    output_url: Optional[str] = None,
    error_message: Optional[str] = None
) -> Optional[Task]:
    values = {"status": status}
    if status == "COMPLETED":
        values["completed_at"] = datetime.datetime.now(datetime.timezone.utc)
    if output_url:
        values["output_url"] = output_url
    if error_message:
        values["error_message"] = error_message
    
    stmt = (
        update(Task)
        .where(Task.id == task_id)
        .values(**values)
        .returning(Task)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalars().first()

async def get_user_tasks(
    db: AsyncSession,
    user_id: str,
    limit: int = 50
) -> List[Task]:
    result = await db.execute(
        select(Task)
        .filter(Task.user_id == user_id)
        .order_by(Task.created_at.desc())
        .limit(limit)
    )
    return result.scalars().all()


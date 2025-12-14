from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from typing import Optional
from backend.app.db.models import User
import uuid

async def create_user(
    db: AsyncSession,
    email: str,
    hashed_password: Optional[str] = None,
    provider: str = "local",
    avatar: Optional[str] = None,
    initial_credits: int = 100
) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password=hashed_password,
        provider=provider,
        avatar=avatar,
        credits_balance=initial_credits,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalars().first()

async def update_user_credits(db: AsyncSession, user_id: str, credits_delta: int) -> Optional[User]:
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(credits_balance=User.credits_balance + credits_delta)
        .returning(User)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.scalars().first()

async def check_and_deduct_credits(db: AsyncSession, user_id: str, cost: int) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user or user.credits_balance < cost:
        return False
    
    stmt = (
        update(User)
        .where(User.id == user_id)
        .where(User.credits_balance >= cost)
        .values(credits_balance=User.credits_balance - cost)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


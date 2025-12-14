from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.models import Base
from backend.app.db.database import engine

async def create_tables():
    """
    Create all database tables.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def init_db():
    """
    Initialize database with default data if needed.
    """
    await create_tables()
    print("Database tables created successfully.")


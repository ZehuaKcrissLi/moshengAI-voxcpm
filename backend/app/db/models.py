import datetime
import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True) # Nullable for OAuth
    provider = Column(String, default="local") # local, google, wechat
    avatar = Column(String, nullable=True)
    credits_balance = Column(Integer, default=100) # Free credits on signup
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tasks = relationship("Task", back_populates="user")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True) # Nullable for demo/anonymous if needed
    text = Column(String, nullable=False)
    voice_path = Column(String, nullable=False)
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    output_url = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="tasks")


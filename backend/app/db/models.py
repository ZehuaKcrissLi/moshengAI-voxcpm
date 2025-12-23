import datetime
import uuid
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True) # Nullable for OAuth
    provider = Column(String, default="local") # local, google, github, wechat
    provider_user_id = Column(String, nullable=True) # OAuth provider user ID
    avatar = Column(String, nullable=True)
    credits_balance = Column(Integer, default=100) # Free credits on signup
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.utcnow())

    tasks = relationship("Task", back_populates="user")
    credit_transactions = relationship("CreditTransaction", back_populates="user")
    feedbacks = relationship("Feedback", back_populates="user")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True) # Nullable for demo/anonymous if needed
    text = Column(String, nullable=False)
    voice_path = Column(String, nullable=False)
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    cost = Column(Integer, default=0) # Credits consumed
    output_url = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.utcnow())
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="tasks")


class CreditTransaction(Base):
    """
    Credits ledger / transaction record.

    Usage:
    - TOPUP: manual recharge (admin) or future payment callback
    - TTS_CHARGE: deduct credits for a TTS task
    - ADJUSTMENT: admin adjustment
    - REFUND: refund on failed task / dispute
    """

    __tablename__ = "credit_transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # positive=credit, negative=debit
    kind = Column(String, nullable=False)  # TOPUP/TTS_CHARGE/ADJUSTMENT/REFUND
    reason = Column(String, nullable=False, default="")
    related_task_id = Column(String, ForeignKey("tasks.id"), nullable=True, index=True)
    external_ref = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.utcnow())

    user = relationship("User", back_populates="credit_transactions")
    task = relationship("Task")


class Feedback(Base):
    """
    User feedback / support ticket (minimal v0.1).

    Fields:
    - message: user-provided message (bug report / feature request)
    - contact: optional contact method (email/telegram/wechat id)
    """

    __tablename__ = "feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    message = Column(String, nullable=False)
    contact = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.utcnow())

    user = relationship("User", back_populates="feedbacks")


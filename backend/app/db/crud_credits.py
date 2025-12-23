"""
Credits ledger CRUD helpers.

This module centralizes all credit balance mutations so that:
- Every balance change is recorded as a `CreditTransaction`
- Balance updates are atomic (no "update balance but forget ledger")

No try/except is used by design: callers should handle and surface errors.
"""

from __future__ import annotations

from typing import Optional, Tuple

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import CreditTransaction, User


async def apply_credit_transaction(
    db: AsyncSession,
    user_id: str,
    amount: int,
    kind: str,
    reason: str,
    related_task_id: Optional[str] = None,
    external_ref: Optional[str] = None,
) -> Optional[Tuple[CreditTransaction, int]]:
    """
    Apply a credit balance change and write a ledger transaction.

    Parameters
    - db: SQLAlchemy AsyncSession
    - user_id: target user id
    - amount: positive=add credits, negative=deduct credits
    - kind: TOPUP / TTS_CHARGE / ADJUSTMENT / REFUND
    - reason: human-readable reason stored in ledger
    - related_task_id: optional task id to link a TTS charge/refund
    - external_ref: optional external payment reference

    Returns
    - (tx, new_balance)

    Returns None when the user is missing or credits are insufficient for deduction.
    """
    if amount == 0:
        raise ValueError("amount must be non-zero")
    if not reason:
        raise ValueError("reason must be non-empty")
    if not kind:
        raise ValueError("kind must be non-empty")

    stmt = update(User).where(User.id == user_id)
    if amount < 0:
        stmt = stmt.where(User.credits_balance >= (-amount))
    stmt = stmt.values(credits_balance=User.credits_balance + amount).returning(User.credits_balance)

    result = await db.execute(stmt)
    row = result.first()
    if row is None:
        return None

    new_balance = int(row[0])

    tx = CreditTransaction(
        user_id=user_id,
        amount=amount,
        kind=kind,
        reason=reason,
        related_task_id=related_task_id,
        external_ref=external_ref,
    )
    db.add(tx)
    await db.flush()
    return tx, new_balance


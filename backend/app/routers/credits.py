from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import select

from backend.app.core.deps import get_current_active_user, get_current_admin_user
from backend.app.db.database import get_db
from backend.app.db.crud_user import get_user_by_id
from backend.app.db.crud_credits import apply_credit_transaction
from backend.app.db.models import User, CreditTransaction

router = APIRouter()

class BalanceResponse(BaseModel):
    balance: int
    user_id: str

class AddCreditsRequest(BaseModel):
    user_id: str
    amount: int = Field(..., gt=0, le=100000)
    reason: str = Field(..., min_length=1, max_length=500)

class CreditTransactionResponse(BaseModel):
    id: str
    amount: int
    kind: str
    reason: str
    related_task_id: Optional[str] = None
    external_ref: Optional[str] = None
    created_at: str

@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's credit balance.
    """
    return {
        "balance": current_user.credits_balance,
        "user_id": current_user.id
    }

@router.post("/add")
async def add_credits(
    request: AddCreditsRequest,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin-only endpoint to manually add credits to a user account.
    For MVP, this is used for manual recharge/top-up.
    
    In production, replace with payment gateway integration.
    """
    target_user = await get_user_by_id(db, request.user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    result = await apply_credit_transaction(
        db=db,
        user_id=request.user_id,
        amount=request.amount,
        kind="TOPUP",
        reason=request.reason,
    )
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    _, new_balance = result
    await db.commit()
    
    return {
        "message": f"Added {request.amount} credits to user {request.user_id}",
        "new_balance": new_balance,
        "reason": request.reason
    }


@router.get("/transactions", response_model=List[CreditTransactionResponse])
async def list_transactions(
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List current user's credit transactions (ledger entries).

    Parameters:
    - limit: max number of records to return (default 50)
    """
    if limit <= 0:
        raise HTTPException(status_code=400, detail="limit must be positive")
    if limit > 200:
        raise HTTPException(status_code=400, detail="limit too large")

    rows = (
        await db.execute(
            select(CreditTransaction)
            .where(CreditTransaction.user_id == current_user.id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()

    return [
        CreditTransactionResponse(
            id=tx.id,
            amount=tx.amount,
            kind=tx.kind,
            reason=tx.reason,
            related_task_id=tx.related_task_id,
            external_ref=tx.external_ref,
            created_at=tx.created_at.isoformat() if tx.created_at else "",
        )
        for tx in rows
    ]


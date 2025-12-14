from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from backend.app.core.deps import get_current_active_user, get_current_admin_user
from backend.app.db.database import get_db
from backend.app.db.crud_user import update_user_credits, get_user_by_id
from backend.app.db.models import User

router = APIRouter()

class BalanceResponse(BaseModel):
    balance: int
    user_id: str

class AddCreditsRequest(BaseModel):
    user_id: str
    amount: int = Field(..., gt=0, le=100000)
    reason: str = Field(..., min_length=1, max_length=500)

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
    
    updated_user = await update_user_credits(db, request.user_id, request.amount)
    
    return {
        "message": f"Added {request.amount} credits to user {request.user_id}",
        "new_balance": updated_user.credits_balance,
        "reason": request.reason
    }


from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.security import get_password_hash, verify_password, create_access_token
from backend.app.core.deps import get_current_active_user
from backend.app.db.database import get_db
from backend.app.db.crud_user import create_user, get_user_by_email
from backend.app.db.models import User, CreditTransaction
from backend.app.schemas.user import RegisterRequest, UserResponse, Token, OAuthCallbackRequest
from backend.app.core.config import settings
from datetime import timedelta

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user with email and password.
    """
    # Check if user already exists
    existing_user = await get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(request.password)
    user = await create_user(
        db,
        email=request.email,
        hashed_password=hashed_password,
        provider="local",
        initial_credits=settings.NEW_USER_CREDITS
    )

    # Record signup bonus in credits ledger (balance already set on user row)
    tx = CreditTransaction(
        user_id=user.id,
        amount=settings.NEW_USER_CREDITS,
        kind="TOPUP",
        reason="Signup bonus",
    )
    db.add(tx)
    await db.commit()
    
    return user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password. Returns JWT access token.
    Username field should contain the email.
    """
    user = await get_user_by_email(db, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check provider
    if user.provider != "local":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This account uses {user.provider} login. Please use OAuth."
        )
    
    # Verify password
    if not user.hashed_password or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user information.
    """
    return current_user

@router.post("/oauth/callback", response_model=Token)
async def oauth_callback(
    request: OAuthCallbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth callback handler for Google, GitHub, and WeChat.
    This is a placeholder endpoint. Full implementation requires:
    
    1. Google OAuth:
       - Install google-auth, google-auth-oauthlib
       - Configure CLIENT_ID, CLIENT_SECRET in settings
       - Exchange code for token
       - Get user info from Google API
    
    2. GitHub OAuth:
       - Install httpx
       - Configure GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET
       - Exchange code for token
       - Get user info from GitHub API
    
    3. WeChat OAuth:
       - Install wechatpy
       - Configure WECHAT_APP_ID, WECHAT_APP_SECRET
       - Exchange code for access_token
       - Get user info from WeChat API
    
    For now, this returns a 501 Not Implemented error.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"OAuth login for {request.provider} is not yet implemented. Please use email/password registration."
    )

@router.get("/oauth/{provider}/login")
async def oauth_login(provider: str):
    """
    Initiate OAuth login flow.
    Returns the authorization URL to redirect the user to.
    
    Supported providers: google, github, wechat
    
    TODO: Implement OAuth URL generation for each provider
    """
    if provider not in ["google", "github", "wechat"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported provider"
        )
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"OAuth login for {provider} is not yet implemented. Please use email/password registration."
    )


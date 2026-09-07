from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.core.database import get_db
from app.schemas.auth import (
    UserCreate, 
    UserLogin, 
    Token, 
    TokenRefresh, 
    UserResponse, 
    LogoutResponse
)
from app.services.auth import create_user, get_user_by_email
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
import jwt

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    user = await create_user(db, user_in)
    return user

@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return tokens."""
    # Generic failure exception to avoid enumeration attacks
    auth_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    user = await get_user_by_email(db, login_data.email)
    if not user:
        raise auth_exception
        
    if not verify_password(login_data.password, user.password_hash):
        raise auth_exception
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
        
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    
    # Generate tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh(refresh_data: TokenRefresh, db: AsyncSession = Depends(get_db)):
    """Refresh access token using refresh token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(refresh_data.refresh_token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        # Verify this is actually a refresh token
        if user_id is None or token_type != "refresh":
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
        
    # Verify user is still active
    from sqlalchemy.future import select
    from app.models.user import User
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise credentials_exception
        
    # Generate new access token
    access_token = create_access_token(subject=user.id)
    
    return {
        "access_token": access_token,
        # Rotate refresh token
        "refresh_token": create_refresh_token(subject=user.id),
        "token_type": "bearer"
    }

@router.post("/logout", response_model=LogoutResponse)
async def logout():
    """
    Stateless logout endpoint.
    Note: Token invalidation requires a token blocklist or a persistent session mechanism.
    Since the current schema lacks a refresh-token or session table, tokens cannot be actively 
    revoked on the server side. The client must discard the token upon this response.
    """
    return {"success": True}

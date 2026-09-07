from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import UserCreate
from app.core.security import get_password_hash

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    # Normalize email
    normalized_email = email.strip().lower()
    stmt = select(User).where(User.email == normalized_email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    normalized_email = user_in.email.strip().lower()
    
    # Check duplicate
    existing_user = await get_user_by_email(db, normalized_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    hashed_password = get_password_hash(user_in.password)
    
    # According to requirements:
    # "Create the user's default settings/profile only if this is clearly required by the existing schema and architecture."
    # The schema doesn't strictly require settings/profile immediately, but since this is a typical flow, 
    # we'll only create the user for now to keep it lean. We can add them later if needed.
    # Actually, let's create the User only.
    
    new_user = User(
        email=normalized_email,
        name=user_in.name,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    await db.refresh(new_user)
    return new_user

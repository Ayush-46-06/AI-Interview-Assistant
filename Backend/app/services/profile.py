from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.profile import Profile
from app.schemas.profile import ProfileUpdate
from uuid import UUID

async def get_or_create_profile(db: AsyncSession, user_id: UUID) -> Profile:
    stmt = select(Profile).where(Profile.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalars().first()
    
    if profile is None:
        # Create a default empty profile
        profile = Profile(
            user_id=user_id,
            technologies=[],
            preferences={}
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)
        
    return profile

async def update_profile(db: AsyncSession, user_id: UUID, profile_in: ProfileUpdate) -> Profile:
    profile = await get_or_create_profile(db, user_id)
    
    update_data = profile_in.model_dump(exclude_unset=True)
    
    # Map preferences Pydantic model to dict if present
    if "preferences" in update_data and update_data["preferences"] is not None:
        # We merge existing preferences with new ones
        current_prefs = profile.preferences or {}
        # update_data["preferences"] is already a dict from model_dump
        new_prefs = update_data.pop("preferences")
        current_prefs.update(new_prefs)
        profile.preferences = current_prefs
        
    for field, value in update_data.items():
        setattr(profile, field, value)
        
    # The updated_at field will be automatically updated by SQLAlchemy's onupdate=func.now()
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(profile)
    return profile

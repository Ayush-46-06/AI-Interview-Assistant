from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from uuid import UUID

from app.models.setting import Setting
from app.schemas.setting import SettingsUpdate

async def get_or_create_settings(db: AsyncSession, user_id: UUID) -> Setting:
    stmt = select(Setting).where(Setting.user_id == user_id)
    result = await db.execute(stmt)
    setting = result.scalars().first()
    
    if setting is None:
        setting = Setting(user_id=user_id)
        db.add(setting)
        await db.commit()
        await db.refresh(setting)
        
    return setting

async def update_settings(db: AsyncSession, user_id: UUID, settings_in: SettingsUpdate) -> Setting:
    setting = await get_or_create_settings(db, user_id)
    
    # Validation logic for ethical disclaimer acceptance
    proposed_invisibility = settings_in.screen_invisibility_enabled
    proposed_disclaimer = settings_in.disclaimer_accepted
    
    # Determine the future state
    future_invisibility = proposed_invisibility if proposed_invisibility is not None else setting.screen_invisibility_enabled
    future_disclaimer = proposed_disclaimer if proposed_disclaimer is not None else setting.disclaimer_accepted
    
    if future_invisibility is True and future_disclaimer is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot enable screen invisibility without accepting the ethical practice disclaimer."
        )

    # Apply updates
    if proposed_invisibility is not None:
        setting.screen_invisibility_enabled = proposed_invisibility
    
    if proposed_disclaimer is not None:
        setting.disclaimer_accepted = proposed_disclaimer
        
    if settings_in.other_preferences is not None:
        # Partial update logic
        current_prefs = dict(setting.other_preferences) if setting.other_preferences else {}
        for k, v in settings_in.other_preferences.items():
            current_prefs[k] = v
        setting.other_preferences = current_prefs
        
    db.add(setting)
    await db.commit()
    await db.refresh(setting)
    
    return setting

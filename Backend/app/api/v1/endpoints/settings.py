from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.setting import SettingsResponse, SettingsUpdate
from app.services.setting import update_settings

router = APIRouter()

@router.put("/", response_model=SettingsResponse)
async def update_user_settings(
    settings_in: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the authenticated user's settings.
    """
    try:
        setting = await update_settings(db, current_user.id, settings_in)
        return setting
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating settings."
        )

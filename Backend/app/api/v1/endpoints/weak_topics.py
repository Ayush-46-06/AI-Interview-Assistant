from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.weak_topic import WeakTopicResponse
from app.services.weak_topic import get_weak_topics

router = APIRouter()

@router.get("/", response_model=List[WeakTopicResponse])
async def list_weak_topics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get weak topics for the authenticated user."""
    return await get_weak_topics(db, current_user.id)

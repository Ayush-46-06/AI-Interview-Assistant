from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.analytics import AnalyticsResponse
from app.services.analytics import get_user_analytics

router = APIRouter()

@router.get("/", response_model=AnalyticsResponse)
async def get_analytics(
    timeRange: str = Query("all", description="Time range for analytics (7d, 30d, 90d, all)"),
    filter: Optional[str] = Query(None, description="Status filter for sessions (e.g., 'completed')"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics for the authenticated user."""
    return await get_user_analytics(db, current_user.id, time_range=timeRange, status_filter=filter)

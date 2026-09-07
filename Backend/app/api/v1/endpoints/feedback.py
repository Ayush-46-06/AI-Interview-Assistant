from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.feedback import FeedbackCreate, FeedbackResponse
from app.services.feedback import create_feedback

router = APIRouter()

@router.post("/", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback_in: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit feedback for an AI answer."""
    return await create_feedback(db, current_user.id, feedback_in)

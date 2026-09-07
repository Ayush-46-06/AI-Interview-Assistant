from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.schemas.session import (
    SessionCreate, SessionResponse, PaginatedSessionResponse, 
    SessionDetailResponse, QuestionCreate, QuestionResponse,
    AnswerCreate, AnswerResponse
)
from app.services.session import (
    create_session, get_sessions_for_user, get_session_detail,
    create_question, create_answer
)

router = APIRouter()

@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_new_session(
    session_in: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new interview session."""
    return await create_session(db, current_user.id, session_in)

@router.get("/", response_model=PaginatedSessionResponse)
async def list_sessions(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List sessions for the authenticated user."""
    skip = (page - 1) * limit
    sessions, total = await get_sessions_for_user(db, current_user.id, skip, limit)
    return PaginatedSessionResponse(sessions=sessions, total=total)

@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get details of a specific interview session including questions and answers."""
    return await get_session_detail(db, current_user.id, session_id)

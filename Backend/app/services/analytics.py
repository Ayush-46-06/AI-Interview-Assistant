from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.models.interview_session import InterviewSession
from app.models.question import Question
from app.models.answer import Answer
from app.models.feedback import Feedback
from app.schemas.analytics import AnalyticsResponse

async def get_user_analytics(db: AsyncSession, user_id: UUID, time_range: str = "all", status_filter: str = None) -> AnalyticsResponse:
    session_conditions = [InterviewSession.user_id == user_id]
    
    if time_range != "all":
        # Ensure UTC timezone aware or naive depending on app config, we'll use naive utcnow since models use func.now()
        now = datetime.utcnow()
        if time_range == "7d":
            start_date = now - timedelta(days=7)
        elif time_range == "30d":
            start_date = now - timedelta(days=30)
        elif time_range == "90d":
            start_date = now - timedelta(days=90)
        else:
            raise HTTPException(status_code=400, detail="Invalid timeRange. Allowed: '7d', '30d', '90d', 'all'")
        session_conditions.append(InterviewSession.created_at >= start_date)
        
    if status_filter:
        if status_filter == "completed":
            session_conditions.append(InterviewSession.ended_at.is_not(None))
        elif status_filter == "active":
            session_conditions.append(InterviewSession.ended_at.is_(None))
        
    # Total sessions
    stmt = select(func.count(InterviewSession.id)).where(*session_conditions)
    result = await db.execute(stmt)
    total_sessions = result.scalar() or 0
    
    # Completed sessions
    stmt_comp = select(func.count(InterviewSession.id)).where(InterviewSession.ended_at.is_not(None)).where(*session_conditions)
    result_comp = await db.execute(stmt_comp)
    completed_sessions = result_comp.scalar() or 0
    
    # Average score
    stmt_score = select(func.avg(InterviewSession.score)).where(*session_conditions).where(InterviewSession.score.is_not(None))
    result_score = await db.execute(stmt_score)
    average_score = result_score.scalar()
    
    # Base conditions for questions joins
    question_conditions = [InterviewSession.user_id == user_id]
    if time_range != "all":
        question_conditions.append(InterviewSession.created_at >= start_date)
    if status_filter:
        if status_filter == "completed":
            question_conditions.append(InterviewSession.ended_at.is_not(None))
        elif status_filter == "active":
            question_conditions.append(InterviewSession.ended_at.is_(None))
        
    # Total questions
    stmt_q = select(func.count(Question.id)).join(InterviewSession, Question.session_id == InterviewSession.id).where(*question_conditions)
    result_q = await db.execute(stmt_q)
    total_questions = result_q.scalar() or 0
    
    # Answered questions
    stmt_aq = select(func.count(Question.id)).join(InterviewSession, Question.session_id == InterviewSession.id).where(Question.is_answered == True).where(*question_conditions)
    result_aq = await db.execute(stmt_aq)
    answered_questions = result_aq.scalar() or 0
    
    # Average feedback rating
    stmt_f = (
        select(func.avg(Feedback.rating))
        .join(Answer, Feedback.answer_id == Answer.id)
        .join(Question, Answer.question_id == Question.id)
        .join(InterviewSession, Question.session_id == InterviewSession.id)
        .where(*question_conditions)
        .where(Feedback.rating.is_not(None))
    )
    result_f = await db.execute(stmt_f)
    average_rating = result_f.scalar()
    
    return AnalyticsResponse(
        total_sessions=total_sessions,
        completed_sessions=completed_sessions,
        total_questions=total_questions,
        answered_questions=answered_questions,
        average_score=float(average_score) if average_score is not None else None,
        average_rating=float(average_rating) if average_rating is not None else None
    )

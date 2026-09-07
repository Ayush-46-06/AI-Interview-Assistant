from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from uuid import UUID
from fastapi import HTTPException, status
from typing import Tuple, List

from app.models.interview_session import InterviewSession
from app.models.question import Question
from app.models.answer import Answer
from app.schemas.session import SessionCreate, QuestionCreate, AnswerCreate

async def create_session(db: AsyncSession, user_id: UUID, session_in: SessionCreate) -> InterviewSession:
    new_session = InterviewSession(
        user_id=user_id,
        mode=session_in.mode,
        target_role=session_in.target_role,
        question_count=0
    )
    db.add(new_session)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(new_session)
    return new_session

async def get_sessions_for_user(db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 10) -> Tuple[List[InterviewSession], int]:
    # Query for total count
    count_stmt = select(func.count()).select_from(InterviewSession).where(InterviewSession.user_id == user_id)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0
    
    # Query for paginated list
    stmt = (
        select(InterviewSession)
        .where(InterviewSession.user_id == user_id)
        .order_by(InterviewSession.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    sessions = list(result.scalars().all())
    
    return sessions, total

async def get_session_detail(db: AsyncSession, user_id: UUID, session_id: UUID) -> InterviewSession:
    stmt = (
        select(InterviewSession)
        .options(selectinload(InterviewSession.questions).selectinload(Question.answers))
        .where(InterviewSession.id == session_id)
        .where(InterviewSession.user_id == user_id)
    )
    result = await db.execute(stmt)
    session = result.scalars().first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
    return session

async def create_question(db: AsyncSession, user_id: UUID, question_in: QuestionCreate) -> Question:
    # 1. Verify session exists and belongs to user
    stmt = select(InterviewSession).where(InterviewSession.id == question_in.session_id).where(InterviewSession.user_id == user_id)
    result = await db.execute(stmt)
    session = result.scalars().first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or unauthorized")
        
    # 2. Create question and increment session question count transactionally
    new_question = Question(
        session_id=session.id,
        transcript=question_in.transcript,
        category=question_in.category,
        difficulty=question_in.difficulty,
        is_answered=False
    )
    db.add(new_question)
    
    # Increment count
    session.question_count += 1
    
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
        
    await db.refresh(new_question)
    return new_question

async def update_question(db: AsyncSession, user_id: UUID, question_id: UUID, transcript: str) -> Question:
    stmt = (
        select(Question)
        .join(InterviewSession, Question.session_id == InterviewSession.id)
        .where(Question.id == question_id)
        .where(InterviewSession.user_id == user_id)
    )
    result = await db.execute(stmt)
    question = result.scalars().first()
    
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found or unauthorized")
        
    question.transcript = transcript
    try:
        await db.commit()
        await db.refresh(question)
    except Exception:
        await db.rollback()
        raise
        
    return question

async def create_answer(db: AsyncSession, user_id: UUID, question_id: UUID, answer_in: AnswerCreate) -> Answer:
    # 1. Verify question exists and its parent session belongs to the user
    stmt = (
        select(Question)
        .join(InterviewSession, Question.session_id == InterviewSession.id)
        .where(Question.id == question_id)
        .where(InterviewSession.user_id == user_id)
    )
    result = await db.execute(stmt)
    question = result.scalars().first()
    
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found or unauthorized")
        
    # 2. Create answer and set question.is_answered = True transactionally
    new_answer = Answer(
        question_id=question.id,
        answer_text=answer_in.answer_text,
        model=answer_in.model,
        mode=answer_in.mode,
        latency_ms=answer_in.latency_ms,
        token_usage=answer_in.token_usage or {},
        is_regenerated=answer_in.is_regenerated
    )
    db.add(new_answer)
    
    question.is_answered = True
    
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
        
    await db.refresh(new_answer)
    return new_answer

async def end_session(db: AsyncSession, user_id: UUID, session_id: UUID) -> InterviewSession:
    stmt = select(InterviewSession).where(InterviewSession.id == session_id).where(InterviewSession.user_id == user_id)
    result = await db.execute(stmt)
    session = result.scalars().first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        
    from datetime import datetime
    session.ended_at = datetime.utcnow()
    
    try:
        await db.commit()
        await db.refresh(session)
    except Exception:
        await db.rollback()
        raise
        
    # Calculate and update session score
    from app.services.feedback import calculate_session_score
    await calculate_session_score(db, session_id)
    await db.refresh(session)
        
    return session

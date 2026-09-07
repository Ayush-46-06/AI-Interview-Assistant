from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from fastapi import HTTPException, status
from decimal import Decimal
from datetime import datetime

from app.models.feedback import Feedback
from app.models.answer import Answer
from app.models.question import Question
from app.models.interview_session import InterviewSession
from app.models.weak_topic import WeakTopic
from app.schemas.feedback import FeedbackCreate

async def update_weak_topics_on_feedback(db: AsyncSession, user_id: UUID, question_category: str, rating: int):
    if rating > 3 or not question_category:
        return
        
    stmt = select(WeakTopic).where(WeakTopic.user_id == user_id).where(WeakTopic.topic == question_category)
    result = await db.execute(stmt)
    weak_topic = result.scalars().first()
    
    score_mapping = {1: 20, 2: 40, 3: 60, 4: 80, 5: 100}
    new_score = score_mapping.get(rating, 0)
    
    if weak_topic:
        weak_topic.frequency += 1
        weak_topic.last_encountered = datetime.utcnow()
        if weak_topic.avg_score is not None:
            weak_topic.avg_score = float((Decimal(str(weak_topic.avg_score)) * (weak_topic.frequency - 1) + Decimal(new_score)) / weak_topic.frequency)
        else:
            weak_topic.avg_score = float(new_score)
    else:
        weak_topic = WeakTopic(
            user_id=user_id,
            topic=question_category,
            category=question_category,
            frequency=1,
            avg_score=float(new_score)
        )
        db.add(weak_topic)

async def create_feedback(db: AsyncSession, user_id: UUID, feedback_in: FeedbackCreate) -> Feedback:
    stmt = (
        select(Answer, Question)
        .join(Question, Answer.question_id == Question.id)
        .join(InterviewSession, Question.session_id == InterviewSession.id)
        .where(Answer.id == feedback_in.answer_id)
        .where(InterviewSession.user_id == user_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Answer not found or unauthorized")
        
    answer, question = row
    
    new_feedback = Feedback(
        answer_id=feedback_in.answer_id,
        rating=feedback_in.rating,
        notes=feedback_in.notes
    )
    db.add(new_feedback)
    
    if question.category:
        await update_weak_topics_on_feedback(db, user_id, question.category, feedback_in.rating)
    
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
        
    await db.refresh(new_feedback)
    return new_feedback

async def calculate_session_score(db: AsyncSession, session_id: UUID):
    stmt = (
        select(Feedback.rating)
        .join(Answer, Feedback.answer_id == Answer.id)
        .join(Question, Answer.question_id == Question.id)
        .where(Question.session_id == session_id)
        .where(Feedback.rating.is_not(None))
    )
    result = await db.execute(stmt)
    ratings = result.scalars().all()
    
    stmt_session = select(InterviewSession).where(InterviewSession.id == session_id)
    session_result = await db.execute(stmt_session)
    session = session_result.scalars().first()
    
    if not session:
        return
        
    if not ratings:
        session.score = None
    else:
        score_mapping = {1: 20, 2: 40, 3: 60, 4: 80, 5: 100}
        total_score = sum(score_mapping.get(r, 0) for r in ratings)
        session.score = float(total_score / len(ratings))
        
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

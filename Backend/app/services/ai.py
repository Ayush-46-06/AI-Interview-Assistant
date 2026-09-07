import time
from uuid import UUID
from typing import Optional, Dict, Any, AsyncGenerator, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from groq import AsyncGroq
import groq

from app.core.config import settings
from app.models.interview_session import InterviewSession
from app.models.question import Question
from app.models.profile import Profile
from app.schemas.session import AnswerCreate, AnswerMode

def get_groq_client() -> Optional[AsyncGroq]:
    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your_groq_api_key_here":
        return None
    return AsyncGroq(api_key=settings.GROQ_API_KEY)

def build_system_prompt(profile: Profile, session: InterviewSession, mode: AnswerMode) -> str:
    prompt = "You are an expert AI Interview Assistant helping a candidate prepare for an interview.\n\n"
    
    prompt += "CONTEXT:\n"
    if session.target_role:
        prompt += f"Target Role: {session.target_role}\n"
    elif profile and profile.target_role:
        prompt += f"Target Role: {profile.target_role}\n"
        
    if profile and profile.technologies:
        prompt += f"Technologies: {', '.join(profile.technologies)}\n"
        
    if profile:
        if profile.resume_text:
            prompt += f"Resume Context: {profile.resume_text}\n"
        if profile.jd_text:
            prompt += f"Job Description: {profile.jd_text}\n"
            
        prefs = profile.preferences or {}
        if prefs.get("experience_years") is not None:
            prompt += f"Experience Level: {prefs['experience_years']} years\n"
        if prefs.get("current_company"):
            prompt += f"Current Company: {prefs['current_company']}\n"
        if prefs.get("company_info"):
            prompt += f"Company Information: {prefs['company_info']}\n"
        if prefs.get("behavioral_context"):
            prompt += f"Behavioral Context: {prefs['behavioral_context']}\n"
        if prefs.get("past_projects"):
            prompt += f"Past Projects: {', '.join(prefs['past_projects'])}\n"
        if prefs.get("key_achievements"):
            prompt += f"Key Achievements: {', '.join(prefs['key_achievements'])}\n"
        
    if session.mode:
        prompt += f"Interview Mode: {session.mode}\n"
        
    prompt += "\nINSTRUCTIONS:\n"
    prompt += "- Answer the user's interview question directly.\n"
    prompt += "- Be interview-ready and practical.\n"
    prompt += "- Avoid meta commentary or saying 'as an AI'.\n"
    prompt += "- Do not fabricate personal experience.\n"
    
    # Adapt to Interview Mode
    if session.mode:
        smode = session.mode.lower()
        if "behavioral" in smode or "hr" in smode:
            prompt += "- For behavioral questions, guide the model toward an appropriate interview-style response.\n"
        elif "technical" in smode or "coding" in smode:
            prompt += "- For coding/technical questions, prioritize technically correct and interview-usable answers.\n"
        elif "rapid-fire" in smode:
            prompt += "- Keep answers very concise and rapid-fire style.\n"
            
    # Adapt to Answer Mode
    if mode == AnswerMode.STAR:
        prompt += "- Structure the response around Situation, Task, Action, Result when appropriate (unless it's a purely technical question where STAR doesn't make sense).\n"
    elif mode == AnswerMode.SHORT:
        prompt += "- Keep the answer very concise and interview-ready.\n"
    elif mode == AnswerMode.NORMAL:
        prompt += "- Provide a balanced, moderate-length answer.\n"
    elif mode == AnswerMode.DETAILED:
        prompt += "- Provide a comprehensive and highly detailed interview-ready answer.\n"

    return prompt

async def get_question_and_profile(db: AsyncSession, user_id: UUID, question_id: UUID):
    stmt = (
        select(Question, InterviewSession)
        .join(InterviewSession, Question.session_id == InterviewSession.id)
        .where(Question.id == question_id)
        .where(InterviewSession.user_id == user_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found or unauthorized")
        
    question, session = row
    
    stmt_prof = select(Profile).where(Profile.user_id == user_id)
    prof_result = await db.execute(stmt_prof)
    profile = prof_result.scalars().first()
    
    return question, session, profile

async def generate_interview_answer(
    db: AsyncSession, 
    user_id: UUID, 
    question_id: UUID, 
    answer_mode: AnswerMode,
    is_regenerated: bool = False
) -> AnswerCreate:
    question, session, profile = await get_question_and_profile(db, user_id, question_id)
    
    system_prompt = build_system_prompt(profile, session, answer_mode)
    user_prompt = f"Question: {question.transcript}"
    
    client = get_groq_client()
    model_name = settings.GROQ_MODEL
    
    if not client:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI generation service is not configured")
    
    start_time = time.time()
    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model_name,
        )
    except groq.GroqError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI Generation failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during AI generation")
        
    latency_ms = int((time.time() - start_time) * 1000)
    answer_text = chat_completion.choices[0].message.content or ""
    
    usage = chat_completion.usage
    token_usage = {}
    if usage:
        token_usage = {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens
        }
        
    return AnswerCreate(
        question_id=question_id,
        answer_text=answer_text,
        model=model_name,
        mode=answer_mode.value,
        latency_ms=latency_ms,
        token_usage=token_usage,
        is_regenerated=is_regenerated
    )

async def stream_interview_answer(
    db: AsyncSession, 
    user_id: UUID, 
    question_id: UUID, 
    answer_mode: AnswerMode
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Streams the AI generated answer chunks and metadata.
    Yields:
      {"type": "chunk", "content": "..."}
      {"type": "meta", "latency_ms": 1200, "token_usage": {...}, "model": "..."}
    """
    question, session, profile = await get_question_and_profile(db, user_id, question_id)
    system_prompt = build_system_prompt(profile, session, answer_mode)
    user_prompt = f"Question: {question.transcript}"
    
    client = get_groq_client()
    model_name = settings.GROQ_MODEL
    
    if not client:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI generation service is not configured")

    start_time = time.time()
    try:
        stream = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=model_name,
            stream=True
        )
        
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content is not None:
                yield {"type": "chunk", "content": content}
                
    except groq.GroqError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"AI Generation failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred during AI generation")
        
    latency_ms = int((time.time() - start_time) * 1000)
    
    # We do not have token_usage readily available from groq streams unless requested explicitly via stream_options
    # We'll just return what we have.
    yield {
        "type": "meta",
        "latency_ms": latency_ms,
        "token_usage": {},
        "model": model_name
    }

async def generate_followup_suggestions(
    db: AsyncSession, 
    user_id: UUID, 
    question_id: UUID, 
    answer_text: str
) -> List[str]:
    question, session, profile = await get_question_and_profile(db, user_id, question_id)
    
    system_prompt = (
        "You are an AI Interview Assistant.\n"
        "Generate 2 concise follow-up interview questions based on the candidate's previous answer.\n"
        "Output ONLY the questions, separated by newlines."
    )
    user_prompt = f"Original Question: {question.transcript}\nCandidate Answer: {answer_text}"
    
    client = get_groq_client()
    if not client:
        return [] # Safe fallback if not configured
        
    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=settings.GROQ_MODEL,
        )
        content = chat_completion.choices[0].message.content or ""
        suggestions = [s.strip("- 1234567890.") for s in content.split("\n") if s.strip()]
        return suggestions[:2]
    except Exception:
        return []

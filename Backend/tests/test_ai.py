import pytest
from uuid import uuid4
from unittest.mock import MagicMock
from fastapi import HTTPException

from app.schemas.session import AnswerMode
from app.models.profile import Profile
from app.models.interview_session import InterviewSession
from app.services.ai import build_system_prompt, generate_interview_answer

def test_build_system_prompt_technical_star():
    profile = Profile(target_role="Backend Engineer", technologies=["Python", "FastAPI"])
    session = InterviewSession(mode="Technical")
    
    prompt = build_system_prompt(profile, session, AnswerMode.STAR)
    
    assert "Target Role: Backend Engineer" in prompt
    assert "Technologies: Python, FastAPI" in prompt
    assert "Interview Mode: Technical" in prompt
    assert "coding/technical questions, prioritize" in prompt
    assert "Situation, Task, Action, Result" in prompt

def test_build_system_prompt_behavioral_short():
    session = InterviewSession(mode="HR / Behavioral", target_role="Manager")
    
    prompt = build_system_prompt(None, session, AnswerMode.SHORT)
    
    assert "Target Role: Manager" in prompt
    assert "Interview Mode: HR / Behavioral" in prompt
    assert "behavioral questions, guide the model" in prompt
    assert "very concise and interview-ready" in prompt
    assert "Situation, Task, Action, Result" not in prompt

def test_build_system_prompt_rapid_fire():
    session = InterviewSession(mode="Rapid-Fire")
    
    prompt = build_system_prompt(None, session, AnswerMode.NORMAL)
    
    assert "Interview Mode: Rapid-Fire" in prompt
    assert "concise and rapid-fire style" in prompt
    assert "balanced, moderate-length answer" in prompt

import asyncio

def test_missing_groq_api_key_raises_503(monkeypatch):
    # Mock settings to have no GROQ_API_KEY
    from app.core.config import settings
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    
    # Mock db
    mock_db = MagicMock()
    # Mock db.execute to return mock session and question
    mock_result = MagicMock()
    mock_question = MagicMock()
    mock_question.transcript = "Test question"
    mock_session = MagicMock()
    mock_session.mode = "Technical"
    mock_session.target_role = "Developer"
    
    mock_result.first.return_value = (mock_question, mock_session)
    
    mock_prof_result = MagicMock()
    mock_prof_result.scalars().first.return_value = None
    
    async def mock_execute(stmt):
        if getattr(mock_execute, "called", False):
            return mock_prof_result
        mock_execute.called = True
        return mock_result
        
    mock_db.execute = mock_execute
    
    async def run_test():
        with pytest.raises(HTTPException) as exc_info:
            await generate_interview_answer(
                db=mock_db,
                user_id=uuid4(),
                question_id=uuid4(),
                answer_mode=AnswerMode.NORMAL
            )
        assert exc_info.value.status_code == 503
        assert "service is not configured" in exc_info.value.detail
        
    asyncio.run(run_test())

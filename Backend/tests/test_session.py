import pytest
from uuid import uuid4
from datetime import datetime
from pydantic import ValidationError

from app.schemas.session import (
    SessionCreate, QuestionCreate, AnswerCreate, SessionResponse, 
    QuestionResponse, AnswerResponse, PaginatedSessionResponse, SessionDetailResponse
)

def test_session_create_schema_valid():
    session = SessionCreate(mode="technical", target_role="Backend Developer")
    assert session.mode == "technical"
    assert session.target_role == "Backend Developer"

def test_session_create_schema_limits():
    with pytest.raises(ValidationError):
        SessionCreate(mode="A" * 51)  # max is 50

def test_question_create_schema_valid():
    q = QuestionCreate(
        session_id=uuid4(),
        transcript="Tell me about yourself.",
        category="behavioral",
        difficulty="medium"
    )
    assert q.transcript == "Tell me about yourself."

def test_question_create_schema_limits():
    with pytest.raises(ValidationError):
        QuestionCreate(
            session_id=uuid4(),
            transcript="A" * 5001  # max is 5000
        )

def test_answer_create_schema_valid():
    a = AnswerCreate(
        question_id=uuid4(),
        answer_text="I am a software engineer.",
        model="llama3",
        mode="text",
        latency_ms=150,
        token_usage={"prompt": 10, "completion": 5}
    )
    assert a.answer_text == "I am a software engineer."
    assert a.is_regenerated is False
    assert a.token_usage["prompt"] == 10

def test_answer_create_schema_limits():
    with pytest.raises(ValidationError):
        AnswerCreate(question_id=uuid4(), answer_text="A" * 10001)  # max is 10000

def test_paginated_response():
    resp = PaginatedSessionResponse(sessions=[], total=0)
    assert resp.total == 0
    assert isinstance(resp.sessions, list)

# Static validations for API models passing

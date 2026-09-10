from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any, Dict
from uuid import UUID
from datetime import datetime

# =======================
# Answer Schemas
# =======================
from enum import Enum

class AnswerMode(str, Enum):
    SHORT = "Short"
    NORMAL = "Normal"
    DETAILED = "Detailed"
    STAR = "STAR"

class AnswerGenerateRequest(BaseModel):
    question_id: UUID
    answer_mode: AnswerMode = AnswerMode.NORMAL

class AnswerCreate(BaseModel):
    question_id: UUID
    answer_text: str = Field(..., max_length=10000)
    model: Optional[str] = Field(None, max_length=50)
    mode: Optional[str] = Field(None, max_length=50)
    latency_ms: Optional[int] = Field(None, ge=0)
    token_usage: Optional[Dict[str, Any]] = None
    is_regenerated: bool = False

class AnswerResponse(BaseModel):
    id: UUID
    question_id: UUID
    answer_text: str
    model: Optional[str]
    mode: Optional[str]
    latency_ms: Optional[int]
    token_usage: Optional[Dict[str, Any]]
    is_regenerated: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# =======================
# Question Schemas
# =======================
class QuestionCreate(BaseModel):
    session_id: UUID
    transcript: str = Field(..., max_length=5000)
    category: Optional[str] = Field(None, max_length=100)
    difficulty: Optional[str] = Field(None, max_length=50)

class QuestionUpdate(BaseModel):
    transcript: str = Field(..., max_length=5000)

class QuestionResponse(BaseModel):
    id: UUID
    session_id: UUID
    transcript: str
    category: Optional[str]
    difficulty: Optional[str]
    is_answered: bool
    created_at: datetime
    answers: List[AnswerResponse] = []
    
    model_config = ConfigDict(from_attributes=True)

# =======================
# Session Schemas
# =======================
class SessionCreate(BaseModel):
    mode: str = Field(..., max_length=50)
    target_role: Optional[str] = Field(None, max_length=100)

class SessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    mode: str
    target_role: Optional[str]
    started_at: datetime
    ended_at: Optional[datetime]
    status: str
    score: Optional[float]
    duration_seconds: Optional[int]
    question_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class SessionDetailResponse(SessionResponse):
    questions: List[QuestionResponse] = []

class PaginatedSessionResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class ContextPreferences(BaseModel):
    experience_years: Optional[int] = Field(None, ge=0, le=100)
    current_company: Optional[str] = Field(None, max_length=200)
    key_achievements: Optional[List[str]] = Field(None, max_length=20)
    # Allow arbitrary other context
    class Config:
        extra = "allow"

class ProfileUpdate(BaseModel):
    target_role: Optional[str] = Field(None, max_length=100)
    technologies: Optional[List[str]] = Field(None, max_length=50)
    resume_text: Optional[str] = Field(None, max_length=50000) # 50K chars is roughly 10-15 pages
    jd_text: Optional[str] = Field(None, max_length=50000)
    preferences: Optional[ContextPreferences] = None

class ProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    target_role: Optional[str]
    technologies: List[str]
    resume_text: Optional[str]
    jd_text: Optional[str]
    preferences: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

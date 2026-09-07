from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class FeedbackCreate(BaseModel):
    answer_id: UUID = Field(..., alias="answerId")
    rating: int = Field(..., ge=1, le=5)
    notes: Optional[str] = None
    
    model_config = ConfigDict(populate_by_name=True)

class FeedbackResponse(BaseModel):
    id: UUID
    answer_id: UUID
    rating: Optional[int]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

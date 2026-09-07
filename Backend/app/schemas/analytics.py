from pydantic import BaseModel
from typing import Optional

class AnalyticsResponse(BaseModel):
    total_sessions: int
    completed_sessions: int
    total_questions: int
    answered_questions: int
    average_score: Optional[float]
    average_rating: Optional[float]

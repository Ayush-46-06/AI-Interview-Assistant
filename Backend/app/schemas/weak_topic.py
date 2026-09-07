from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class WeakTopicResponse(BaseModel):
    id: UUID
    user_id: UUID
    topic: str
    category: Optional[str]
    frequency: int
    avg_score: Optional[float]
    last_encountered: datetime

    model_config = ConfigDict(from_attributes=True)

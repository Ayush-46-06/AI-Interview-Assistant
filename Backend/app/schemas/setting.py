from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class SettingsUpdate(BaseModel):
    screen_invisibility_enabled: Optional[bool] = None
    disclaimer_accepted: Optional[bool] = None
    other_preferences: Optional[Dict[str, Any]] = None

class SettingsResponse(BaseModel):
    id: UUID
    user_id: UUID
    screen_invisibility_enabled: bool
    disclaimer_accepted: bool
    other_preferences: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

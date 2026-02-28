from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class User(BaseModel):
    name: str
    email: EmailStr

class MeetingRequest(BaseModel):
    title: str
    start_time: datetime
    duration_minutes: int = 30
    description: Optional[str] = None
    attendee: User

class MeetingResult(BaseModel):
    success: bool
    event_link: Optional[str] = None
    message: str

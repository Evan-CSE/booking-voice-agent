from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from .models import MeetingRequest, MeetingResult

class CalendarRepository(ABC):
    @abstractmethod
    def check_availability(self, start_time: datetime, duration_minutes: int) -> bool:
        """Check if the user's primary calendar is free for the given time slot."""
        pass
    
    @abstractmethod
    def schedule_event(self, request: MeetingRequest) -> MeetingResult:
        """Schedules an event on the calendar and returns the result."""
        pass

class EmailSender(ABC):
    @abstractmethod
    def send_overview_email(self, recipient_email: str, subject: str, body: str) -> bool:
        """Sends an email overview to the attendee."""
        pass

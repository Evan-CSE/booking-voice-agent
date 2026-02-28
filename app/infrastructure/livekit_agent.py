from livekit.agents import function_tool, RunContext
from ..usecases.schedule_meeting import VoiceAgentUseCase
from ..domain.models import MeetingRequest, User
from datetime import datetime
from ..services.logger import get_logger

logger = get_logger("infrastructure.livekit_tools")

class AgentTools:
    """
    Encapsulates LiveKit `@function_tool` definitions.
    Translates VoiceAgent primitive tool calls into Domain use cases.
    """
    
    def __init__(self, use_case: VoiceAgentUseCase):
        self.use_case = use_case

    @function_tool(description="Check the user's calendar events for a specific date/time range to see if there are conflicts.")
    def check_availability(self, start_time_iso: str, duration_minutes: int = 30) -> str:
        """Check availability on the calendar.
        
        Args:
            start_time_iso: The start time in ISO 8601 format (e.g., 2024-05-15T10:00:00+06:00).
            duration_minutes: The duration of the meeting in minutes.
        """
        logger.info(f"Tool check_availability called for {start_time_iso} ({duration_minutes} min)")
        return self.use_case.check_time_available(start_time_iso, duration_minutes)

    @function_tool(description="Schedule a new appointment or meeting on the user's Google Calendar and send an email overview.")
    def schedule_event(
        self,
        title: str,
        start_time_iso: str,
        user_name: str,
        user_email: str,
        duration_minutes: int = 30,
        description: str = "",
    ) -> str:
        """Schedule an event on the calendar.
        
        Args:
            title: The title or summary of the meeting
            start_time_iso: The start time in ISO 8601 format with timezone (e.g., 2024-05-15T10:00:00+06:00)
            user_name: The name of the person booking the appointment
            user_email: The email address of the person booking the appointment
            duration_minutes: The duration of the meeting in minutes.
            description: Optional details or notes for the meeting
        """
        logger.info(f"Tool schedule_event called for {title} at {start_time_iso}")
        try:
            start_time = datetime.fromisoformat(start_time_iso)
        except ValueError:
            return "Failed to schedule: Invalid time format."

        request = MeetingRequest(
            title=title,
            start_time=start_time,
            duration_minutes=duration_minutes,
            description=description,
            attendee=User(name=user_name, email=user_email)
        )
        return self.use_case.schedule_and_notify(request)

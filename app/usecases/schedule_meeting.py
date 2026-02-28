from ..domain.models import MeetingRequest, MeetingResult
from ..domain.interfaces import CalendarRepository, EmailSender
from ..services.logger import get_logger

logger = get_logger("usecases")

class VoiceAgentUseCase:
    """
    Orchestrates the business logic for the voice agent scheduling flow.
    Follows Single Responsibility Principle (coordinating scheduling)
    and Dependency Inversion (depends on abstractions, not concrete infra).
    """

    def __init__(self, calendar_repo: CalendarRepository, email_sender: EmailSender):
        # Dependency Injection via constructor
        self.calendar_repo = calendar_repo
        self.email_sender = email_sender

    def check_time_available(self, start_time_iso: str, duration_minutes: int = 30) -> str:
        """Use Case: Check if a given time slot is free."""
        from datetime import datetime
        try:
            start_time = datetime.fromisoformat(start_time_iso)
            is_free = self.calendar_repo.check_availability(start_time, duration_minutes)
            if is_free:
                return "The time slot is free."
            else:
                return "There is a conflict at the specified time. Please suggest another time."
        except ValueError:
            return "Invalid time format. Please provide time in ISO 8601 format."
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return "Failed to check availability due to an internal error."

    def schedule_and_notify(self, request: MeetingRequest) -> str:
        """Use Case: Schedule the meeting and send a confirmation email."""
        # 1. Schedule Calendar Event
        result = self.calendar_repo.schedule_event(request)
        
        if not result.success:
            return f"Failed to book the meeting: {result.message}"
        
        # 2. Send Overview Email
        subject = f"Meeting Scheduled: {request.title}"
        body = (
            f"Hello {request.attendee.name},\n\n"
            f"Your meeting '{request.title}' has been successfully scheduled.\n"
            f"Start Time: {request.start_time.strftime('%Y-%m-%d %H:%M %Z')}\n"
            f"Duration: {request.duration_minutes} minutes\n\n"
            f"Description: {request.description or 'No description provided'}\n\n"
            f"Calendar Link: {result.event_link}\n\n"
            f"Best regards,\nYour Voice Assistant"
        )
        
        email_sent = self.email_sender.send_overview_email(
            recipient_email=request.attendee.email,
            subject=subject,
            body=body
        )

        email_status = "and a confirmation email was sent" if email_sent else "(but failed to send confirmation email)"
        return f"Meeting successfully scheduled {email_status}. You can access it here: {result.event_link}"

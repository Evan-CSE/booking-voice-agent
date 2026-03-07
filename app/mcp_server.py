from mcp.server.fastmcp import FastMCP
from datetime import datetime

# Import existing infrastructure using absolute imports from the project root
from app.infrastructure.google_calendar import GoogleCalendarRepository
from app.infrastructure.smtp_email import SmtpEmailSender
from app.domain.models import MeetingRequest, User

# Initialize FastMCP Server
mcp = FastMCP("PersonalAssistantServer")

calendar_repo = GoogleCalendarRepository()
email_sender = SmtpEmailSender()

@mcp.tool()
def check_availability(start_time: str, duration_minutes: int) -> bool:
    """
    Check if the user is available for a meeting at the given start time and duration.
    
    Args:
        start_time: The start time in ISO 8601 format (e.g., '2023-10-27T10:00:00+06:00')
        duration_minutes: The duration of the meeting in minutes.
    """
    try:
        dt_start = datetime.fromisoformat(start_time)
        return calendar_repo.check_availability(dt_start, duration_minutes)
    except Exception as e:
        return f"Error checking availability: {str(e)}"

@mcp.tool()
def schedule_event(title: str, start_time: str, duration_minutes: int, attendee_name: str, attendee_email: str, description: str = "") -> str:
    """
    Schedule a meeting and send an email confirmation to the attendee.
    
    Args:
        title: The title of the meeting.
        start_time: The start time in ISO 8601 format (e.g., '2023-10-27T10:00:00+06:00')
        duration_minutes: The duration of the meeting in minutes.
        attendee_name: The name of the person attending the meeting.
        attendee_email: The email address of the person attending the meeting.
        description: An optional description or agenda for the meeting.
    """
    try:
        dt_start = datetime.fromisoformat(start_time)
        
        request = MeetingRequest(
            title=title,
            start_time=dt_start,
            duration_minutes=duration_minutes,
            attendee=User(name=attendee_name, email=attendee_email),
            description=description
        )
        
        result = calendar_repo.schedule_event(request)
        
        if result.success:
            # Send confirmation email
            email_subject = f"Meeting Confirmation: {title}"
            email_body = (
                f"Hi {attendee_name},\n\n"
                f"Your meeting '{title}' has been successfully scheduled.\n"
                f"Start Time: {dt_start.strftime('%Y-%m-%d %H:%M %Z')}\n"
                f"Duration: {duration_minutes} minutes\n\n"
                f"Event Link: {result.event_link}\n\n"
                f"Thank you!"
            )
            email_sent = email_sender.send_overview_email(attendee_email, email_subject, email_body)
            
            response = f"Meeting scheduled successfully! Link: {result.event_link}"
            if not email_sent:
                response += " (Note: Failed to send confirmation email)."
            return response
        else:
            return f"Failed to schedule meeting: {result.message}"
            
    except Exception as e:
        return f"Error scheduling event: {str(e)}"

@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """
    Send an arbitrary email to a recipient.
    
    Args:
        to: The email address of the recipient.
        subject: The subject of the email.
        body: The body content of the email.
    """
    success = email_sender.send_overview_email(to, subject, body)
    if success:
        return f"Email sent successfully to {to}"
    else:
        return f"Failed to send email to {to}. Check server logs."

if __name__ == "__main__":
    mcp.run()

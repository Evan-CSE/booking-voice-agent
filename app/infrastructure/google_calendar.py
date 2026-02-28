import os.path
import logging
from datetime import datetime, timedelta

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..domain.models import MeetingRequest, MeetingResult
from ..domain.interfaces import CalendarRepository
from ..services.logger import get_logger

logger = get_logger("infrastructure.calendar")

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

class GoogleCalendarRepository(CalendarRepository):
    """Infrastructure implementation of CalendarRepository using Google Calendar API v3."""

    def __init__(self):
        self._service = self._get_calendar_service()

    def _get_calendar_service(self):
        """Authenticate and return a Google Calendar API service."""
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists("credentials.json"):
                    logger.error("credentials.json not found!")
                    return None
                flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
                creds = flow.run_local_server(port=0)
            with open("token.json", "w") as token:
                token.write(creds.to_json())
        try:
            return build("calendar", "v3", credentials=creds)
        except HttpError as error:
            logger.error(f"An error occurred initializing calendar service: {error}")
            return None

    def check_availability(self, start_time: datetime, duration_minutes: int) -> bool:
        if not self._service:
            raise Exception("Google Calendar service is not initialized.")

        end_time = start_time + timedelta(minutes=duration_minutes)

        try:
            events_result = (
                self._service.events()
                .list(
                    calendarId="primary",
                    timeMin=start_time.isoformat(),
                    timeMax=end_time.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])
            return len(events) == 0  # True if available (no conflicting events)
        except HttpError as error:
            logger.error(f"An error occurred checking availability: {error}")
            raise Exception(f"Google Calendar API Error: {error}")

    def schedule_event(self, request: MeetingRequest) -> MeetingResult:
        if not self._service:
            return MeetingResult(success=False, message="Calendar service not initialized.")

        end_time = request.start_time + timedelta(minutes=request.duration_minutes)

        event_body = {
            "summary": request.title,
            "description": f"Booked by: {request.attendee.name}\nEmail: {request.attendee.email}\n\n{request.description or ''}",
            "start": {"dateTime": request.start_time.isoformat()},
            "end": {"dateTime": end_time.isoformat()},
            "attendees": [{"email": request.attendee.email, "displayName": request.attendee.name}],
        }

        try:
            event = self._service.events().insert(calendarId="primary", body=event_body).execute()
            return MeetingResult(
                success=True, 
                event_link=event.get("htmlLink"),
                message="Event successfully created."
            )
        except HttpError as error:
            logger.error(f"An error occurred scheduling the event: {error.content}")
            return MeetingResult(success=False, message=str(error.reason))

import os
import sys
import uuid
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from aiohttp import web
import aiohttp_cors

from livekit import api
from livekit.agents import AgentSession, AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli
from livekit.agents.voice import Agent
from livekit.plugins import silero, google, openai

# Clean Architecture Imports
from .infrastructure.google_calendar import GoogleCalendarRepository
from .infrastructure.smtp_email import SmtpEmailSender
from .infrastructure.livekit_agent import AgentTools
from .usecases.schedule_meeting import VoiceAgentUseCase
from .services.logger import get_logger
from .presentation.middleware import logging_middleware

load_dotenv()
logger = get_logger("composition-root")

# --- Composition Root: Dependency Injection Setup ---
def create_agent_tools() -> list:
    """Wires up the dependencies and returns the LiveKit function tools."""
    calendar_repo = GoogleCalendarRepository()
    email_sender = SmtpEmailSender()
    use_case = VoiceAgentUseCase(calendar_repo, email_sender)
    livekit_tools = AgentTools(use_case)
    
    # We expose the bound methods as a list of tools for the LiveKit Agent
    return [livekit_tools.check_availability, livekit_tools.schedule_event]

# --- LiveKit Agent Worker Setup ---
def prewarm(proc: JobProcess):
    """Pre-load VAD model."""
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    stt = openai.STT(base_url=os.getenv("STT_BASE_URL", "http://stt:8000/v1"), api_key="not-needed")
    tts = openai.TTS(base_url=os.getenv("TTS_BASE_URL", "http://tts:8001/v1"), api_key="not-needed", response_format="pcm")
    gemini_llm = google.LLM(model="gemini-3-flash-preview")

    fnc_tools = create_agent_tools()

    instructions = f"""
    You are a highly efficient personal scheduling assistant.
    Your ONLY purpose is to help the user schedule appointments on their personal Google Calendar.
    Current date and time: {datetime.now().astimezone().isoformat()}
    
    Workflow:
    1. Greet the user. Gather: Title, Date/Time, Duration, Full Name, Email, Description.
    2. Convert times to ISO 8601 / RFC3339 format with local timezone offset (+06:00).
    3. Call `check_availability` to verify no conflicts.
    4. Call `schedule_event` to book and send email.
    
    CRITICAL VOICE OUTPUT RULES:
    - NEVER use markdown. NEVER use emojis. Write numbers as words.
    Keep responses concise.
    """

    agent = Agent(
        instructions=instructions,
        stt=stt,
        llm=gemini_llm,
        tts=tts,
        vad=ctx.proc.userdata["vad"],
        tools=fnc_tools,
    )

    session = AgentSession()
    await session.start(agent=agent, room=ctx.room)
    await session.say("Hello! I can help you schedule a meeting. What would you like to book?", allow_interruptions=True)

# --- Web Server Setup ---
async def get_token(request):
    room_name = request.query.get("room_name", f"voice-{uuid.uuid4().hex[:8]}")
    participant_identity = request.query.get("identity", f"user-{uuid.uuid4().hex[:8]}")
    try:
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")
        token = api.AccessToken(api_key, api_secret).with_identity(participant_identity).with_name("Web User").with_grants(
            api.VideoGrants(room_join=True, room=room_name)
        )
        return web.json_response({"token": token.to_jwt(), "url": os.getenv("LIVEKIT_URL", "")})
    except Exception as e:
         return web.json_response({"error": str(e)}, status=500)

def run_web():
    app = web.Application(middlewares=[logging_middleware])
    cors = aiohttp_cors.setup(app, defaults={"*": aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*")})
    cors.add(app.router.add_get('/token', get_token))
    
    current_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    frontend_dir = os.path.join(current_dir, "frontend")
    app.router.add_static('/', frontend_dir, name='static', show_index=True)
    
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting web server on port {port}")
    web.run_app(app, port=port)

# --- CLI Router ---
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "web":
        run_web()
    else:
        # Default to Livekit Agent (livekit CLI processes sys.argv itself, so we must not pass 'agent' as arg 1 to cli.run_app if it intercepts it, 
        # but typically livekit agents are run via `python main.py start`)
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))

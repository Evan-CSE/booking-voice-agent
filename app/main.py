import os
import sys
import uuid
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from aiohttp import web
import aiohttp_cors

from livekit import api
from livekit.agents import AgentSession, AutoSubscribe, JobContext, JobProcess, WorkerOptions, cli, mcp
from livekit.agents.voice import Agent
from livekit.plugins import silero, google, openai

# Clean Architecture Imports
from .services.logger import get_logger
from .presentation.middleware import logging_middleware
from .config.settings import settings

logger = get_logger("composition-root")

# --- LiveKit Agent Worker Setup ---
def prewarm(proc: JobProcess):
    """Pre-load VAD model."""
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Initialize MCP Server to provide tools
    print("Connecting to MCP Server...")
    mcp_server = mcp.MCPServerStdio(
        command="python",
        args=["-m", "app.mcp_server"],
        env=os.environ.copy()
    )
    print("MCP server initialized.")

    stt = openai.STT(base_url=settings.STT_BASE_URL, api_key="not-needed")
    tts = openai.TTS(model="kokoro", base_url=settings.TTS_BASE_URL, api_key="not-needed", response_format="pcm")
    gemini_llm = google.LLM(model=settings.LLM_MODEL)

    instructions = f"""
    You are a highly efficient personal scheduling assistant.
    Your ONLY purpose is to help the user schedule appointments on Evan's personal Google Calendar.
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
        mcp_servers=[mcp_server],
    )

    session = AgentSession()
    await session.start(agent=agent, room=ctx.room)
    await session.say("Hello! I can help you schedule a meeting. What would you like to book?", allow_interruptions=True)

# --- Web Server Setup ---
async def get_token(request):
    room_name = request.query.get("room_name", f"voice-{uuid.uuid4().hex[:8]}")
    participant_identity = request.query.get("identity", f"user-{uuid.uuid4().hex[:8]}")
    try:
        api_key = settings.LIVEKIT_API_KEY
        api_secret = settings.LIVEKIT_API_SECRET
        token = api.AccessToken(api_key, api_secret).with_identity(participant_identity).with_name("Web User").with_grants(
            api.VideoGrants(room_join=True, room=room_name)
        )
        return web.json_response({"token": token.to_jwt(), "url": settings.LIVEKIT_URL})
    except Exception as e:
         return web.json_response({"error": str(e)}, status=500)

def run_web():
    app = web.Application(middlewares=[logging_middleware])
    cors = aiohttp_cors.setup(app, defaults={"*": aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*")})
    cors.add(app.router.add_get('/token', get_token))
    
    current_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    frontend_dir = os.path.join(current_dir, "frontend")
    app.router.add_static('/', frontend_dir, name='static', show_index=True)
    
    port = settings.PORT
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
